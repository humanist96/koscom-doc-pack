"""코쇠 일러스트를 덱에 넣는다.

- replace: 기존 그림(예: '일러스트 생성 대기' 자리)을 같은 위치·크기 그대로 새 그림으로 교체
- spots:   흰 배경 장표의 제목 오른쪽 상단 빈 띠에 작은 스팟 일러스트를 오른쪽 정렬로 배치

생성 이미지의 옅은 회색 바탕은 순백으로 맞추고(슬라이드 위 사각 테두리 방지),
투명 PNG는 흰 배경으로 합친다. 스팟은 여백을 잘라 낸 뒤 띠 안에 맞춘다.

사용: python insert_images.py in.pptx out.pptx plan.json
plan.json 예:
{
  "replace": [{"slide": 4, "picture": "Image 9", "image": "img/ch1.png", "name": "Kosoe Illustration ch1", "alt": "설명"}],
  "spots":   [{"slide": 5, "image": "img/s05.png", "left": 8.37, "alt": "설명"}],
  "band":    {"top": 0.45, "bottom": 2.05, "right": 12.5, "gap": 0.45, "max_w": 3.4}
}
spots[].left = inspect_deck.py가 알려 준 빈 띠의 왼쪽 경계(인치)
"""
import io
import json
import sys

import numpy as np
from PIL import Image, ImageChops
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches


def load_rgb(path):
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    return im.convert('RGB')


def whiten(im, floor=228):
    """옅은 회색 바탕 → 순백."""
    a = np.asarray(im.convert('RGB')).astype(np.int16)
    lo, hi = a.min(axis=2), a.max(axis=2)
    a[(lo >= floor) & (hi - lo <= 14)] = 255
    return Image.fromarray(a.astype('uint8'))


def png(im):
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    buf.seek(0)
    return buf


def trimmed(path, pad_ratio=0.04):
    im = whiten(load_rgb(path))
    diff = ImageChops.difference(im, Image.new('RGB', im.size, 'white')).convert('L').point(lambda v: 255 if v > 18 else 0)
    l, t, r, b = diff.getbbox() or (0, 0, *im.size)
    pad = int(max(r - l, b - t) * pad_ratio)
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


def cover_crop(path, aspect):
    im = whiten(load_rgb(path))
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect)
        return im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = int(w / aspect)
    return im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))


def find_picture(shapes, name):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            hit = find_picture(sh.shapes, name)
            if hit is not None:
                return hit
        elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE and sh.name == name:
            return sh
    return None


def main(src, out, plan_path):
    plan = json.load(open(plan_path, encoding='utf-8'))
    band = {'top': 0.45, 'bottom': 2.05, 'right': 12.5, 'gap': 0.45, 'max_w': 3.4, **plan.get('band', {})}
    prs = Presentation(src)
    slides = list(prs.slides)

    for r in plan.get('replace', []):
        slide = slides[r['slide'] - 1]
        pic = find_picture(slide.shapes, r['picture'])
        assert pic is not None, f"slide {r['slide']}: picture '{r['picture']}' not found"
        _, rId = slide.part.get_or_add_image_part(png(cover_crop(r['image'], pic.width / pic.height)))
        pic._element.blipFill.blip.rEmbed = rId
        pic.name = r.get('name', pic.name)
        if r.get('alt'):
            pic._element.nvPicPr.cNvPr.set('descr', r['alt'])
        print(f"slide {r['slide']}: replaced '{r['picture']}'")

    for s in plan.get('spots', []):
        slide = slides[s['slide'] - 1]
        im = trimmed(s['image'])
        box_l = s['left'] + band['gap']
        box_w = min(band['right'] - box_l, band['max_w'])
        box_h = band['bottom'] - band['top']
        k = min(box_w / im.width, box_h / im.height)
        w, h = im.width * k, im.height * k
        x, y = band['right'] - w, band['top'] + (box_h - h) / 2
        pic = slide.shapes.add_picture(png(im), Inches(x), Inches(y), Inches(w), Inches(h))
        pic.name = s.get('name', f"Kosoe Spot s{s['slide']:02d}")
        if s.get('alt'):
            pic._element.nvPicPr.cNvPr.set('descr', s['alt'])
        print(f"slide {s['slide']}: spot at x{x:.2f} y{y:.2f} w{w:.2f} h{h:.2f}")

    prs.save(out)
    print('saved', out)


if __name__ == '__main__':
    main(*sys.argv[1:4])
