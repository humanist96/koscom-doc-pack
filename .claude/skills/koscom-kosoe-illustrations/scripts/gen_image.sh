#!/usr/bin/env bash
# Codex CLI의 image_gen 도구로 이미지 1장을 생성한다 (ChatGPT 로그인 필요: codex login).
# 사용법: gen_image.sh <prompt.txt> <out.png> [reference.png ...]
#   - 레퍼런스 이미지는 여러 장 가능. 코쇠 일관성을 위해 assets/kosoe-character-sheet.png 를 꼭 넘긴다.
#   - 여러 장을 병렬로 돌려도 Codex 세션 ID로 결과를 회수하므로 섞이지 않는다.
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "사용법: $0 <prompt.txt> <out.png> [reference.png ...]" >&2; exit 2
fi
command -v codex >/dev/null || { echo "codex CLI가 없습니다: npm i -g @openai/codex && codex login" >&2; exit 2; }

PROMPT_FILE="$1"; OUT="$2"; shift 2
mkdir -p "$(dirname "$OUT")"
OUT_DIR="$(cd "$(dirname "$OUT")" && pwd)"
OUT_NAME="$(basename "$OUT")"
GEN_ROOT="${CODEX_HOME:-$HOME/.codex}/generated_images"
LOG="$OUT_DIR/.${OUT_NAME%.*}.codex.log"

# 레퍼런스는 절대경로로 넘긴다 (상대경로는 Codex 작업 폴더 기준으로 해석되어 실패함)
abs_path() {
  local p; p="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
  if command -v cygpath >/dev/null; then cygpath -m "$p"; else echo "$p"; fi
}
REF_ARGS=()
for r in "$@"; do
  [ -f "$r" ] || { echo "레퍼런스 이미지가 없습니다: $r" >&2; exit 2; }
  REF_ARGS+=(-i "$(abs_path "$r")")
done

# 프롬프트를 -i 앞에 둬야 한다. 저장은 이 스크립트가 하므로 Codex에는 생성만 시킨다.
codex exec -C "$OUT_DIR" --skip-git-repo-check \
  "Use the image generation tool to generate one image as described below. Use any attached image only as a character design reference. Do not run any shell commands and do not try to save or copy files.

$(cat "$PROMPT_FILE")" "${REF_ARGS[@]}" > "$LOG" 2>&1 < /dev/null || true

SESSION="$(grep -m1 -oE 'session id: [0-9a-f-]+' "$LOG" | awk '{print $3}' || true)"
SRC=""
if [ -n "$SESSION" ] && [ -d "$GEN_ROOT/$SESSION" ]; then
  SRC="$(ls -t "$GEN_ROOT/$SESSION"/*.png 2>/dev/null | head -1 || true)"
fi

if [ -n "$SRC" ] && [ -s "$SRC" ]; then
  cp "$SRC" "$OUT_DIR/$OUT_NAME"
  # 가끔 투명 배경(RGBA)으로 나오면 문서에서 검게 보이므로 흰 배경으로 합친다
  python -c "import sys;from PIL import Image;im=Image.open(sys.argv[1])
if im.mode in ('RGBA','LA','P'):
    im=im.convert('RGBA');bg=Image.new('RGBA',im.size,(255,255,255,255));bg.alpha_composite(im);bg.convert('RGB').save(sys.argv[1])" "$OUT_DIR/$OUT_NAME" 2>/dev/null || true
  rm -f "$LOG"
  echo "OK  $OUT_DIR/$OUT_NAME"
else
  echo "FAIL  $OUT_NAME — 로그 확인: $LOG" >&2; exit 1
fi
