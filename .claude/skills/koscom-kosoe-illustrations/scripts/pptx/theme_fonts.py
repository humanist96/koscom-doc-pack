"""덱 테마 폰트를 확인하고 바꾼다.

한글은 테마의 동아시아(ea) 폰트로 그려진다. 영문(latin)만 바꾸고 ea가 설치 안 된 폰트로 남아 있으면
한글만 대체 폰트로 보이는 문제가 생긴다 — 이 스크립트로 둘 다 확인한다.

확인: python theme_fonts.py deck.pptx
변경: python theme_fonts.py deck.pptx out.pptx --major "KoPub돋움체 Bold" --minor "KoPub돋움체 Medium" [--scripts latin,ea,cs]
설치 확인(Windows): powershell "Add-Type -AssemblyName System.Drawing; (New-Object System.Drawing.Text.InstalledFontCollection).Families.Name"
"""
import argparse
import re
import zipfile

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def show(path):
    z = zipfile.ZipFile(path)
    for n in sorted(x for x in z.namelist() if re.match(r'ppt/theme/theme\d+\.xml$', x)):
        x = z.read(n).decode('utf-8')
        for kind in ('majorFont', 'minorFont'):
            m = re.search(rf'<a:{kind}>(.*?)</a:{kind}>', x, re.S)
            if m:
                f = dict(re.findall(r'<a:(latin|ea|cs) typeface="([^"]*)"', m.group(1)))
                hang = re.search(r'<a:font script="Hang" typeface="([^"]*)"', m.group(1))
                print(f"{n} {kind}: latin={f.get('latin')!r} ea={f.get('ea')!r} cs={f.get('cs')!r}"
                      + (f" Hang={hang.group(1)!r}" if hang else ''))


def change(src, dst, major, minor, scripts):
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if re.match(r'ppt/theme/theme\d+\.xml$', item.filename):
            x = data.decode('utf-8')
            for kind, face in (('majorFont', major), ('minorFont', minor)):
                if not face:
                    continue

                def repl(m, face=face):
                    block = m.group(0)
                    for s in scripts:
                        block = re.sub(rf'<a:{s} typeface="[^"]*"', f'<a:{s} typeface="{face}"', block, count=1)
                    # 한글 스크립트 지정(Hang)이 있으면 함께 맞춘다
                    return re.sub(r'(<a:font script="Hang" typeface=")[^"]*"', rf'\g<1>{face}"', block)
                x = re.sub(rf'<a:{kind}>.*?</a:{kind}>', repl, x, flags=re.S)
            data = x.encode('utf-8')
        zout.writestr(item, data)
    zout.close()
    show(dst)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst', nargs='?')
    ap.add_argument('--major')
    ap.add_argument('--minor')
    ap.add_argument('--scripts', default='latin,ea,cs')
    a = ap.parse_args()
    if a.dst:
        change(a.src, a.dst, a.major, a.minor, a.scripts.split(','))
    else:
        show(a.src)
