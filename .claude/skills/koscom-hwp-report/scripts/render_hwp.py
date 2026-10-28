#!/usr/bin/env python3
"""
koscom-hwp-report - 렌더링(Python 진입점)

report.json을 코스콤 서식 .hwp로 만든다. scripts/render.ps1과 같은 렌더러를 부르므로 결과가 같다.
PowerShell이 없거나(맥·리눅스, Codex 등) Python에서 바로 부르고 싶을 때 쓴다.
"preset"이 든 report.json이면 렌더링 뒤 문서 유형 템플릿 구성 확인(presets.py check)까지 한다.

출력은 렌더러 그대로다: 고칠 점은 `WARN …`, 마지막 줄은 `OK <경로>`, 실패하면 `ERROR …`와 종료 코드 1.
그림(figure)의 상대 경로는 현재 폴더 기준이다.

Usage:
    python scripts/render_hwp.py <report.json> <out.hwp> [--no-check]

Examples:
    python scripts/render_hwp.py report.json 결과.hwp
    python scripts/render_hwp.py references/examples/summary_sample.json %TEMP%/test.hwp

Dependencies:
    None (only uses standard library; needs java on PATH)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parents[1]


def utf8_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            setattr(sys, name, io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))


def render(report: Path, out: Path) -> int:
    classpath = os.pathsep.join(
        str(p) for p in (SKILL_DIR / "lib" / "hwplib-1.1.9.jar", SKILL_DIR / "scripts" / "koscom-hwp.jar"))
    try:
        proc = subprocess.run(
            ["java", "-Dfile.encoding=UTF-8", "-cp", classpath, "Renderer", str(report), str(out),
             str(SKILL_DIR / "templates")],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print("ERROR java가 PATH에 없음 — Java 8 이상을 설치할 것")
        return 1
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0 and proc.stderr.strip():
        print(proc.stderr.strip().splitlines()[-1], file=sys.stderr)
    return proc.returncode


def main(argv: Optional[list[str]] = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="report.json → 코스콤 서식 .hwp")
    parser.add_argument("report", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--no-check", action="store_true", help="프리셋 구성 확인을 건너뜀")
    args = parser.parse_args(argv)

    code = render(args.report, args.out)
    if code != 0 or args.no_check:
        return code
    try:
        preset = json.loads(args.report.read_text(encoding="utf-8-sig")).get("preset")
    except (OSError, json.JSONDecodeError):
        return code
    if preset:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import presets  # noqa: E402

        try:
            presets.cmd_check(args.report, None)
        except presets.PresetError as exc:
            print(f"ERROR {exc}")
            return 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
