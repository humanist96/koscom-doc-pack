"""레이어 상자 좌표를 잡기 위해 이미지에 격자와 눈금 숫자를 씌운다.

사용: python grid.py img/ch1.png [-o out.png] [--zoom x0,y0,x1,y1]
- 기본: 50px 격자, 100px마다 숫자
- --zoom: 그 영역만 2배 확대해 10px 격자(20px마다 숫자) — 세밀한 경계 확인용
"""
import argparse

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('-o', '--out')
    ap.add_argument('--zoom')
    a = ap.parse_args()
    im = Image.open(a.image).convert('RGB')
    ox = oy = 0
    step, label, k = 50, 100, 1
    if a.zoom:
        x0, y0, x1, y1 = map(int, a.zoom.split(','))
        im = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST)
        ox, oy, step, label, k = x0, y0, 10, 20, 2
    d = ImageDraw.Draw(im)
    for v in range(-(-ox // step) * step, ox + im.width // k + 1, step):
        X = (v - ox) * k
        major = v % label == 0
        d.line([(X, 0), (X, im.height)], fill=(255, 0, 0) if major else (255, 190, 190))
        if major:
            d.text((X + 2, 2), str(v), fill=(255, 0, 0))
    for v in range(-(-oy // step) * step, oy + im.height // k + 1, step):
        Y = (v - oy) * k
        major = v % label == 0
        d.line([(0, Y), (im.width, Y)], fill=(0, 150, 0) if major else (190, 230, 190))
        if major:
            d.text((2, Y + 2), str(v), fill=(0, 150, 0))
    out = a.out or a.image.rsplit('.', 1)[0] + '_grid.png'
    im.save(out)
    print(out)


if __name__ == '__main__':
    main()
