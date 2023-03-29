import json
import os
from struct import unpack

import execjs
import requests
from playwright.sync_api import sync_playwright
import re

js_code = '''function ByteStream(a) {
        this.bytes = new Uint8Array(a);

    }

    ByteStream.prototype.readCString = function () {
        for (var a = this.bytes, c = this.bytes.length, b = 0; b < c; ++b)
            if (0 == a[b])
                return a = String.fromCharCode.apply(null, this.bytes.subarray(0, b)),
                    this.bytes = this.bytes.subarray(b + 1),
                    a;
        return null
    };
    ByteStream.prototype.readBytes = function (a) {
        var c = this.bytes.subarray(0, a);
        this.bytes = this.bytes.subarray(a);
        return c
    }
    ;
    ByteStream.prototype.readUint32 = function () {
        var a = this.bytes
            , c = a[0] | a[1] << 8 | a[2] << 16 | a[3] << 24;
        this.bytes = a.subarray(4);
        return c
    }
    ;

    function Archive(a) {
        let length = a.length;
        let array_b1 = new ArrayBuffer(length);
        var view = new Uint8Array(array_b1);
        for (let i = 0; i < length; i++) {
            view[i] = a[i];
        }
        this.files = [];
        for (a = new ByteStream(a); 0 < a.bytes.length;) {
            var c = {};
            c.name = a.readCString();
            c.type = a.readCString();
            var b = a.readUint32()
                , d = a.readUint32()
                , e = a.readUint32();
            c.data = a.readBytes(d);
            if (!(c.data.length < d)) {
                if (b & 1 && (c.data = this.decompress(c.data, e),
                null === c.data))
                    continue;
                this.files[c.name] = c
            }
        }
    }

    Archive.prototype.decompress = function (a, c) {
        var b = new Uint8Array(c)
            , d = 0
            , e = new Uint32Array(4096)
            , f = new Uint32Array(4096)
            , g = 256
            , h = a.length
            , k = 0
            , n = 1
            , m = 0
            , l = 1;
        b[d++] = a[0];
        for (var p = 1; ; p++) {
            l = p + (p >> 1);
            if (l + 1 >= h)
                break;
            var m = a[l + 1]
                , l = a[l]
                , r = p & 1 ? m << 4 | l >> 4 : (m & 15) << 8 | l;
            if (r < g)
                if (256 > r)
                    m = d,
                        l = 1,
                        b[d++] = r;
                else
                    for (var m = d, l = f[r], r = e[r], s = r + l; r < s;)
                        b[d++] = b[r++];
            else if (r == g) {
                m = d;
                l = n + 1;
                r = k;
                for (s = k + n; r < s;)
                    b[d++] = b[r++];
                b[d++] = b[k]
            } else
                break;
            e[g] = k;
            f[g++] = n + 1;
            k = m;
            n = l;
            g = 4096 <= g ? 256 : g
        }
        return d == c ? b : null
    };

    function start(file_path) {
        const fs = require('fs');
        const b1 = fs.readFileSync(file_path);
        const d = new Archive(b1); 
        var result = {};
        for(var h in d.files){
            result[h] = d.files[h].data;
        }
        return result;
    };
    '''
rc = execjs.compile(js_code)


def get_obj_main(folder, new_folder):
    if not os.path.exists(new_folder):
        os.mkdir(new_folder)
    # print(os.path.abspath('.'))
    f = open("%s/scene.json" % folder)
    data = json.load(f)
    f.close()
    omtl = open("%s/master.mtl" % new_folder, "w")
    for mat in data["materials"]:
        name = mat["name"]
        diffuse = mat["albedoTex"]
        omtl.write("newmtl {0}\n".format(name))
        omtl.write("map_Ka {0}\n".format(diffuse))
        omtl.write("map_Kd {0}\n".format(diffuse))

    omtl.close()

    for mesh in data["meshes"]:
        name = mesh["name"]
        dat = mesh["file"]
        print("converting %s" % dat)
        wire_count = mesh["wireCount"]
        vertex_count = mesh["vertexCount"]
        tex_coord_2 = 0
        if "secondaryTexCoord" in mesh:
            tex_coord_2 = mesh["secondaryTexCoord"]

        vertex_color = 0
        if "vertexColor" in mesh:
            vertex_color = mesh["vertexColor"]
        index_type_size = mesh["indexTypeSize"]
        # consts
        stride = 32
        if vertex_color > 0:
            stride = stride + 4
        if tex_coord_2 > 0:
            stride = stride + 8
        df = open("%s/%s" % (folder, dat), "rb")
        # write stream
        output = open("{0}/{1}.obj".format(new_folder, dat), "w")
        output.write("mtllib master.mtl\n")
        face_list = []
        vert_list = []
        uv_list = []
        materials_list = []
        for sub_mesh in mesh["subMeshes"]:
            faces = []
            material = sub_mesh["material"]
            index_count_2 = sub_mesh["indexCount"]
            wire_count_2 = sub_mesh["wireIndexCount"]
            face_count = int((index_count_2 * index_type_size) / 6)
            if index_type_size == 4:
                face_count = int((index_count_2 * index_type_size) / 12)
            for f in range(face_count):
                if index_type_size == 2:
                    faces.append(unpack("<HHH", df.read(6)))
                else:
                    faces.append(unpack("<III", df.read(12)))
            face_list.append(faces)
            materials_list.append(material)
        df.seek(wire_count * index_type_size, 1)
        for v in range(vertex_count):
            pos = unpack("<fff", df.read(12))
            texpos = unpack("<ff", df.read(8))
            df.read(stride - 20)
            vert_list.append(pos)
            uv_list.append(texpos)

        for vert in vert_list:
            output.write("v {0} {1} {2}\n".format(vert[0], vert[1], vert[2]))

        for uv in uv_list:
            output.write("vt {0} {1}\n".format(uv[0], uv[1]))

        for x, faces in enumerate(face_list):
            output.write("\n")
            output.write("g {0}\n".format(name))
            output.write("usemtl {0}\n".format(materials_list[x]))

            for face in faces:
                output.write("f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}\n".format(face[0] + 1, face[1] + 1, face[2] + 1))

        df.close()
        output.close()

    print("COMPLETED!!!")


