#!/usr/bin/env python3
"""Make a picture ready for the TV: crop it to the part worth showing, turn it upright, shrink it and save it as JPEG.

Usage:  python3 scripts/prepare_image.py SOURCE TARGET [--crop X,Y,W,H]

- SOURCE: the picture as the admins sent it (any format Pillow reads).
- TARGET: where it goes in this repository, e.g. images/2026-10-31-lalji-maharajs-visit.jpg.
- --crop: the part to keep, in percent of the picture: left, top, width, height (e.g. 0,42,100,58 keeps the bottom
  58%). Leave it out to keep the whole picture.
The longest side is at most 1600 px (the picture fills at most part of a 1920x1080 screen), so files stay small.
Needs: pip install pillow
"""
import argparse
import os

from PIL import Image, ImageOps

MAX_SIDE = 1600


def crop_box(size, crop):
    """Pixel box for a crop given in percent, kept inside the picture and at least 10% of each side."""
    w, h = size
    x, y, cw, ch = (max(0.0, min(100.0, float(v))) for v in crop)
    cw, ch = max(cw, 10.0), max(ch, 10.0)
    x, y = min(x, 100 - cw), min(y, 100 - ch)
    return (round(w * x / 100), round(h * y / 100), round(w * (x + cw) / 100), round(h * (y + ch) / 100))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('target')
    ap.add_argument('--crop', help='X,Y,W,H in percent')
    a = ap.parse_args()
    img = ImageOps.exif_transpose(Image.open(a.source)).convert('RGB')
    if a.crop:
        parts = [p for p in a.crop.split(',') if p.strip()]
        if len(parts) == 4 and not (float(parts[2]) >= 100 and float(parts[3]) >= 100):
            img = img.crop(crop_box(img.size, parts))
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    os.makedirs(os.path.dirname(a.target) or '.', exist_ok=True)
    img.save(a.target, 'JPEG', quality=84, optimize=True, progressive=True)
    print('%s: %dx%d, %d KB' % (a.target, img.width, img.height, os.path.getsize(a.target) // 1024))


if __name__ == '__main__':
    main()
