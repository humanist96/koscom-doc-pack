# PPT 덱에 코쇠 삽화 넣기

기존 .pptx 덱에 코쇠 일러스트를 채우고, 장표별 스팟 그림과 애니메이션까지 붙이는 절차다.
`scripts/pptx/`의 도구를 쓴다. 렌더링·애니메이션·동영상 검수는 **Windows + PowerPoint**가 필요하다
(python-pptx, Pillow, numpy 필수 / ffmpeg는 동영상 프레임 검수용).

원칙: **원본 덱은 덮어쓰지 않는다.** 결과는 항상 새 이름으로 저장하고, 작업 중 사용자가 파일을 고쳤는지
확인한 뒤(도형 위치·텍스트 비교) 가장 최신 파일 위에 다시 적용한다.

## 1. 덱 파악

```bash
powershell -ExecutionPolicy Bypass -File scripts/pptx/render.ps1 -Pptx deck.pptx -Out renders
python scripts/pptx/inspect_deck.py deck.pptx renders
python scripts/pptx/theme_fonts.py deck.pptx
```

- 렌더 PNG를 몇 장씩 이어 붙여(접촉 시트) 덱 전체 디자인을 먼저 본다.
- `inspect_deck.py`는 도형 이름·위치·텍스트와, 흰 배경 장표의 **제목 오른쪽 상단 빈 띠** 폭을 알려 준다.
- "일러스트 대기"처럼 비워 둔 그림 자리(예: 그룹 안 `Image 9`)를 찾는다 → **메인 일러스트** 자리.
- 빈 띠 폭 2인치 이상인 흰 배경 장표 → **스팟 일러스트** 후보.
- 건너뛸 장표: 표지, 챕터 구분, 검은/진한 배경(흰 손그림이 스티커처럼 뜬다), 이미 차트·범례가 상단에 있는 장표.

## 2. 기획

장표마다 그 장의 **제목 한 줄 메시지**를 한 컷 은유로 바꾼다. 메인은 장 도입(“한 장으로 보기”)의 핵심 구조,
스팟은 코쇠 + 사물 1~2개의 단순한 장면. 같은 덱 안에서 은유가 겹치지 않게 한다(관문을 두 번 쓰면 하나는 밸브로).

## 3. 프롬프트

- 메인: `prompt-template.md` 그대로.
- 스팟: 템플릿 첫 줄을 아래로 바꾸고 규칙을 덧붙인다.

```text
Generate one small SPOT illustration that will be placed as a small thumbnail (about 3 x 1.5 inches) in the top-right corner of a presentation slide.
...(템플릿 공통부)...
Spot illustration rules (override the above where they conflict):
Arrange the whole drawing inside a WIDE horizontal band (about 2:1) in the vertical middle of the canvas; keep the top 22% and bottom 22% of the canvas completely empty white.
Very few elements: 코쇠 plus at most two simple objects. Bold, simple, slightly thicker pen lines so it stays readable at thumbnail size. No small details, no background scenery, no ground clutter.
No text at all unless a label is explicitly given below.
```

스팟에는 글자를 거의 넣지 않는다(작아서 안 읽히고 오탈자 위험만 커진다). 꼭 필요하면 숫자 하나(예: "95%").

## 4. 생성 (병렬)

```bash
ls prompts | sed 's/\.txt$//' | xargs -P 4 -I{} bash scripts/gen_image.sh prompts/{}.txt img/{}.png assets/kosoe-character-sheet.png
```

24장 기준 약 10~15분. 4개 넘게 동시에 돌리지 않는다.

## 5. 이미지 검수

`qa-checklist.md` 기준에 더해:

- **한글 오탈자**: 편집 프롬프트로 두 번 고쳐도 같은 오타가 나오면(예: 용어집 → 용여집) 모델이 그 글자를 못 쓰는 것이다.
  `grid.py --zoom`으로 글자를 확대해 획 단위로 직접 고친다(예: ㅕ의 두 획을 지우고 ㅓ 한 획을 같은 색·굵기로).
- **투명 배경**: 가끔 RGBA로 나와 검게 보인다. `gen_image.sh`와 `insert_images.py`가 흰 배경으로 합친다.

## 6. 삽입

`plan.json`(형식은 `insert_images.py` 머리말)을 쓰고:

```bash
python scripts/pptx/insert_images.py deck.pptx out.pptx plan.json
```

- 메인: 기존 그림의 위치·크기·애니메이션을 그대로 두고 이미지만 교체(자리 비율에 맞춰 가운데 자름).
- 스팟: 여백을 잘라 띠(기본 y 0.45~2.05in) 안에 오른쪽 정렬. 부제 아래 구분선과 0.2in 이상 띄운다.
- 생성 이미지 바탕은 아주 옅은 회색이라 그대로 넣으면 **흐린 사각 테두리**가 보인다 → 스크립트가 순백으로 맞춘다.
- 대체 텍스트(`alt`)를 그림마다 넣는다.

