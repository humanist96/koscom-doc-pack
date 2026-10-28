#!/usr/bin/env python3
"""
koscom-hwp-report - 그림 여백 자르기

보고서에 넣을 그림(특히 흰 여백을 넉넉히 두는 코쇠 삽화)의 바깥 흰 여백을 잘라 낸다.
여백이 많은 16:9 삽화를 그대로 넣으면 같은 폭에서 그림이 높아져 쪽이 넘어가고 빈 공간이 생긴다.
내용 경계(밝기 235 미만인 픽셀)를 찾고, 그림 폭의 일정 비율만큼 여유를 남겨 자른다.
원본은 그대로 두고 `<이름>-crop.png`(또는 -o 경로)로 저장한다.

Usage:
    python scripts/crop_image.py <image> [<image> ...] [-o OUT] [--margin 0.03]

Examples:
    python scripts/crop_image.py illustrations/01-engine.png
    python scripts/crop_image.py illustrations/*.png --margin 0.05

Dependencies:
    Pillow
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from typing import Optional

THRESHOLD = 235


def utf8_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))


def crop(src: Path, out: Path, margin: float) -> str:
    from PIL import Image

    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        # 투명 배경은 문서에서 검게 보일 수 있어 흰 배경으로 합친다
        rgba = im.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        bg.alpha_composite(rgba)
        im = bg
    im = im.convert("RGB")
    box = im.convert("L").point(lambda v: 255 if v < THRESHOLD else 0).getbbox()
    if box is None:
        return f"WARN {src.name}: 내용이 없는 흰 그림 — 자르지 않음"
    w, h = im.size
    m = int(w * margin)
    x0, y0, x1, y1 = max(0, box[0] - m), max(0, box[1] - m), min(w, box[2] + m), min(h, box[3] + m)
    im.crop((x0, y0, x1, y1)).save(out)
    cw, ch = x1 - x0, y1 - y0
    return f"OK {out} {w}x{h} → {cw}x{ch} (가로세로 {cw / ch:.2f}, 폭 130mm면 높이 약 {130 * ch / cw:.0f}mm)"


def main(argv: Optional[list[str]] = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="그림의 바깥 흰 여백을 잘라 보고서용으로 저장")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="저장 경로(그림이 하나일 때만)")
    parser.add_argument("--margin", type=float, default=0.03, help="남길 여유(그림 폭 대비, 기본 0.03)")
    args = parser.parse_args(argv)
    if args.out and len(args.images) > 1:
        print("ERROR -o는 그림이 하나일 때만 쓸 수 있음")
        return 1
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("ERROR Pillow 없음 — pip install Pillow")
        return 1
    code = 0
    for src in args.images:
        if not src.is_file():
            print(f"ERROR 파일 없음: {src}")
            code = 1
            continue
        out = args.out or src.with_name(src.stem + "-crop.png")
        print(crop(src, out, args.margin))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
