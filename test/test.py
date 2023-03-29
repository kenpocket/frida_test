import execjs
import json
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
s = (rc.call('start', 'RoarkeEstrin_AscendSMG.mview'))
for files in s:
    with open(files, 'wb') as fp:
        data = bytes(list(s[files].values()))
        fp.write(data)
