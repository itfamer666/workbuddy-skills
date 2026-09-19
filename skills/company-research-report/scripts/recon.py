#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recon.py — 企业官网全站侦察器

用途：给定一个网址，把"看得见的页面"和"看不见的数据接口"全部扒下来。
核心价值：现代官网多为 JS 渲染，WebFetch 只能拿到占位符（如"API接口单元"），
          而且真正的结构化数据（门店/品牌/产品线）往往藏在 XHR 接口里，
          接口数据的准确度远高于网页宣传文案。

用法：
    python3 recon.py https://www.example.com
    python3 recon.py https://www.example.com -o ./调研 --max-pages 20
    python3 recon.py https://www.example.com --probe-only   # 只跑接口探测

输出：
    <outdir>/raw/*.html        原始页面
    <outdir>/raw/*.js          站内 JS
    <outdir>/api/*.json        成功命中并返回 JSON 的接口
    <outdir>/endpoints.txt     候选接口清单
    <outdir>/recon-report.md   侦察小结
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from collections import OrderedDict

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 接口路径出现在 JS/HTML 里的常见形态
EP_PATTERNS = [
    r'url\s*[:=]\s*["\'](/[A-Za-z0-9_\-/\.=&?]{4,80})["\']',
    r'\$\.(?:get|post|ajax)\s*\(\s*["\'](/[A-Za-z0-9_\-/\.=&?]{4,80})["\']',
    r'axios\.(?:get|post)\s*\(\s*["\'](/[A-Za-z0-9_\-/\.=&?]{4,80})["\']',
    r'fetch\s*\(\s*["\'](/[A-Za-z0-9_\-/\.=&?]{4,80})["\']',
    r'action\s*=\s*["\'](/[A-Za-z0-9_\-/\.=&?]{4,80})["\']',
    r'["\'](/[a-z][A-Za-z0-9_]*(?:/[A-Za-z0-9_\-\.]+){1,4})["\']',
]
SKIP_EXT = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.woff', '.woff2', '.ttf', '.mp4', '.webp', '.pdf')
JS_PLACEHOLDER_HINTS = ('API接口单元', 'loading', 'Loading', '请开启JavaScript',
                        'enable JavaScript', '<div id="app">', '<div id="root">')


def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.stdout.decode('utf-8', 'ignore')
    except Exception:
        return ''


def curl(url, timeout=25, out=None, retries=3, extra=None):
    """
    带重试与状态码识别的抓取。
    真实环境里企业官网经常间歇性 502/超时，不重试会得到假结果。
    extra: 附加的 curl 参数（如 ['-X','POST','-d','...']），用于补参探测。
    返回 body；抓取是否成功记录在 LAST_STATUS 里。
    """
    body, code = '', 0
    for attempt in range(retries):
        cmd = ['curl', '-sL', '--max-time', str(timeout),
               '-H', 'User-Agent: ' + UA,
               '-H', 'Accept-Language: zh-CN,zh;q=0.9']
        if extra:
            cmd += extra
        cmd += ['-w', '\n__HTTPCODE__%{http_code}', url]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout + 8)
            txt = r.stdout.decode('utf-8', 'ignore')
        except Exception:
            txt = ''
        if '__HTTPCODE__' in txt:
            body, c = txt.rsplit('__HTTPCODE__', 1)
            try:
                code = int(c.strip())
            except Exception:
                code = 0
        else:
            body, code = txt, 0
        if code == 200 and body.strip():
            break
        time.sleep(1.5 * (attempt + 1))
    LAST_STATUS['code'] = code
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(body)
    return body


LAST_STATUS = {'code': 0}


def same_host(url, base_host):
    try:
        h = urllib.parse.urlparse(url).netloc
        return h == '' or h == base_host or h.endswith('.' + base_host) or base_host.endswith('.' + h)
    except Exception:
        return False


def extract_links(html, base_url, base_host):
    """抽取站内链接（去重、去锚点、去静态资源）"""
    urls = set()
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', html, re.I):
        u = m.group(1).strip()
        if u.startswith(('javascript:', 'mailto:', 'tel:', 'data:', '#')):
            continue
        # 前端模板占位符（Vue/Thymeleaf 等）会被误当成链接，必须剔除
        if '${' in u or '{{' in u or '}}' in u:
            continue
        full = urllib.parse.urljoin(base_url, u)
        full = full.split('#')[0]
        if not full.startswith('http'):
            continue
        # 页面里写错的 href（如 /https://xxx.com/）会被 urljoin 拼成畸形地址，
        # 特征：URL 里出现两个 ://  或路径中出现 /http
        if full.count('://') > 1 or re.search(r'/https?:', full):
            continue
        if not same_host(full, base_host):
            continue
        low = full.lower().split('?')[0]
        if low.endswith(SKIP_EXT):
            continue
        urls.add(full)
    return urls


# 公共库：名字里带这些的 JS 几乎不可能藏业务接口，但往往几百 KB~1MB，
# 全下下来既慢又会被业务 JS 挤掉（只取前 40 个）。
KNOWN_LIB = re.compile(
    r'(jquery|echarts|vue|react|angular|swiper|bootstrap|wow|lazyload|lodash|'
    r'underscore|axios|moment|d3|chart|polyfill|element|antd|fullpage|rem\.js|'
    r'100rem|modernizr|slick|owl\.carousel|layui|amazeui|zepto)', re.I)


def extract_js(html, base_url, base_host):
    urls = set()
    for m in re.finditer(r'<script[^>]+src\s*=\s*["\']([^"\']+)["\']', html, re.I):
        full = urllib.parse.urljoin(base_url, m.group(1))
        if same_host(full, base_host) and full.lower().split('?')[0].endswith('.js'):
            if KNOWN_LIB.search(full.split('/')[-1]):
                continue
            urls.add(full)
    return urls


def extract_endpoints(text):
    eps = OrderedDict()
    for pat in EP_PATTERNS:
        for m in re.finditer(pat, text):
            ep = m.group(1)
            low = ep.lower().split('?')[0]
            if low.endswith(SKIP_EXT):
                continue
            if len(ep) < 6 or ep.startswith('//'):
                continue
            eps.setdefault(ep, 0)
            eps[ep] += 1
    # 按出现次数排序（出现多的更可能是真实业务接口）
    return [e for e, _ in sorted(eps.items(), key=lambda x: -x[1])]


def looks_json(txt):
    t = txt.strip()
    return ((t.startswith('{') and t.endswith('}'))
            or (t.startswith('[') and t.endswith(']')))


def count_items(obj, depth=0):
    """统计 JSON 中最有价值的那个列表的条目数。

    很多接口形如 {"code":1,"data":{"list":[...]}}，只看 data 长度会得到 1，
    所以要下钻找出最大的那个列表。
    """
    best = 0
    if isinstance(obj, list):
        best = len(obj)
    elif isinstance(obj, dict) and depth < 6:
        for v in obj.values():
            best = max(best, count_items(v, depth + 1))
    return best


def summarize_json(path):
    """给出 JSON 结构的简要描述，便于人工判断价值"""
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        return '（非标准 JSON）'
    def walk(o, depth=0):
        if isinstance(o, dict):
            return '{%s}' % ', '.join(list(o.keys())[:8])
        if isinstance(o, list):
            return '[%d 项] %s' % (len(o), walk(o[0], depth + 1) if o else '')
        return type(o).__name__
    return walk(d)


def main():
    ap = argparse.ArgumentParser(description='企业官网全站侦察')
    ap.add_argument('url', help='目标网址')
    ap.add_argument('-o', '--out', default='./recon', help='输出目录')
    ap.add_argument('--max-pages', type=int, default=25, help='最多抓取子页面数')
    ap.add_argument('--probe-only', action='store_true', help='只做接口探测')
    args = ap.parse_args()

    url = args.url if '://' in args.url else 'https://' + args.url
    pu = urllib.parse.urlparse(url)
    base_host = pu.netloc
    scheme_host = f'{pu.scheme}://{pu.netloc}'
    raw_dir = os.path.join(args.out, 'raw')
    api_dir = os.path.join(args.out, 'api')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(api_dir, exist_ok=True)

    print(f'🎯 目标：{url}')
    home = curl(url, out=os.path.join(raw_dir, 'index.html'))
    code = LAST_STATUS['code']
    if code != 200 or not home.strip():
        low = home.strip().lower()
        print(f'\n❌ 首页抓取失败：HTTP {code}（已重试 3 次）')
        if 'upstream' in low or 'timeout' in low or not low:
            print(f'   服务端返回：{home.strip()[:120]}')
        print('\n   这通常意味着站点临时不可用 / 需要鉴权 / 拒绝爬虫。可选办法：')
        print('   1. 稍后重试本脚本（间歇性 502 很常见，换个时间往往就好了）')
        print('   2. 换用 https:// 试一次，或去掉 www / 加 www 再试')
        print('   3. 站点确实打不开时，改用 WebSearch + 公开资料调研，')
        print('      并在报告第 12 章注明「官网不可访问，数据来源以二手渠道为主」')
        sys.exit(1)
    print(f'   首页抓取 {len(home)} 字节（HTTP {code}）')

    is_js_rendered = False
    text_len = len(re.sub(r'<[^>]+>', '', home))
    hint = any(h in home[:3000] for h in JS_PLACEHOLDER_HINTS)
    # 判别要点：HTML 很大但正文极少 = 内容由 JS 注入（SPA）；
    # 小页面本身正文就少，不能仅凭 text_len 判定，否则误报。
    if hint or (text_len < 500 and len(home) > 3000):
        is_js_rendered = True
        print('   ⚠️  检测为 JS 渲染页 —— WebFetch 会失败，必须用本脚本的原始 HTML')
    elif text_len < 3000:
        print('   ⚠️  正文很短，可能是 SPA 或内容由接口下发')

    all_text = home
    endpoints = OrderedDict()

    if not args.probe_only:
        links = sorted(extract_links(home, url, base_host))
        print(f'🔗 发现站内链接 {len(links)} 个，抓取前 {args.max_pages} 个')
        seen = {hashlib.md5(home.encode('utf-8', 'ignore')).hexdigest()}
        n_dup = 0
        got = 0
        # 配额只算「成功抓到的唯一页」：重复页不该消耗预算，否则 8 个配额
        # 可能全被 ?page=0/1/2 这类分页吃光。attempts 上限防死循环。
        attempts = min(len(links), max(args.max_pages * 4, 30))
        for lk in links[:attempts]:
            if got >= args.max_pages:
                break
            name = re.sub(r'[^A-Za-z0-9_\-]', '_', urllib.parse.urlparse(lk).path.strip('/') or 'page')[:60]
            fp = os.path.join(raw_dir, f'{name}.html')
            if os.path.exists(fp):
                n_dup += 1
                continue
            t = curl(lk, out=fp)
            if not t:
                continue
            # 分页参数常导致同一页面被抓多次（?page=0/1/2 内容完全一样），按内容去重
            h = hashlib.md5(t.encode('utf-8', 'ignore')).hexdigest()
            if h in seen:
                n_dup += 1
                try:
                    os.remove(fp)
                except OSError:
                    pass
                continue
            seen.add(h)
            got += 1
            all_text += '\n' + t
            print(f'   ✓ [{len(t):>7}] {lk[:90]}')
            for ep in extract_endpoints(t):
                endpoints[ep] = endpoints.get(ep, 0) + 1
        if n_dup:
            print(f'   （跳过 {n_dup} 个重复页：同名或内容完全一致的分页）')

        print('📦 下载站内 JS…')
        jss = sorted(extract_js(home, url, base_host))
        for i, ju in enumerate(jss[:40]):
            name = ju.split('/')[-1].split('?')[0]
            # 安全网：业务 JS 超过 500KB 极罕见，截断避免卡在一个巨型 bundle 上
            t = curl(ju, out=os.path.join(raw_dir, 'js_' + name),
                     extra=['--max-filesize', '500000'])
            all_text += '\n' + t
            print(f'   ✓ [{len(t):>7}] {ju[:90]}')
            for ep in extract_endpoints(t):
                endpoints[ep] = endpoints.get(ep, 0) + 1

    # 首页里也可能直接内联
    for ep in extract_endpoints(home):
        endpoints[ep] = endpoints.get(ep, 0) + 1

    eps = [e for e, _ in sorted(endpoints.items(), key=lambda x: -x[1])]
    with open(os.path.join(args.out, 'endpoints.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(eps))
    print(f'\n🔎 候选接口 {len(eps)} 个，开始探测（返回 JSON 的才是宝贝）')

    def probe(full):
        """返回 (文本, 解析后的对象)；失败返回 (None, None)"""
        txt = curl(full, timeout=15)
        if not txt or not looks_json(txt):
            return None, None
        try:
            obj = json.loads(txt)
        except Exception:
            return None, None
        return txt, obj if isinstance(obj, dict) else None

    def probe_with_params(full):
        """空数据接口补参再探：POST JSON / POST 表单 / GET 带分页参数。

        很多后台接口（新闻列表、留言、黑名单分页）默认 GET 返回空，
        必须带 pageNum/pageSize 才吐数据。
        """
        cands = [
            ('POST', full, ['-X', 'POST', '-H', 'Content-Type: application/json',
                            '-d', '{"pageNum":1,"pageSize":20}']),
            ('POST', full, ['-X', 'POST', '-H', 'Content-Type: application/json',
                            '-d', '{}']),
            ('POST', full, ['-X', 'POST', '-d', 'pageNum=1&pageSize=20']),
            ('GET', full + ('&' if '?' in full else '?') + 'pageNum=1&pageSize=20', []),
        ]
        for method, target, extra in cands:
            txt = curl(target, timeout=15, extra=extra)
            if not txt or not looks_json(txt):
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                continue
            if isinstance(obj, dict) and count_items(obj) > 0:
                return txt, obj, f'{method} {extra[-1][:40]}' if extra else method
        return None, None, None

    hits = []
    for ep in eps[:60]:
        full = urllib.parse.urljoin(scheme_host, ep)
        txt, obj = probe(full)
        if obj is None:
            continue
        code = obj.get('code')
        data = obj.get('data')
        if data in (None, '', [], {}) and code not in (1, 0, 200, '200', '1'):
            continue
        # 过滤掉明显无业务价值的
        if isinstance(data, dict) and len(data) == 0:
            continue
        name = re.sub(r'[^A-Za-z0-9_]', '_', ep.strip('/'))[:50] or 'root'
        fp = os.path.join(api_dir, name + '.json')
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(txt)
        n = count_items(obj)
        desc = summarize_json(fp)
        hits.append([ep, len(txt), n, desc, full])
        mark = '✅' if n > 0 else '⚠️  空数据'
        print(f'   {mark} {ep}  → {len(txt)} 字节 / {n} 项\n        {desc[:140]}')

    # 第二遍：空数据接口补参再探（POST / 带分页参数），常能救回新闻、留言、名单类接口
    empties = [h for h in hits if h[2] == 0]
    if empties:
        print(f'\n🔁 补参再探 {len(empties)} 个空接口（试 POST + 分页参数）')
        for h in empties:
            txt, obj, how = probe_with_params(h[4])
            if obj is None:
                continue
            n = count_items(obj)
            if n <= 0:
                continue
            ep = h[0]
            name = re.sub(r'[^A-Za-z0-9_]', '_', ep.strip('/'))[:50] or 'root'
            fp = os.path.join(api_dir, name + '.json')
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(txt)
            h[1], h[2] = len(txt), n
            h[3] = summarize_json(fp)
            h.append(how)
            print(f'   🎯 {ep}  → {n} 项（{how}）')

    # 侦察小结
    rep = ['# 侦察小结', '',
           f'- 目标：{url}', f'- JS 渲染：{"是（WebFetch 不可用，必须用 raw 目录里的原始 HTML）" if is_js_rendered else "否"}',
           f'- 页面：{len([f for f in os.listdir(raw_dir) if f.endswith(".html")])} 个',
           f'- 候选接口：{len(eps)} 个 / 命中 JSON：{len(hits)} 个'
           f'（其中有数据 {len([h for h in hits if h[2] > 0])} 个）', '',
           '## 有价值接口（按数据量排序）', '']
    for h in sorted([h for h in hits if h[2] > 0], key=lambda x: -x[1]):
        rep.append(f'- `{h[0]}` — {h[1]} 字节，{h[2]} 项')
        rep.append(f'  - 结构：`{h[3][:200]}`')
        if len(h) > 5 and h[5]:
            rep.append(f'  - 调用方式：需 **{h[5]}** 才有数据（GET 默认返回空）')
    empties = [h for h in hits if h[2] == 0]
    if empties:
        rep += ['', '## 空数据接口（补参仍为空，多半需鉴权或必填业务参数）', '']
        for h in empties:
            rep.append(f'- `{h[0]}` — {h[1]} 字节，结构 `{h[3][:120]}`')
    rep += ['', '## 下一步', '',
            '1. 用 `html_to_text.py` 批量转换 raw/*.html 读取正文',
            '2. 重点读取上面命中的 JSON，它们通常包含**门店/品牌/产品线/区域**等真实结构化数据',
            '3. 用 WebSearch 补充：管理层姓名职务、年度，营收、行业榜单、信息化供应商案例']
    with open(os.path.join(args.out, 'recon-report.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(rep))

    print(f'\n📁 输出目录：{os.path.abspath(args.out)}')
    print(f'   raw/ 页面 {len([f for f in os.listdir(raw_dir) if f.endswith(".html")])} 个 · api/ 接口 {len(hits)} 个')
    print(f'   📄 侦察小结：{os.path.join(args.out, "recon-report.md")}')


if __name__ == '__main__':
    main()
