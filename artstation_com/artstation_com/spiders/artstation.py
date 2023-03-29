import os
import execjs
import scrapy
from scrapy import Request
from scrapy.cmdline import execute
from scrapy.http.response.text import TextResponse
import re
from extract import get_obj_main
import sys
sys.path.append('..')
from items import ArtstationComItem

class ArtstationSpider(scrapy.Spider):
    name = "artstation"
    allowed_domains = ["www.artstation.com"]
    start_urls = ["https://www.artstation.com/"]
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

    def start_requests(self):
        yield Request(method='GET',
                      url='https://www.artstation.com/api/v2/community/channels/projects.json?channel_id=6003&page=1&sorting=trending&dimension=all&per_page=30',
                      callback=self.parse, dont_filter=True)

    def parse(self, response: TextResponse):
        print(response)
        try:
            max_page = response.json()['total_count'] // 30
            if max_page > 333:
                max_page = 333
        except:
            max_page = 0
        debugger = False
        if debugger:
            max_page = 2
        for page in range(1, max_page):
            url = 'https://www.artstation.com/api/v2/community/channels/projects.json?channel_id=6003&page={}&sorting=trending&dimension=all&per_page=30'.format(
                page)
            yield Request(url=url, callback=self.parse_get_mview, dont_filter=True)

    def parse_get_mview(self, response: TextResponse):
        data = response.json()
        data = data.get('data', [])
        if data:
            for d in data:
                if d['icons']['marmoset']:
                    model_id = d.get('id', '')
                    model_url = d.get('url', '')
                    model_hash_code = d.get('hash_id', '')
                    if model_url and model_hash_code and model_id:
                        # embed_url = model_url
                        item = ArtstationComItem()
                        # meta = response.meta
                        item['model_id'] = model_id
                        item['model_url'] = model_url
                        item['hash_id'] = d['hash_id']
                        item['title'] = d['title']
                        # meta['model_id'] = model_id
                        # meta['model_url'] = model_url
                        # meta['Referer'] = model_url
                        # meta['is_model'] = True
                        yield item
                        # TODO 403 clouldflare
                        # yield Request(method='GET', url=embed_url, callback=self.parse_download, dont_filter=True,
                        #               meta=meta)
    # def parse_download(self, response: TextResponse):
    #     meta = response.meta
    #     model_id = meta['model_id']
    #     comp = re.compile(r'https://cdna.artstation.com/.*?\.mview\?' + str(model_id))
    #     download_url = comp.search(response.text)
    #     if download_url:
    #         download_url = download_url.group()
    #         yield Request(url=download_url, callback=self.download, dont_filter=True)
    # def download(self, response: TextResponse):
    #     body = response.body
    #     file_name = response.url.split('/')[-1].split('?')[0]
    #     if not os.path.exists('mview'):
    #         os.mkdir('mview')
    #     with open('mview/' + file_name, 'wb') as fp:
    #         fp.write(body)
    #     rc = self.rc
    #     s = rc.call('main', 'mview/' + file_name)
    #     if not os.path.exists('mview/' + file_name):
    #         os.mkdir('mview/' + file_name)
    #     for files in s:
    #         with open('mview/' + file_name + '/' + files, 'wb') as fp:
    #             data = bytes(list(s[files].values()))
    #             fp.write(data)
    #     get_obj_main('mview/' + file_name, 'mview/' + file_name)


if __name__ == '__main__':
    execute('scrapy crawl artstation'.split())
