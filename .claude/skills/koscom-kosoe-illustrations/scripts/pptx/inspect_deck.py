"""덱 구조와 삽화 넣을 자리를 파악한다.

1) 슬라이드별 레이아웃, 도형(그룹 안까지) 이름·위치·텍스트를 출력한다.
2) render.ps1로 만든 PNG가 있으면, 흰 배경 장표의 '제목 오른쪽 상단 빈 띠' 폭을 잰다.
   → 스팟 일러스트를 넣을 수 있는 장표와 왼쪽 경계(인치)를 알려 준다.

사용: python inspect_deck.py deck.pptx [renders_dir] [--band 0.45,2.2] [--right 12.55]
"""
import argparse
import glob
import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

EMU = 914400


def walk(shapes, depth=1):
    for sh in shapes:
        pad = '  ' * depth
        geo = f'x{sh.left / EMU:.2f} y{sh.top / EMU:.2f} w{sh.width / EMU:.2f} h{sh.height / EMU:.2f}'
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            print(f'{pad}[G {sh.name}] {geo}')
            walk(sh.shapes, depth + 1)
        else:
            text = sh.text_frame.text.replace('\n', ' / ')[:90] if sh.has_text_frame else ''
            kind = 'PIC' if sh.shape_type == MSO_SHAPE_TYPE.PICTURE else 'SHP'
            if text or kind == 'PIC':
                print(f'{pad}{kind} {sh.name} {geo} | {text}')


def free_band(png, slide_w_in, band, right_in, white_min=600):
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(png).convert('L')).astype(int)
    h, w = im.shape
    px = w / slide_w_in
    # 배경이 흰색이 아니면(챕터·검은 장표) 건너뛴다
    if (im > 240).mean() < 0.55:
        return None
    ink = im[int(band[0] * px):int(band[1] * px)] < 235
    cols = ink.any(axis=0)
    x = int(right_in * px)
    while x > 0 and not cols[x]:
        x -= 1
    return x / px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pptx')
    ap.add_argument('renders', nargs='?')
    ap.add_argument('--band', default='0.45,2.2', help='상단 띠 y범위(인치)')
    ap.add_argument('--right', type=float, default=12.55, help='띠 오른쪽 끝(인치)')
    a = ap.parse_args()
    prs = Presentation(a.pptx)
    sw = prs.slide_width / EMU
    print(f'slide {sw:.2f} x {prs.slide_height / EMU:.2f} in, {len(prs.slides)} slides')
    for i, s in enumerate(prs.slides, 1):
        print(f'\n=== {i} [{s.slide_layout.name}]')
        walk(s.shapes)
    if a.renders:
        band = [float(v) for v in a.band.split(',')]
        print('\n# 제목 오른쪽 상단 빈 띠 (스팟 후보: 폭 2.0in 이상)')
        for png in sorted(glob.glob(os.path.join(a.renders, 's*.png'))):
            n = int(os.path.basename(png)[1:3])
            left = free_band(png, sw, band, a.right)
            if left is None:
                print(f'{n:02d}: 흰 배경 아님 — 건너뜀')
            else:
                width = a.right - left
                mark = '✓' if width >= 2.0 else '·'
                print(f'{n:02d}: {mark} free x {left:.2f}..{a.right:.2f} (w {width:.2f})')


if __name__ == '__main__':
    main()
