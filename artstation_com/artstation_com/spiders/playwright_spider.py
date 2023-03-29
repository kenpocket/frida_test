import os.path
import sys
import execjs
from playwright.sync_api import sync_playwright
import pymongo
import threading
import re
import random
import requests
from extract import get_obj_main
from scrapy.cmdline import execute

sys.path.append('..')
from settings import PROXY_LIST, mongo_host, mongo_password, mongo_user, mongo_port, mongo_cli, mongo_db

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
mongo = pymongo.MongoClient(host=mongo_host, port=mongo_port, username=mongo_user, password=mongo_password)
db = mongo[mongo_db]
cli = db[mongo_cli]

# File_Path = 'new_mview'  # 此处需要自己设定文件存放路径
# if not os.path.exists(File_Path):
#     os.mkdir(File_Path)


def get_file(url: str, s):
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
    proxy = random.choice(PROXY_LIST)
    proxies = {"http": proxy, "https": proxy}
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
        cli.update_one({"model_id": s['model_id']}, {"$set": {"is_play": -1}})
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
    cli.update_one({"model_id": s['model_id']}, {"$set": {"is_play": 2}})


def get_mview_url(strs, s):
    comp = re.compile(r'https\:\/\/cdn[a|b]\.artstation\.com/.*?\.mview\?(\d+)\"')
    download_url = comp.search(strs)
    if download_url:
        model_url = download_url.group(0)
        model_id = download_url.group(1)
        get_file(model_url, s)


def get_response(response, model_id):
    if 'https://www.artstation.com/embed' in response.url and response.status == 200:
        # get_mview_url(response.body())
        cli.update_one({"model_id": int(model_id)}, {"$set": {"is_play": 1, "embed_text": response.body().decode()}})
        print(response.body().decode())
        # threading.Thread(target=get_mview_url, args=(response.body())).start()


def get_1(s):
    print(s)
    url = s['model_url']
    model_id = s['model_id']
    with sync_playwright() as p:
        rch = p.chromium.launch(headless=False)
        page = rch.new_page()
        page.on('response', lambda response: get_response(response, model_id))
        page.goto(url)
        # page.wait_for_url(url,timeout=6000000)


def embed():
    s = cli.find({"is_play": 0}, {"_id": 0})
    a = next(s, '')
    while a:
        get_1(a)
        a = next(s, '')


def files():
    s = cli.find({"is_play": 1}, {"_id": 0})
    a = next(s, '')
    while a:
        get_mview_url(a['embed_text'], a)
        a = next(s, '')


if __name__ == '__main__':
    # threading.Thread(target=embed).start()  # 第二步， embed为一个api，有cloudflare反爬，使用playwright绕过了cloudflare的触发
    threading.Thread(target=files).start()  # 第三步， 将下载好的mview文件解析，存储
    # execute('scrapy crawl artstation'.split())  # 第一步， 爬取反爬措施较弱的url，存储在mongo
