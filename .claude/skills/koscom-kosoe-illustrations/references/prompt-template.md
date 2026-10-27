# 이미지 생성 프롬프트 템플릿

한 장씩 생성한다. 아래 템플릿의 `{...}`를 본문에 맞게 채운다. 이미지 모델이 영어 지시를 더 잘 따르므로 지시는 영어로, **그림 안에 들어갈 라벨만 한국어**로 쓴다.

항상 `assets/kosoe-character-sheet.png`를 레퍼런스 이미지로 첨부한다.

```text
Generate one standalone 16:9 horizontal Korean article illustration.

Visual DNA:
Pure white background. Minimalist dark-charcoal hand-drawn line art. Slightly wobbly pen lines. Lots of empty white space. Sparse orange/blue/red handwritten Korean annotations. Clean, absurd product-sketch feeling. Objects are line-only (white inside), no gray shading on objects. No gradients, no shadows, no paper texture, no complex background, no commercial vector style, no PPT infographic look, no cute mascot poster, no children's illustration, no realistic UI, no company logos.

Recurring character required — 코쇠 (Kosoe):
Keep the character design EXACTLY as in the attached character sheet: a small solid charcoal-gray (#5A5555) rounded-square block body like a worn keycap, one bright orange (#E96717) chevron ">" crest on top of the head always pointing right, two white dot eyes, tiny flat-line mouth, very thin black stick arms and legs. Deadpan, serious, diligent, slightly bizarre — not cute. Use the attached image ONLY for character design consistency; do not copy its layout, poses or labels.
코쇠 must perform the core conceptual action, not decorate the scene.

Color use:
Dark charcoal for line art. Orange (#E96717) for the main flow, path and arrows. Blue (#4368F2) only for secondary notes or system state. Red only for one key warning or problem, if needed.

Constraints:
One image explains only one core structure. Main subject around 40%-60% of the canvas, at least 35% blank white space. At most 5 short handwritten Korean labels (2-8 characters each), spelled exactly as given. No title in the top-left corner. Do not write the structure type on the image. Clear but not instructional, interesting but not childish, strange but clean.

Theme: {삽화 주제 — 한 줄 의미}
Structure type: {workflow / system detail / before-after / state change / concept metaphor / layers / map route / short comic}
Composition: {코쇠가 어디서 무엇을 하는지, 주요 사물, 흐름 방향을 구체적으로 영어로}
Korean labels: "{라벨1}" ({위치/색}), "{라벨2}", "{라벨3}", "{라벨4}"
```

## 작성 팁

- **Composition이 품질의 80%** 다. "코쇠가 ○○을 하고 있다"를 동사로 분명히 쓴다.
- 라벨은 따옴표로 정확히 적고 개수를 줄일수록 한글 오탈자가 줄어든다.
- 색 지시는 라벨 옆에 괄호로: `"동시에" (orange)`, `"정상" (blue)`, `"장애!" (red)`.
- 코쇠가 여러 명이면 "two Kosoe characters"처럼 수를 명시한다.
- 숫자·시각(09:00, 0.001초)은 짧을수록 정확하게 나온다.

## 편집 프롬프트

왼쪽 위 제목 지우기:

```text
Edit the provided image. Remove only the handwritten title "{지울 글자}" and its underline from the top-left corner. Fill that area with the same clean white background. Preserve everything else exactly: characters, labels, paths, line style, composition, aspect ratio and image quality. Do not add any new text or objects.
```

한글 라벨 고치기:

```text
Edit the provided image. Replace only the handwritten Korean label "{틀린 글자}" with "{맞는 글자}" in the same handwriting style, color, size and position. Preserve everything else exactly.
```

코쇠를 동작의 주체로:

```text
Regenerate this illustration with the same core meaning and simple layout, but make 코쇠 more central to the conceptual action. 코쇠 should be doing the strange work that explains the idea, not standing beside it. Keep 코쇠's design identical to the attached character sheet. Keep it clean, sparse, hand-drawn and not cute.
```

코쇠 디자인 복구:

```text
Edit the provided image. Redraw only the character so it exactly matches the attached character sheet: solid charcoal-gray (#5A5555) rounded-square keycap body, one orange (#E96717) chevron ">" crest on top pointing right, white dot eyes, thin black stick limbs. Keep its pose, position and everything else in the image unchanged.
```
