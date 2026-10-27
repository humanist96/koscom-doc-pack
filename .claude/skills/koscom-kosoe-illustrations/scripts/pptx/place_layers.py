"""layers.py로 분리한 레이어를 슬라이드에 겹쳐 놓는다.

- 대상 그림(그룹 안이어도 됨)의 이미지를 배경 레이어로 교체 → 기존 등장 애니메이션은 그대로 유지
- 움직일 레이어를 원본 좌표·같은 배율로 그 위에 추가. 이름: 'Kosoe Layer <name>_<id>'
- 'kosoe'가 들어간 레이어는 맨 위에 둔다(다른 레이어에 가려지지 않게)

사용: python place_layers.py in.pptx out.pptx <slide>:<layer/name.out.json>[:<그림 이름 접두어>] ...
그림 이름 접두어 기본값: 'Kosoe Illustration' (insert_images.py의 replace.name)
"""
import io
import json
import sys

import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'


def whiten(im, floor=228):
    a = np.asarray(im.convert('RGB')).astype(np.int16)
    lo, hi = a.min(axis=2), a.max(axis=2)
    a[(lo >= floor) & (hi - lo <= 14)] = 255
    return Image.fromarray(a.astype('uint8'))


def png(im):
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    buf.seek(0)
    return buf


def find(shapes, prefix, group=None):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            hit = find(sh.shapes, prefix, sh)
            if hit:
                return hit
        elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE and sh.name.startswith(prefix):
            return sh, group
    return None


def abs_rect(pic, group):
    """그룹 안 그림이면 그룹 좌표 변환을 적용한 슬라이드 절대 좌표(EMU)."""
    if group is None:
        return pic.left, pic.top, pic.width, pic.height
    x = group._element.grpSpPr.find(A + 'xfrm')
    off, ext, choff, chext = (x.find(A + t) for t in ('off', 'ext', 'chOff', 'chExt'))
    sx = int(ext.get('cx')) / int(chext.get('cx'))
    sy = int(ext.get('cy')) / int(chext.get('cy'))
    return (int(off.get('x')) + (pic.left - int(choff.get('x'))) * sx,
            int(off.get('y')) + (pic.top - int(choff.get('y'))) * sy,
            pic.width * sx, pic.height * sy)


def main(src, out, jobs):
    prs = Presentation(src)
    for job in jobs:
        parts = job.split(':')
        n, spec_path = int(parts[0]), parts[1]
        prefix = parts[2] if len(parts) > 2 else 'Kosoe Illustration'
        spec = json.load(open(spec_path, encoding='utf-8'))
        name = spec['layers'][0]['path'].replace('\\', '/').split('/')[-1].rsplit('_', 1)[0]
        slide = prs.slides[n - 1]
        hit = find(slide.shapes, prefix)
        assert hit, f"slide {n}: picture '{prefix}*' not found"
        pic, group = hit
        x, y, w, h = abs_rect(pic, group)
        _, rId = slide.part.get_or_add_image_part(png(whiten(Image.open(spec['bg']))))
        pic._element.blipFill.blip.rEmbed = rId
        W, H = spec['size']
        sx, sy = w / W, h / H
        for L in sorted(spec['layers'], key=lambda L: 'kosoe' in L['id']):
            p = slide.shapes.add_picture(png(Image.open(L['path'])), Emu(int(x + L['x'] * sx)), Emu(int(y + L['y'] * sy)),
                                         Emu(int(L['w'] * sx)), Emu(int(L['h'] * sy)))
            p.name = f"Kosoe Layer {name}_{L['id']}"
            p._element.nvPicPr.cNvPr.set('descr', f"애니메이션 레이어: {name} {L['id']}")
            print(f'slide {n}: {p.name}')
        # 이동 경로 계산용: 원본 1px = 슬라이드 폭의 몇 배인지
        print(f'slide {n}: path unit = {sx / prs.slide_width:.6f} per source px (dx_px * unit = 경로 x값)')
    prs.save(out)
    print('saved', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
