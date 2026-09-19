#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_html.py — 单文件交互 HTML 的三步交付前校验

第 1 步  node --check        ：JS 语法是否合法
第 2 步  DOM 桩里真跑一遍    ：渲染函数有没有运行时异常
第 3 步  断言渲染条数        ：数据有没有真的渲染出来（而不是静默失败）

用法：
    python3 verify_html.py report.html
    python3 verify_html.py report.html --expect '#parkList|pitem|39'
          --expect 格式： 容器选择器|条目的 class 名|期望数量
          例：#brandBars|brow|51  表示 #brandBars 里应渲染 51 个 class 含 brow 的条目
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

STUB = r'''
const store={};
function mk(){
  const el={_h:'',dataset:{},style:{display:''},value:'',id:'',
    classList:{add(){},remove(){},toggle(){},contains(){return false}},
    getAttribute(){return '#s1'},scrollIntoView(){},animate(){},appendChild(){},
    addEventListener(){},textContent:'',
    querySelector:()=>mk(), querySelectorAll:()=>[], closest:()=>null};
  Object.defineProperty(el,'innerHTML',{get(){return el._h},set(v){el._h=v}});
  el.parentElement=el; return el;
}
global.document={querySelector:mk,querySelectorAll:()=>[],createElement:mk,
  documentElement:{dataset:{},scrollTop:0,scrollHeight:1,clientHeight:1},
  addEventListener(){},body:mk()};
global.localStorage={getItem:k=>store[k]||null,setItem:(k,v)=>store[k]=v,
  removeItem:k=>delete store[k]};
global.performance={now:()=>0};
global.requestAnimationFrame=f=>f(0);
global.addEventListener=()=>{}; global.scrollTo=()=>{}; global.print=()=>{};
global.IntersectionObserver=class{constructor(){} observe(){}};
global.location={reload(){},href:'http://x/'};
global.window=global;
'''

CAPTURE = r'''
const __cap={};
const __orig=document.querySelector;
document.querySelector=sel=>{
  const e=__orig(sel);
  return new Proxy(e,{
    set(t,k,v){ if((k==='innerHTML'||k==='textContent')&&typeof v==='string')
                  __cap[sel]=(__cap[sel]||'')+v;
                t[k]=v; return true; },
    get(t,k){ const r=t[k];
              return (typeof r==='function')? r.bind(t) : r; }
  });
};
try{ __CODE__ }
catch(e){ console.log('__ERR__'+e.message+'\n'+e.stack.split('\n').slice(0,5).join('\n')); }
console.log('__CAP__'+JSON.stringify(__cap));
'''


def find_node():
    cands = [
        '/Users/itfamer/.workbuddy/binaries/node/versions/22.22.2-3/bin/node',
        '/Users/itfamer/.workbuddy/binaries/node/versions/20.18.0/bin/node',
        '/usr/local/bin/node', '/opt/homebrew/bin/node',
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    from shutil import which
    return which('node')


def top_classes(h, n=4):
    """统计容器里出现最多的 class 名，用于人工核对渲染条数"""
    from collections import Counter
    c = Counter()
    for m in re.finditer(r'class="([^"]+)"', h):
        first = m.group(1).split()[0]
        first = re.sub(r'\$\{.*', '', first)      # 去掉模板插值尾巴
        if first and len(first) < 24:
            c[first] += 1
    return c.most_common(n)


def count_cls(h, cls):
    return len(re.findall(r'class="[^"]*\b' + re.escape(cls) + r'\b', h))


def main():
    ap = argparse.ArgumentParser(description='单文件交互 HTML 交付前校验')
    ap.add_argument('file')
    ap.add_argument('--expect', action='append', default=[],
                    help='断言，格式 "#id:数量"，可多次传入')
    args = ap.parse_args()

    node = find_node()
    if not node:
        print('❌ 找不到 node，无法校验', file=sys.stderr)
        sys.exit(2)

    src = open(args.file, encoding='utf-8').read()
    scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', src, re.I)
    if not scripts:
        print('⚠️  没有找到 <script> 段，跳过')
        return
    # 取最长的一段作为主逻辑（模板通常只有一个大脚本）
    code = max(scripts, key=len)

    print('—' * 62)
    print('第 1 步 · JS 语法检查')
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(code)
        tmp = f.name
    r = subprocess.run([node, '--check', tmp], capture_output=True, text=True)
    if r.returncode != 0:
        print('❌ 语法错误：')
        print((r.stderr or '').strip()[:1200])
        os.unlink(tmp)
        sys.exit(1)
    print('✅ 语法通过')

    print('—' * 62)
    print('第 2 步 · DOM 桩运行时检查')
    runner = STUB + CAPTURE.replace('__CODE__', code)
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(runner)
        tmp2 = f.name
    r = subprocess.run([node, tmp2], capture_output=True, text=True, timeout=60)
    out = (r.stdout or '')
    if '__ERR__' in out:
        print('❌ 运行时异常：')
        print(out.split('__ERR__')[1].split('__CAP__')[0][:1200])
        sys.exit(1)
    print('✅ 渲染逻辑执行无异常')

    cap = {}
    if '__CAP__' in out:
        js = out.split('__CAP__')[1]
        try:
            cap = json.loads(js[:js.rfind('}') + 1])
        except Exception:
            pass

    print('—' * 62)
    print('第 3 步 · 渲染条数统计')
    if not cap:
        print('⚠️  未捕获到任何渲染输出')
    else:
        print(f'{"容器":<22}{"字符":>8}  主要条目（class × 数量）')
        for k, v in sorted(cap.items(), key=lambda x: -len(x[1])):
            if len(v) < 40:
                continue
            tc = ', '.join(f'{c}×{n}' for c, n in top_classes(v))
            print(f'{k:<22}{len(v):>8}  {tc}')

    ok = True
    if args.expect:
        print('—' * 62)
        print('断言结果')
        for e in args.expect:
            parts = [p.strip() for p in e.split('|')]
            if len(parts) != 3:
                print(f'  ⚠️  格式应为 #选择器|class名|数量，收到：{e}')
                continue
            sel, cls, want = parts
            got = count_cls(cap.get(sel, ''), cls)
            good = (got == int(want))
            ok = ok and good
            print(f'  {"✅" if good else "❌"} {sel} 的 .{cls} 期望 {want} / 实际 {got}')

    for f_ in (tmp, tmp2):
        try:
            os.unlink(f_)
        except Exception:
            pass

    print('—' * 62)
    if ok:
        print('🎉 全部通过，可以交付')
    else:
        print('⚠️  有断言未通过，请检查数据源')
        sys.exit(1)


if __name__ == '__main__':
    main()
