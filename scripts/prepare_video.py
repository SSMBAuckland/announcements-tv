#!/usr/bin/env python3
"""Make a video ready for the TV: crop it to the part worth showing, drop the sound, shrink it, and save it twice,
as WebM (what the TV plays) and as MP4 next to it (for phones that can't play WebM).

Usage:  python3 scripts/prepare_video.py SOURCE TARGET.webm [--crop X,Y,W,H] [--start SECONDS] [--seconds N]

- TARGET: where it goes in this repository, e.g. videos/2026-11-06-dhanteras.webm (the .mp4 is written beside it).
- --crop: the part to keep, in percent of the picture: left, top, width, height (as in prepare_image.py).
- --start: skip an intro, so the loop on the TV doesn't restart with it (e.g. 1 for a title that fades in).
- --seconds: keep at most this long (default 20); the TV loops it.
The longest side is at most 960 px (the video fills part of a 1920x1080 screen), with no sound, so files stay small
and play smoothly on the TV players. Needs ffmpeg.
"""
import argparse
import os
import re
import subprocess
import sys

MAX_SIDE = 960


def size_of(path):
    """Width and height of the first video stream, read from ffmpeg's own report."""
    err = subprocess.run(['ffmpeg', '-hide_banner', '-i', path], capture_output=True, text=True).stderr
    m = re.search(r'Video:.*?(\d{2,5})x(\d{2,5})', err)
    if not m:
        sys.exit('not a video: ' + path)
    return int(m.group(1)), int(m.group(2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('target')
    ap.add_argument('--crop', help='X,Y,W,H in percent')
    ap.add_argument('--start', type=float, default=0)
    ap.add_argument('--seconds', type=float, default=20)
    a = ap.parse_args()
    if not a.target.endswith('.webm'):
        sys.exit('the target must be a .webm file')
    sw, sh = size_of(a.source)
    w, h = sw, sh
    filters = []
    if a.crop:
        x, y, cw, ch = (max(0.0, min(100.0, float(v))) for v in a.crop.split(','))
        cw, ch = max(cw, 10.0), max(ch, 10.0)
        x, y = min(x, 100 - cw), min(y, 100 - ch)
        w, h = round(sw * cw / 100), round(sh * ch / 100)
        filters.append('crop=%d:%d:%d:%d' % (w, h, round(sw * x / 100), round(sh * y / 100)))
    scale = min(1.0, MAX_SIDE / max(w, h))
    filters.append('scale=%d:%d' % (int(w * scale) // 2 * 2, int(h * scale) // 2 * 2))
    filters.append('fps=30')
    base = ['ffmpeg', '-v', 'error', '-y', '-ss', str(a.start), '-t', str(a.seconds), '-i', a.source, '-an', '-vf', ','.join(filters)]
    os.makedirs(os.path.dirname(a.target) or '.', exist_ok=True)
    mp4 = a.target[:-5] + '.mp4'
    subprocess.run(base + ['-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '36', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '4', a.target], check=True)
    subprocess.run(base + ['-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-profile:v', 'main', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], check=True)
    for p in (a.target, mp4):
        print('%s: %d KB' % (p, os.path.getsize(p) // 1024))


if __name__ == '__main__':
    main()
