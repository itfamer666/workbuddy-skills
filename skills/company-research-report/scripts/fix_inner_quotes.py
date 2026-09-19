#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_inner_quotes.py — 修复单文件 HTML 里"中文文案中的 ASCII 双引号"

【为什么需要】
写研究报告时，中常出现：{y:2006,c:"成立"东创建国汽车集团"，颁布集团 VI 标准"}
其中内层的 " 会提前结束 JS 字符串 → 整个页面白屏，控制台报 SyntaxError。

【判别规则】
一个 " 只有在"前后都不是 JS 语法分隔符"时，才是文案内部引号：
  - 前一个字符是汉字（或前一个也是 " 且后一个是汉字）→ 疑似内部引号
  - 且下一个字符不是 ASCII 的 , } ] ) ; + 空白换行 → 才真正替换
    （全角逗号"，"是文案，半角逗号","是语法 —— 这是区分的关键）
开/合按出现顺序交替替换为 “ 和 ”。

用法：
    python3 fix_inner_quotes.py report.html           # 就地修复并备份 .bak
    python3 fix_inner_quotes.py report.html --dry-run # 只报告不修改
    python3 fix_inner_quotes.py report.html --check   # 只检查是否有隐患
"""
import argparse
import sys

FW = '，。、；：！？（）《》【】·—～…“”'


def cjk(ch):
    return bool(ch) and '\u4e00' <= ch <= '\u9fff'


def fw(ch):
    return ch in FW


def find_bad(seg):
    """返回需要替换的下标列表"""
    # 前面是这些字符 → 一定是 JS 语法定界符（k:"v" / a=="x" / [ "x" / fn("x"）
    SKIP_PREV = '=,([{:`'
    # 后面是这些字符 → 一定是 JS 语法定界符（"v", / "v"} / "v"?x:y / "v".length）
    SKIP_NEXT = ',}]) ;\n\t+?:.`'
    idx = []
    n = len(seg)
    for i, ch in enumerate(seg):
        if ch != '"':
            continue
        prev = seg[i - 1] if i > 0 else ''
        nxt = seg[i + 1] if i + 1 < n else ''
        if prev in SKIP_PREV or nxt in SKIP_NEXT:
            continue                      # 语法定界符，不动
        inner_open = cjk(prev) or (prev == '"' and cjk(nxt))
        inner_close = (cjk(prev) or fw(prev)) and (cjk(nxt) or fw(nxt))
        if inner_open or inner_close:
            idx.append(i)
    return idx


def process(text):
    out = list(text)
    hits = find_bad(text)
    for k, i in enumerate(hits):
        out[i] = '\u201c' if k % 2 == 0 else '\u201d'
    return ''.join(out), len(hits)


def main():
    ap = argparse.ArgumentParser(description='修复 HTML 中 JS 字符串内的中文引号')
    ap.add_argument('file')
    ap.add_argument('--dry-run', action='store_true', help='只报告不修改')
    ap.add_argument('--check', action='store_true', help='有隐患返回退出码 1')
    args = ap.parse_args()

    src = open(args.file, encoding='utf-8').read()

    # 只处理 <script> 内的代码段，避免动到正文 HTML
    parts, result, total = [], 0, []
    pos = 0
    for m in __import__('re').finditer(r'<script[^>]*>([\s\S]*?)</script>', src, __import__('re').I):
        total.append(src[pos:m.start(1)])
        fixed, n = process(m.group(1))
        result += n
        total.append(fixed)
        pos = m.end(1)
    total.append(src[pos:])
    new = ''.join(total)

    print(f'发现内部引号 {result} 处 → {"（奇数，可能仍在误伤！请人工复核）" if result % 2 else "（成对 OK）"}')

    if args.check:
        sys.exit(1 if result else 0)
    if args.dry_run:
        print('（dry-run，未修改文件）')
        return
    if result:
        open(args.file + '.bak', 'w', encoding='utf-8').write(src)
        open(args.file, 'w', encoding='utf-8').write(new)
        print(f'✅ 已修复并备份到 {args.file}.bak')
    else:
        print('✅ 无需修改')


if __name__ == '__main__':
    main()
