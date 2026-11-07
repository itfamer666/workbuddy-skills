#!/usr/bin/env python3
"""移除生成图右下角的服务侧角标（纯 Pillow，无需 NumPy / OpenCV）。

算法为实测验证版本：
  保守修补区 → 左侧同尺寸暗部纹理水平翻转平移 → 与 30px 高斯低频基底混合
  → 羽化只放左/上边界，右/下贴图像边界全强度替换

用法：
  python3 remove_corner_badge.py <图1> [<图2> ...] --out-dir <新目录> [--suffix _无角标]

判据：修补区亮度 >42 的近中性像素数归零，并另做放大目视复查。
"""
import argparse
import os
from PIL import Image, ImageFilter, ImageDraw

# 2048x1152 上实测角标亮像素包围盒 (1913,1084)-(2036,1140)
# 保守修补区取 (1876,1058) 起至边界，换算为比例以适配其他画幅
RATIO_X = 1876 / 2048
RATIO_Y = 1058 / 1152
FEATHER = 18


def bright_count(im, rx0, ry0):
    px = im.load()
    W, H = im.size
    n = 0
    # 统计范围比修补区略宽，用于确认边缘没有残留
    x0 = max(0, rx0 - 36)
    y0 = max(0, ry0 - 28)
    for y in range(y0, H):
        for x in range(x0, W):
            r, g, b = px[x, y]
            if (r + g + b) // 3 > 42 and abs(r - g) < 45 and abs(g - b) < 45:
                n += 1
    return n


def repair(im, rx0=None, ry0=None, feather=FEATHER):
    W, H = im.size
    if rx0 is None:
        rx0 = int(W * RATIO_X)
    if ry0 is None:
        ry0 = int(H * RATIO_Y)
    rx1, ry1 = W, H
    rw, rh = rx1 - rx0, ry1 - ry0
    if rw <= 0 or rh <= 0 or rx0 - rw < 0:
        raise ValueError("画幅过小或修补区比例不适用，请用 --rx0 / --ry0 显式指定")

    before = bright_count(im, rx0, ry0)

    # 源块：修补区左侧同尺寸暗部纹理，水平翻转后平移
    src = im.crop((rx0 - rw, ry0, rx0, ry1)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    # 低频基底：保留局部明暗趋势，避免补出突兀纯黑
    lowfreq = im.filter(ImageFilter.GaussianBlur(radius=30)).crop((rx0, ry0, rx1, ry1))
    src = Image.blend(src.filter(ImageFilter.GaussianBlur(radius=1.4)), lowfreq, 0.34)

    # 蒙版：内部全不透明；仅左、上两边羽化；右、下贴图像边界不做羽化
    mask = Image.new("L", (rw, rh), 255)
    d = ImageDraw.Draw(mask)
    for i in range(feather):
        a = int(255 * (i / feather))
        d.line((i, 0, i, rh - 1), fill=a)
        d.line((0, i, rw - 1, i), fill=a)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2.5))
    d2 = ImageDraw.Draw(mask)
    d2.rectangle((rw - 6, 0, rw - 1, rh - 1), fill=255)
    d2.rectangle((0, rh - 6, rw - 1, rh - 1), fill=255)

    out = im.copy()
    out.paste(src, (rx0, ry0), mask)
    after = bright_count(out, rx0, ry0)
    return out, before, after, (rx0, ry0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--suffix", default="_无角标")
    ap.add_argument("--rx0", type=int)
    ap.add_argument("--ry0", type=int)
    ap.add_argument("--feather", type=int, default=FEATHER)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    for path in args.inputs:
        im = Image.open(path).convert("RGB")
        out, before, after, origin = repair(im, args.rx0, args.ry0, args.feather)
        stem, ext = os.path.splitext(os.path.basename(path))
        name = stem + args.suffix + (ext or ".png")
        dst = os.path.join(args.out_dir, name)
        out.save(dst)
        print(f"{os.path.basename(path)}: size={out.size} origin={origin} "
              f"corner bright>42 {before} -> {after}  saved={dst}")
        if after > 0:
            print("  WARN: 仍有亮色残留，请放大复查或调小 --rx0 / --ry0 扩大修补区")


if __name__ == "__main__":
    main()
