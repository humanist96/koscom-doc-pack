#!/usr/bin/env python3
"""
koscom-hwp-report - 문서 유형 템플릿(프리셋) 도구

templates/presets/<id>/preset.md 로 정의한 문서 유형 템플릿을 다룬다.

- index : preset.md 앞머리를 모아 templates/presets/presets_index.json을 만든다(--check는 최신 여부만 확인)
- check : report.json이 프리셋의 보고 형식·구성·표 위치를 따르는지 확인한다
- test  : 모든 프리셋의 example.json을 렌더링하고 check까지 돌린다(회귀 확인)

출력 형식은 렌더러와 같다. 고칠 점은 `WARN …`, 참고 사항은 `INFO …`, 마지막 줄은 `OK …`.
오류(알 수 없는 프리셋, JSON 문법 오류 등)는 `ERROR …`를 찍고 종료 코드 1을 돌려준다.

Usage:
    python scripts/presets.py index [--check]
    python scripts/presets.py check <report.json> [--preset ID]
    python scripts/presets.py test [--only ID ...] [--out DIR]

Examples:
    python scripts/presets.py index
    python scripts/presets.py check 결과/report.json
    python scripts/presets.py test --out %TEMP%/preset_test

Dependencies:
    None (only uses standard library; `test` needs java on PATH)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parents[1]
PRESETS_DIR = SKILL_DIR / "templates" / "presets"
INDEX_PATH = PRESETS_DIR / "presets_index.json"
LIST_KEYS = ("outline", "table_in", "keywords")
REQUIRED_KEYS = ("id", "name", "base", "summary", "outline", "keywords")
INDEX_KEYS = ("name", "base", "summary", "pages", "heading_style", "cover", "outline", "table_in", "keywords")
BASES = ("summary", "detail")


def utf8_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))


class PresetError(RuntimeError):
    """프리셋 정의나 입력이 잘못돼 계속할 수 없을 때."""


# --------------------------------------------------------------------------- #
# preset.md
# --------------------------------------------------------------------------- #

def parse_frontmatter(path: Path) -> dict:
    """preset.md 앞머리를 읽는다. `키: 값`과 한 줄 목록 `키: [a, b]`만 쓴다(PyYAML 불필요)."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.S)
    if not match:
        raise PresetError(f"{path}: 앞머리(---) 없음")
    data: dict = {}
    for raw in match.group(1).splitlines():
        line = raw.split(" #", 1)[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise PresetError(f"{path}: 읽을 수 없는 줄: {raw}")
        key, val = (s.strip() for s in line.split(":", 1))
        if val.startswith("[") and val.endswith("]"):
            data[key] = [v.strip() for v in val[1:-1].split(",") if v.strip()]
        else:
            data[key] = val.strip('"').strip("'")
    for key in LIST_KEYS:
        if isinstance(data.get(key), str):
            raise PresetError(f"{path}: {key}는 [a, b] 목록이어야 함")
    missing = [k for k in REQUIRED_KEYS if not data.get(k)]
    if missing:
        raise PresetError(f"{path}: 필수 항목 없음: {', '.join(missing)}")
    if data["base"] not in BASES:
        raise PresetError(f"{path}: base는 {'/'.join(BASES)} 중 하나여야 함")
    if data["id"] != path.parent.name:
        raise PresetError(f"{path}: id '{data['id']}'가 폴더 이름과 다름")
    return data


def load_presets() -> dict[str, dict]:
    presets = {}
    for spec in sorted(PRESETS_DIR.glob("*/preset.md")):
        data = parse_frontmatter(spec)
        presets[data["id"]] = data
    return presets


def build_index(presets: dict[str, dict]) -> str:
    index = {pid: {k: p[k] for k in INDEX_KEYS if k in p} for pid, p in presets.items()}
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n"


def cmd_index(check: bool) -> int:
    fresh = build_index(load_presets())
    current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.is_file() else ""
    if check:
        if current.replace("\r\n", "\n") != fresh:
            print(f"WARN presets_index.json이 preset.md와 다름 — python scripts/presets.py index 로 다시 만들 것")
            return 1
        print("OK presets_index.json 최신")
        return 0
    INDEX_PATH.write_text(fresh, encoding="utf-8", newline="\n")
    print(f"OK {INDEX_PATH.relative_to(SKILL_DIR).as_posix()} ({len(json.loads(fresh))}종)")
    return 0


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #

def norm(text: str) -> str:
    return re.sub(r"[\s·ㆍ.,()]", "", text)


def headings_of(report: dict) -> list[tuple[str, list]]:
    """(제목, 그 아래 항목 묶음 목록). 요약보고는 대제목, 상세보고는 장."""
    if report.get("type", "summary") == "detail":
        out = []
        for ch in report.get("chapters", []):
            groups = [s.get("items", []) for s in ch.get("sections", [])]
            for part in ch.get("parts", []):
                groups += [s.get("items", []) for s in part.get("sections", [])]
            out.append((ch.get("title", ""), groups))
        return out
    return [(s.get("heading", ""), [s.get("items", [])]) for s in report.get("sections", [])]


def has_table(items: list) -> bool:
    for item in items:
        if item.get("type") == "table":
            return True
        if item.get("type") == "box" and has_table(item.get("items", [])):
            return True
        if has_table(item.get("children", [])):
            return True
    return False


def find_heading(want: str, heads: list[tuple[str, list]]) -> Optional[int]:
    w = norm(want)
    for i, (title, _) in enumerate(heads):
        t = norm(title)
        if t == w or (w and (w in t or t in w)):
            return i
    return None


def check_report(report: dict, preset: dict) -> list[str]:
    lines = []
    rtype = report.get("type", "summary")
    if rtype != preset["base"]:
        lines.append(f"WARN [형식] 프리셋 '{preset['id']}'는 {preset['base']}인데 report.json은 {rtype}")

    heads = headings_of(report)
    found = []
    for want in preset["outline"]:
        idx = find_heading(want, heads)
        if idx is None:
            lines.append(f"WARN [구성] '{want}' {'장' if rtype == 'detail' else '대제목'} 없음")
        else:
            found.append((want, idx))
    order = [idx for _, idx in found]
    if order != sorted(order):
        lines.append("WARN [구성] 순서가 프리셋과 다름. 지금: " + " → ".join(heads[i][0] for i in sorted(order))
                     + " / 프리셋: " + " → ".join(want for want, _ in found))

    for want in preset.get("table_in", []):
        idx = find_heading(want, heads)
        if idx is not None and not any(has_table(g) for g in heads[idx][1]):
            lines.append(f"WARN [표] '{heads[idx][0]}'에 표가 없음(프리셋은 표로 정리)")

    holders = [k for k, v in (report.get("approval") or {}).items() if "○" in str(v)]
    if holders:
        lines.append(f"INFO 결재라인 자리표시 남음({', '.join(holders)}) — 전달할 때 채우라고 알릴 것")
    for key in ("dept", "hq"):
        if "○" in str(report.get(key, "")):
            lines.append(f"INFO {key} 자리표시 남음 — 전달할 때 채우라고 알릴 것")
    return lines


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise PresetError(f"{path}: JSON 문법 오류 — {exc}") from exc


def cmd_check(report_path: Path, preset_id: Optional[str]) -> int:
    report = load_json(report_path)
    pid = preset_id or report.get("preset")
    if not pid:
        raise PresetError("프리셋을 알 수 없음 — report.json에 \"preset\"을 넣거나 --preset을 줄 것")
    presets = load_presets()
    if pid not in presets:
        raise PresetError(f"알 수 없는 프리셋 '{pid}' (있는 것: {', '.join(presets)})")
    lines = check_report(report, presets[pid])
    for line in lines:
        print(line)
    warns = sum(1 for ln in lines if ln.startswith("WARN"))
    print(f"OK {pid} 구성 확인" + (f" (경고 {warns}건)" if warns else ""))
    return 0


# --------------------------------------------------------------------------- #
# test
# --------------------------------------------------------------------------- #

def render(src: Path, out: Path) -> list[str]:
    classpath = os.pathsep.join(
        str(p) for p in (SKILL_DIR / "lib" / "hwplib-1.1.9.jar", SKILL_DIR / "scripts" / "koscom-hwp.jar"))
    proc = subprocess.run(
        ["java", "-Dfile.encoding=UTF-8", "-cp", classpath, "Renderer", str(src), str(out),
         str(SKILL_DIR / "templates")],
        cwd=SKILL_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if proc.returncode != 0 or not lines or not lines[-1].startswith("OK"):
        detail = lines[-1] if lines else (proc.stderr.strip().splitlines() or ["출력 없음"])[-1]
        raise PresetError(f"{src.parent.name}: 렌더링 실패 — {detail}")
    return lines[:-1]


def cmd_test(only: Optional[list[str]], out_dir: Optional[Path]) -> int:
    presets = load_presets()
    ids = only or list(presets)
    unknown = [i for i in ids if i not in presets]
    if unknown:
        raise PresetError(f"알 수 없는 프리셋: {', '.join(unknown)}")
    total_warn = 0
    with tempfile.TemporaryDirectory(prefix="preset-test-") as tmp:
        target = out_dir or Path(tmp)
        target.mkdir(parents=True, exist_ok=True)
        for pid in ids:
            example = PRESETS_DIR / pid / "example.json"
            if not example.is_file():
                print(f"WARN [{pid}] example.json 없음")
                total_warn += 1
                continue
            report = load_json(example)
            lines = [ln for ln in render(example, target / f"{pid}.hwp") if not ln.startswith("WARN 목차 쪽번호")]
            lines += [ln for ln in check_report(report, presets[pid]) if ln.startswith("WARN")]
            if report.get("preset") != pid:
                lines.append(f"WARN example.json의 \"preset\"이 '{pid}'가 아님")
            warns = [ln for ln in lines if ln.startswith("WARN")]
            total_warn += len(warns)
            print(f"{'OK  ' if not warns else 'WARN'} {pid}")
            for ln in warns:
                print(f"     {ln}")
    print(f"OK {len(ids)}종 렌더링" + (f" (경고 {total_warn}건)" if total_warn else ", 경고 없음"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="코스콤 한글 보고서 문서 유형 템플릿 도구.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_index = sub.add_parser("index", help="presets_index.json 만들기")
    p_index.add_argument("--check", action="store_true", help="최신인지만 확인")
    p_check = sub.add_parser("check", help="report.json이 프리셋 구성을 따르는지 확인")
    p_check.add_argument("report", type=Path)
    p_check.add_argument("--preset", help="프리셋 id (기본: report.json의 \"preset\")")
    p_test = sub.add_parser("test", help="모든 예시를 렌더링하고 확인")
    p_test.add_argument("--only", nargs="+", metavar="ID")
    p_test.add_argument("--out", type=Path, help="렌더링한 .hwp를 남길 폴더")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "index":
            return cmd_index(args.check)
        if args.cmd == "check":
            return cmd_check(args.report, args.preset)
        return cmd_test(args.only, args.out)
    except PresetError as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
