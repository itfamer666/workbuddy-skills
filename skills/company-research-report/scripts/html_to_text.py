#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html_to_text.py — 批量把抓取的 HTML 转成可阅读的纯文本

用法：
    python3 html_to_text.py ./recon/raw                # 输出到一个合并文件
    python3 html_to_text.py ./recon/raw -o all.txt
    python3 html_to_text.py ./recon/raw --per-file     # 每个页面单独输出
    python3 html_to_text.py ./recon/raw --dedupe       # 去掉重复的导航文案（推荐）
"""
import argparse
import html
import os
import re
import sys


def strip_html(d):
    d = re.sub(r'<script[\s\S]*?</script>', '', d, flags=re.I)
    d = re.sub(r'<style[\s\S]*?</style>', '', d, flags=re.I)
    d = re.sub(r'<!--[\s\S]*?-->', '', d)
    d = re.sub(r'<[^>]+>', '\n', d)
    d = html.unescape(d)
    lines = [l.strip() for l in d.split('\n') if l.strip()]
    return lines


def dedupe_lines(lines):
    """去掉连续重复行（导航/页脚在各页反复出现）"""
    out, prev = [], None
    for l in lines:
        if l != prev:
            out.append(l)
        prev = l
    return out


def dedupe_across(pages_lines):
    """
    跨页去重：某行若在半数以上页面都出现过且长度较短，
    判定为通用页眉/页脚/导航并剔除，让每页只保留独有正文。
    """
    from collections import Counter
    if len(pages_lines) < 3:
        return pages_lines
    c = Counter()
    seen = []
    for lines in pages_lines:
        s = set(lines)
        seen.append(s)
        c.update(s)
    thresh = max(2, int(len(pages_lines) * 0.5))
    boiler = {l for l, n in c.items() if n >= thresh and len(l) < 30}
    return [[l for l in lines if l not in boiler] for lines in pages_lines]


def main():
    ap = argparse.ArgumentParser(description='HTML 批量转纯文本')
    ap.add_argument('dir', help='包含 .html 的目录，或单个 .html 文件')
    ap.add_argument('-o', '--out', default=None, help='合并输出文件')
    ap.add_argument('--per-file', action='store_true', help='每个输入文件单独输出 .txt')
    ap.add_argument('--dedupe', action='store_true', help='跨页去掉重复导航/页脚')
    ap.add_argument('--max-chars', type=int, default=0, help='单页正文截断字符数，0=不截断')
    args = ap.parse_args()

    if os.path.isfile(args.dir):
        files = [args.dir]
    else:
        files = sorted(os.path.join(args.dir, f) for f in os.listdir(args.dir)
                       if f.lower().endswith(('.html', '.htm')))
    if not files:
        print('❌ 没有找到 HTML 文件', file=sys.stderr)
        sys.exit(1)

    pages = []
    for fp in files:
        try:
            d = open(fp, encoding='utf-8', errors='ignore').read()
        except Exception as e:
            print(f'  跳过 {fp}: {e}')
            continue
        # 顺便提取 title
        tm = re.search(r'<title[^>]*>([\s\S]*?)</title>', d, re.I)
        title = html.unescape(tm.group(1)).strip() if tm else os.path.basename(fp)
        lines = dedupe_lines(strip_html(d))
        body = '\n'.join(lines)
        if args.max_chars and len(body) > args.max_chars:
            body = body[:args.max_chars] + '\n…（已截断）'
        pages.append((fp, title, body))

    if args.dedupe:
        bodies = dedupe_across([p[2].split('\n') for p in pages])
        pages = [(p[0], p[1], '\n'.join(b)) for p, b in zip(pages, bodies)]

    if args.per_file:
        outdir = args.out or (os.path.dirname(files[0]) + '_txt')
        os.makedirs(outdir, exist_ok=True)
        for fp, title, body in pages:
            name = os.path.splitext(os.path.basename(fp))[0] + '.txt'
            with open(os.path.join(outdir, name), 'w', encoding='utf-8') as f:
                f.write(body)
        print(f'✅ 输出 {len(pages)} 个文件到 {outdir}')
        return

    merged = '\n\n'.join(f'{"=" * 70}\n【{title}】 源文件：{os.path.basename(fp)}\n{"=" * 70}\n{body}'
                         for fp, title, body in pages)
    total = len(merged)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(merged)
        print(f'✅ 已写入 {args.out}（{total} 字符，共 {len(pages)} 页）')
    else:
        limit = 60000
        print(merged[:limit])
        if total > limit:
            print(f'\n… （正文共 {total} 字符，已显示前 {limit}；建议用 -o 输出到文件后分段阅读）')


if __name__ == '__main__':
    main()
