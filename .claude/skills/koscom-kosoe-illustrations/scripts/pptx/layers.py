"""메인 일러스트를 애니메이션용 레이어로 분리한다.

원본 그림에서 움직일 요소를 잘라 투명 PNG로 만들고, 배경에서는 그 자리를 흰색으로 지운다.
레이어는 원본 좌표를 기억하므로 슬라이드에 정확히 겹쳐 놓을 수 있다(애니메이션 끝 장면 = 원본 그림).

사용: python layers.py spec.json [--out layer]
spec.json 예:
{
  "name": "bridge", "image": "img/ch1_bridge.png",
  "layers": [
    {"id": "kosoe", "boxes": [[785,215,1000,507],[1000,275,1255,475]]},
    {"id": "plank", "boxes": [[699,505,1012,574]], "recolor": [[699,505,1012,516,[244,97,16]]]},
    {"id": "arrow", "boxes": [[425,295,1222,412]], "color": "orange", "exclude": [[640,355,722,440]]}
  ]
}
- boxes   : 이 상자들(합집합) 안의 잉크 = 레이어. 상자 안에 다른 요소가 섞이지 않게 잡는다
- exclude : 상자에서 뺄 영역(배경에 남김)
- color   : orange|red|blue — 다른 선과 겹친 화살표·라벨을 색으로만 골라낼 때
- recolor : [x0,y0,x1,y1,[r,g,b]] 레이어 안의 어두운 잉크를 다른 색으로 (예: 판자 위에 남은 발 자국 → 판자색)
- 상자 좌표는 원본 이미지 픽셀. 격자를 씌운 이미지로 확인하며 잡는다
결과: <out>/<name>_bg.png, <out>/<name>_<id>.png, <out>/<name>.out.json
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

COLORS = {
    'orange': lambda r, g, b: (r > 190) & (g > 60) & (g < 175) & (b < 120) & (r - b > 110),
    'red': lambda r, g, b: (r > 170) & (g < 110) & (b < 110) & (r - g > 90),
    'blue': lambda r, g, b: (b > 140) & (r < 130) & (b - r > 60),
}


def paper_mask(a, floor=228):
    lo, hi = a.min(axis=2), a.max(axis=2)
    return (lo >= floor) & (hi - lo <= 16)


def select(shape, boxes, exclude):
    sel = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        sel[y0:y1, x0:x1] = True
    for x0, y0, x1, y1 in exclude:
        sel[y0:y1, x0:x1] = False
    return sel


def outside_white(crop):
    """잘라 낸 영역 테두리와 이어진 흰 바탕 = 투명. 닫힌 흰 면(눈, 판자 속)은 불투명 유지."""
    paper = paper_mask(crop)
    h, w = paper.shape
    m = Image.new('L', (w + 2, h + 2), 255)
    m.paste(Image.fromarray(np.where(paper, 255, 0).astype('uint8')), (1, 1))
    ImageDraw.floodfill(m, (0, 0), 128)
    return np.asarray(m)[1:-1, 1:-1] == 128


def bbox(mask):
    ys, xs = np.where(mask)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def cut_ink(a, sel):
    x0, y0, x1, y1 = bbox(sel)
    crop = a[y0:y1, x0:x1]
    alpha = sel[y0:y1, x0:x1] & ~outside_white(crop)
    erase = np.zeros(sel.shape, bool)
    erase[y0:y1, x0:x1] = alpha
    # 외곽선의 반투명 픽셀까지 지우도록 넓히고, 선택 영역 안의 옅은 픽셀도 지운다(배경 잔상 방지)
    grown = np.asarray(Image.fromarray((erase * 255).astype('uint8')).filter(ImageFilter.MaxFilter(7))) > 0
    erase = (grown & sel) | (sel & (a.min(axis=2) >= 170))
    return crop, alpha, (x0, y0), erase


def cut_color(a, sel, color):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    core = COLORS[color](r, g, b) & sel
    grown = np.asarray(Image.fromarray((core * 255).astype('uint8')).filter(ImageFilter.MaxFilter(5))) > 0
    m = (grown & sel & ~paper_mask(a, 236) & ~(a.max(axis=2) < 110)) | core   # 반투명 테두리 포함, 검은 선 제외
    x0, y0, x1, y1 = bbox(m)
    return a[y0:y1, x0:x1], m[y0:y1, x0:x1], (x0, y0), m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--out', default='layer')
    args = ap.parse_args()
    spec = json.load(open(args.spec, encoding='utf-8'))
    os.makedirs(args.out, exist_ok=True)
    img = Image.open(spec['image']).convert('RGB')
    a = np.asarray(img).astype(np.int16)
    bg = np.asarray(img).copy()
    result = {'image': spec['image'], 'size': img.size, 'layers': []}
    for L in spec['layers']:
        sel = select(a.shape[:2], L['boxes'], L.get('exclude', []))
        if L.get('color'):
            crop, alpha, origin, erase = cut_color(a, sel, L['color'])
        else:
            crop, alpha, origin, erase = cut_ink(a, sel)
        rgba = np.dstack([crop.astype('uint8'), (alpha * 255).astype('uint8')])
        for x0, y0, x1, y1, rgb in L.get('recolor', []):
            sub = rgba[y0 - origin[1]:y1 - origin[1], x0 - origin[0]:x1 - origin[0]]
            dark = (sub[..., :3].max(axis=2) < 90) & (sub[..., 3] > 0)
            sub[dark, :3] = rgb
        path = os.path.join(args.out, f"{spec['name']}_{L['id']}.png")
        Image.fromarray(rgba, 'RGBA').save(path)
        bg[erase] = 255
        result['layers'].append({'id': L['id'], 'path': path, 'x': int(origin[0]), 'y': int(origin[1]),
                                 'w': int(rgba.shape[1]), 'h': int(rgba.shape[0])})
    result['bg'] = os.path.join(args.out, f"{spec['name']}_bg.png")
    Image.fromarray(bg).save(result['bg'])

    # 검증: 배경 + 레이어 재합성이 원본과 같은지 (recolor 한 픽셀만 달라야 정상)
    comp = Image.open(result['bg']).convert('RGBA')
    for L in result['layers']:
        comp.alpha_composite(Image.open(L['path']), (L['x'], L['y']))
    diff = np.abs(np.asarray(comp.convert('RGB')).astype(int) - np.asarray(img).astype(int)).max(axis=2)
    result['recomposite_diff_px'] = int((diff > 40).sum())
    out_json = os.path.join(args.out, f"{spec['name']}.out.json")
    json.dump(result, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{spec['name']}: {len(result['layers'])} layers, recomposite diff {result['recomposite_diff_px']} px -> {out_json}")


if __name__ == '__main__':
    main()
