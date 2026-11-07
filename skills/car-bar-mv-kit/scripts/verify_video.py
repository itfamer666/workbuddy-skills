#!/usr/bin/env python3
"""视频成片验收：读取真实元信息、音轨音量，抽帧生成拼图与右下角放大图。

依赖：ffmpeg + Pillow（无需 ffprobe / NumPy / OpenCV）。

用法：
  python3 verify_video.py <视频.mp4> --out-dir <目录> [--times 0,1.2,2.5,3.8,4.8]

产出：
  frames_grid.png   抽帧拼图（供图像查看能力逐帧核对）
  corner_zoom.png   末帧右下角放大图（查角标）
  控制台摘要        时长 / 分辨率 / fps / 帧数 / 流 / 音轨 mean & max volume
"""
import argparse
import os
import re
import shutil
import subprocess
from PIL import Image, ImageDraw


def find_ffmpeg(explicit=None):
    if explicit:
        return explicit
    p = shutil.which("ffmpeg")
    if p:
        return p
    fallback = os.path.expanduser("~/.local/bin/ffmpeg")
    if os.path.exists(fallback):
        return fallback
    raise RuntimeError("未找到 ffmpeg，请用 --ffmpeg 指定路径")


def probe(ffmpeg, video):
    # 用 ffmpeg -i 读元信息（无 ffprobe）；命令无输出文件会返回非 0，但 stderr 含完整信息
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", video],
                       capture_output=True, text=True)
    info = r.stderr
    duration = re.search(r"Duration:\s*([0-9:.]+)", info)
    vstream = re.search(r"Video:\s*([^\n]+)", info)
    astream = re.search(r"Audio:\s*([^\n]+)", info)
    res = re.search(r"(\d{3,5})x(\d{3,5})", vstream.group(1)) if vstream else None
    fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", vstream.group(1)) if vstream else None
    return {
        "duration": duration.group(1) if duration else "未读到",
        "resolution": f"{res.group(1)}x{res.group(2)}" if res else "未读到",
        "fps": fps.group(1) if fps else "未读到",
        "video_stream": vstream.group(1).strip() if vstream else "无",
        "audio_stream": astream.group(1).strip() if astream else "无音轨",
    }


def volume(ffmpeg, video):
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", video,
                        "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", r.stderr)
    mx = re.search(r"max_volume:\s*([-\d.]+)\s*dB", r.stderr)
    return (mean.group(1) if mean else None, mx.group(1) if mx else None)


def frame_count(ffmpeg, video):
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", video,
                        "-map", "0:v:0", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"frame=\s*(\d+)", r.stderr)
    return m.group(1) if m else "未读到"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--times", default="0,1.2,2.5,3.8,4.8")
    ap.add_argument("--ffmpeg")
    args = ap.parse_args()

    ffmpeg = find_ffmpeg(args.ffmpeg)
    os.makedirs(args.out_dir, exist_ok=True)
    times = [t.strip() for t in args.times.split(",") if t.strip()]

    meta = probe(ffmpeg, args.video)
    mean, mx = volume(ffmpeg, args.video)
    frames = frame_count(ffmpeg, args.video)

    print("=== 成片实读规格 ===")
    print(f"时长      : {meta['duration']}")
    print(f"分辨率    : {meta['resolution']}   fps: {meta['fps']}   帧数: {frames}")
    print(f"视频流    : {meta['video_stream']}")
    print(f"音频流    : {meta['audio_stream']}")
    if mean is not None:
        print(f"音轨音量  : mean {mean} dB / max {mx} dB  -> 非静音，交付须提示后期静音或替换")
    else:
        print("音轨音量  : 未检测到有效音频（静音或无音轨）")

    paths = []
    for t in times:
        out = os.path.join(args.out_dir, f"frame_{t}.png")
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error",
                        "-ss", t, "-i", args.video, "-frames:v", "1", "-y", out],
                       capture_output=True, text=True)
        if os.path.exists(out):
            paths.append((t, out))

    if not paths:
        print("WARN: 未抽到任何帧")
        return

    ims = [(t, Image.open(p).convert("RGB")) for t, p in paths]
    tw = 640
    th = int(ims[0][1].height * tw / ims[0][1].width)
    cols = 2
    rows = (len(ims) + cols - 1) // cols
    grid = Image.new("RGB", (tw * cols, (th + 28) * rows), (20, 20, 20))
    d = ImageDraw.Draw(grid)
    for i, (t, im) in enumerate(ims):
        c = im.resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 28)
        grid.paste(c, (x, y))
        d.text((x + 8, y + th + 6), f"t = {t} s", fill=(255, 255, 0))
    grid_path = os.path.join(args.out_dir, "frames_grid.png")
    grid.save(grid_path)
    print(f"抽帧拼图  : {grid_path}  ({len(ims)} 帧)")

    last = ims[-1][1]
    W, H = last.size
    corner = last.crop((int(W * 0.82), int(H * 0.86), W, H))
    corner = corner.resize((corner.width * 2, corner.height * 2), Image.LANCZOS)
    corner_path = os.path.join(args.out_dir, "corner_zoom.png")
    corner.save(corner_path)
    print(f"右下角放大: {corner_path}")

    print("=== 待人工核对 ===")
    print("主唱动作 / 车辆静止与形态 / 乐队 / 场景一致性 / 新增文字 / 角标；")
    print("「画面流畅」「运镜连贯」「口型贴合」无法从抽帧确认，需实际播放查看。")


if __name__ == "__main__":
    main()