다시 렌더링해 겹침·여백·테두리를 확인한다.

## 7. 애니메이션

### ① 기본 등장 (전 장표)

클릭 없이 자동(after previous). 스팟은 `fade` 0.6s(지연 0.2s), 메인은 `wipe` 왼쪽에서 1.0s.
도형 이름은 그룹이면 그룹 이름을 쓴다.

### ③ 레이어 분리 + 이동 경로 (메인만)

원본 그림을 배경과 움직일 요소로 잘라, 마지막 장면이 원본과 **같아지도록** 겹쳐 놓고 순서대로 등장·이동시킨다.

1. 좌표 잡기: `python scripts/pptx/grid.py img/ch1.png` (세밀한 곳은 `--zoom x0,y0,x1,y1`)
2. 분리 명세(`layers.py` 머리말 형식) 작성 → `python scripts/pptx/layers.py spec.json --out layer`
   - 출력의 `recomposite diff`가 0(또는 recolor한 픽셀 수)이어야 한다.
   - 배경(`*_bg.png`)과 레이어를 나란히 보고 반쪽 잘린 요소·잔상이 없는지 확인.
3. 배치: `python scripts/pptx/place_layers.py out.pptx layered.pptx 4:layer/bridge.out.json ...`
   - 출력되는 `path unit`(원본 1px = 슬라이드 폭 비율)로 이동 거리를 계산한다.
4. 타임라인 JSON(`animate.ps1` 머리말 형식) 작성 → `animate.ps1` 실행.
5. 검수: `export_video.ps1 -Slides "4"` → `ffmpeg -i v.mp4 -vf fps=2 f_%02d.png` → 프레임을 이어 붙여 본다.

연출 패턴:

| 패턴 | 타임라인 |
|---|---|
| 코쇠가 걸어 들어옴 | `fade`(after, 0.3) + `path`(with, 1.6~2.4s, linear, 시작점 음수) |
| 코쇠가 지나가며 무언가를 놓음 | 놓이는 요소 `wipe`(with, delay = 코쇠가 도착하기 직전) |
| 무리가 날아옴 | 무리 레이어 `fade` + `path`(with, 부드럽게) |
| 결과가 차례로 펼쳐짐 | 요소별 `wipe` 왼쪽에서, after |
| 강조 | 마지막에 `teeter`(after, 0.5) |

함정:

- **상자 안에 다른 선이 섞이면 함께 움직인다.** 벽·바닥선 위를 지나는 요소는 상자를 그 선 위에서 끊거나,
  주황·빨강·파랑 요소는 `color`로 색만 골라낸다(화살표·라벨이 검은 선과 겹칠 때).
- **잔상**: 외곽선 반투명 픽셀이 배경에 남으면 흐린 실루엣이 보인다 → `layers.py`가 지우는 범위를 넓혀 처리.
- **다리 사이로 지나는 선**(테이블 모서리 등)은 코쇠 상자에서 그 선 높이의 얇은 띠만 빼 배경 쪽에 남긴다.
- **코쇠 레이어는 맨 위**(place_layers.py가 자동 처리). 출발 위치가 사람·사물과 겹치지 않게 시작점을 잡는다.
- 코쇠는 통째로 미끄러지듯 이동한다(다리는 안 움직인다). 걷는 느낌은 linear 이동 + 도착 후 `teeter`로 보완.
- 새 효과는 기존 순서 뒤에 붙는다. 메인 그림(배경)의 기존 등장 효과가 먼저 재생된다.
- `export_video.ps1`의 `-Slides`는 문자열 `"4,10"`로 넘긴다.

## 8. 폰트

`theme_fonts.py`로 major/minor의 latin **과 ea** 를 함께 본다. 한글은 ea 폰트로 그려지므로,
ea가 설치되지 않은 폰트(예: Pretendard)면 한글만 대체 폰트로 바뀌고 글자 폭이 달라진다.

```bash
python scripts/pptx/theme_fonts.py in.pptx out.pptx --major "KoPub돋움체 Bold" --minor "KoPub돋움체 Medium"
```

바꾼 뒤 전 장표를 다시 렌더링해 넘침을 확인한다. 받는 사람 PC에도 같은 폰트가 있어야 한다고 안내한다.

## 9. 마무리

- `validate.py`가 있으면 원본 대비 구조 검증.
- 전달: 저장 경로, 메인·스팟 장수와 장표별 용도, 애니메이션 내용, 손으로 고친 곳, 손대지 않은 장표와 이유.
- PDF로 내보내면 애니메이션은 사라진다는 점을 알린다.