def get_file(url: str):
    headers = {
        'authority': 'www.artstation.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'cookie': 'PRIVATE-CSRF-TOKEN=b8dVOI19Ofed4e5vTII8K05cj9btc7c031K7c0AUSoo%3D; __stripe_mid=bb175804-3f3c-4144-860a-65f903fded7d832692; visitor-uuid=d8dab88f-ca36-4057-a31f-b5ec0629df63; _pk_id.1.119b=57c75791dcbf5376.1679017805.; _gcl_au=1.1.2121583257.1679017805; _ga=GA1.2.309061946.1679017805; __cf_bm=s8VgtghMndOxoaUlEreEdv1dYez3Fkf2z8IYquEhD8A-1679237172-0-AfwNWfP8akkiOymtaJ/iGqRa+40vVuHaKr1SST9i1forhu80hCm03lqA4+bKqSQ/7b+R/M+V5fhL6zROuGC5T0V6b7oF0TDCMp2TmFO2BG0W',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
    }
    # cookie时效性很长，如果真的403了，直接去网站找个cookie替换即可
    proxies = {"http": 'http://127.0.0.1:7890', "https": 'http://127.0.0.1:7890'}
    try:
        response = requests.get(url=url, headers=headers, proxies=proxies)
    except requests.exceptions.ProxyError as p:
        print('代理失效了！', p)
        return
    filename = url.split('/')[-1].split('?')[0]
    mview_path = 'mview'
    if not os.path.exists(mview_path):
        os.mkdir(mview_path)
    f_path = mview_path + '/' + filename.split('.')[0]
    if not os.path.exists(f_path):
        os.mkdir(f_path)
    with open(f_path + '/' + filename, 'wb') as fp:
        fp.write(response.content)
    # print('ok')
    print(f_path + '/' + filename)
    try:
        sa = rc.call('start', f_path + '/' + filename)
    except execjs._exceptions.ProgramError as p:
        print('unknown reason ', p)
        return
    for fs in sa:  # type: str
        if fs.endswith('.jpg'):
            if not os.path.exists('new_' + f_path):
                os.mkdir('new_' + f_path)
            with open('new_' + f_path + '/' + fs, 'wb') as fp:
                data = bytes(list(sa[fs].values()))
                fp.write(data)
        else:
            with open(f_path + '/' + fs, 'wb') as fp:
                data = bytes(list(sa[fs].values()))
                fp.write(data)
    get_obj_main(f_path, 'new_' + f_path)
    print('over')


def get_mview_url(strs):
    comp = re.compile(r'https\:\/\/cdn[a|b]\.artstation\.com/.*?\.mview\?(\d+)\"')
    download_url = comp.search(strs)
    if download_url:
        model_url = download_url.group(0)
        # model_id = download_url.group(1)
        get_file(model_url)


def get_response(response):
    if 'https://www.artstation.com/embed' in response.url:
        if response.status == 403:
            print('代理失效了，快换代理！')
        else:
            get_mview_url(response.body().decode())

        # print(response.body().decode())


def get_1(s):
    print(s)
    url = s
    try:
        with sync_playwright() as p:
            rch = p.chromium.launch(headless=False)
            page = rch.new_page()
            page.on('response', lambda response: get_response(response,))
            page.goto(url)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    urls = ['''https://www.artstation.com/artwork/d0AYyx''',
            'https://www.artstation.com/artwork/8w2oGq',
            'https://www.artstation.com/artwork/kQl6bK', #调用了S站的数据，模型文件不在A站
            'https://www.artstation.com/marketplace/p/KXgwA/woman-character' #没有模型文件，爬不到
            ]
    for url in urls:
        get_1(url)
        # break
