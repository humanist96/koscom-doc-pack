#!/usr/bin/env python3
"""
koscom-doc-pack - 시작 점검(doctor)

PPT·한글·삽화 세 경로가 이 PC에서 돌아갈 준비가 됐는지 한 번에 확인한다.
PPT 쪽은 ppt-master의 preflight 점검 함수를 그대로 다시 쓰고, 한글·삽화 쪽
점검을 더한다. 경로를 멈추게 하는 문제는 FAIL, 결과 확인만 못 하게 되는 문제는
WARN으로 알린다.

Usage:
    python .claude/skills/koscom-doc-pack/scripts/doctor.py [options]

Examples:
    python .claude/skills/koscom-doc-pack/scripts/doctor.py
    python .claude/skills/koscom-doc-pack/scripts/doctor.py --smoke
    python .claude/skills/koscom-doc-pack/scripts/doctor.py --only hwp --smoke

Dependencies:
    None (only uses standard library; PPT checks probe third-party deps by import)
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# scripts/doctor.py: [0]=scripts [1]=koscom-doc-pack [2]=skills [3]=.claude [4]=repo
REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS = REPO_ROOT / ".claude" / "skills"
PPT_SCRIPTS = SKILLS / "ppt-master" / "scripts"
HWP_SKILL = SKILLS / "koscom-hwp-report"
KOSOE_SKILL = SKILLS / "koscom-kosoe-illustrations"

if str(PPT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PPT_SCRIPTS))

from console_encoding import configure_utf8_stdio  # noqa: E402
import preflight  # noqa: E402

HWP_BASES = ("summary_base.hwp", "detail_base.hwp")
HWP_SAMPLES = ("summary_sample.json", "detail_sample.json")
# HWP 5.0은 OLE 복합 문서다. 보호 도구가 암호화한 파일은 이 서명이 없다.
OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
HWP_VIEWER = Path(r"C:\Program Files (x86)\HNC\Office NEO\HOfficeViewer96\Bin\HwpViewer.exe")
SECTIONS = ("ppt", "hwp", "illust")


# --------------------------------------------------------------------------- #
# PPT
# --------------------------------------------------------------------------- #

def check_pptx_default_template() -> list[str]:
    """python-pptx는 새 덱을 자기 패키지의 default.pptx에서 시작한다. 사내 보호 도구가 이
    파일을 .pia로 암호화하면 import는 되지만 PPTX 내보내기가 PackageNotFoundError로 멈춘다."""
    if preflight._module_missing("pptx"):
        return []  # check_core_deps가 이미 알린다.
    import pptx

    default = Path(pptx.__file__).parent / "templates" / "default.pptx"
    if default.is_file():
        return []
    reason = "사내 보호 도구가 .pia로 암호화함" if default.with_name("default.pptx.pia").exists() else "파일 없음"
    return [f"python-pptx 기본 템플릿을 쓸 수 없음({reason}: {default}) — PPTX 내보내기 불가. "
            f"`pip install --force-reinstall python-pptx`로 다시 설치할 것"]


def check_ppt() -> tuple[list[str], list[str]]:
    failures = preflight.check_core_deps() + check_pptx_default_template() + preflight.check_codex_stubs()
    warnings = preflight.check_optional_deps() + preflight.check_fonts() + preflight.check_officecli()
    return failures, warnings


# --------------------------------------------------------------------------- #
# 한글(HWP)
# --------------------------------------------------------------------------- #

def java_major() -> Optional[int]:
    """`java -version`의 주 버전. java가 없으면 None."""
    if not shutil.which("java"):
        return None
    proc = subprocess.run(["java", "-version"], capture_output=True, text=True, errors="replace")
    match = re.search(r'version "(\d+)(?:\.(\d+))?', proc.stderr + proc.stdout)
    if not match:
        return 0
    major = int(match.group(1))
    # Java 8 이하는 "1.8.0_xxx"로 표기한다.
    return int(match.group(2) or 0) if major == 1 else major


def check_java() -> list[str]:
    major = java_major()
    if major is None:
        return ["java가 PATH에 없음 — 한글 렌더러 실행 불가. Java 8 이상(JRE) 설치 후 터미널을 새로 열 것"]
    if major < 8:
        return [f"Java {major}는 너무 낮음 — 한글 렌더러는 Java 8 이상 필요"]
    return []


def check_hwp_templates() -> list[str]:
    tdir = HWP_SKILL / "templates"
    problems = []
    for name in HWP_BASES:
        path = tdir / name
        if (tdir / (name + ".pia")).exists():
            problems.append(
                f"{path.name}이 사내 보호 도구로 암호화됨({name}.pia) — 해제하거나 "
                f"`git checkout -- {path.relative_to(REPO_ROOT).as_posix()}`로 다시 받을 것")
            continue
        if not path.is_file():
            problems.append(f"템플릿 없음: {path.relative_to(REPO_ROOT).as_posix()}")
            continue
        with path.open("rb") as fh:
            if fh.read(8) != OLE_SIGNATURE:
                problems.append(f"{path.name}이 HWP 5.0 형식이 아님(손상 또는 암호화)")
    for jar in (HWP_SKILL / "scripts" / "koscom-hwp.jar", HWP_SKILL / "lib" / "hwplib-1.1.9.jar"):
        if not jar.is_file():
            problems.append(f"렌더러 파일 없음: {jar.relative_to(REPO_ROOT).as_posix()}")
    return problems


def render_hwp_samples() -> list[str]:
    """예시 report.json 두 개를 임시 폴더에 렌더링해 마지막 줄이 OK인지 본다."""
    classpath = os.pathsep.join(
        str(p) for p in (HWP_SKILL / "lib" / "hwplib-1.1.9.jar", HWP_SKILL / "scripts" / "koscom-hwp.jar"))
    problems = []
    with tempfile.TemporaryDirectory(prefix="doc-pack-doctor-") as tmp:
        for sample in HWP_SAMPLES:
            src = HWP_SKILL / "references" / "examples" / sample
            out = Path(tmp) / (Path(sample).stem + ".hwp")
            # 예시의 그림 경로는 스킬 폴더 기준 상대 경로라 cwd를 스킬 폴더로 둔다.
            proc = subprocess.run(
                ["java", "-Dfile.encoding=UTF-8", "-cp", classpath, "Renderer",
                 str(src), str(out), str(HWP_SKILL / "templates")],
                cwd=HWP_SKILL, capture_output=True, text=True, encoding="utf-8", errors="replace")
            lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
            if proc.returncode != 0 or not lines or not lines[-1].startswith("OK") or not out.is_file():
                detail = lines[-1] if lines else (proc.stderr.strip().splitlines() or ["출력 없음"])[-1]
                problems.append(f"한글 예시 렌더링 실패({sample}): {detail}")
            else:
                print(f"  · 한글 예시 렌더링 OK: {sample} ({out.stat().st_size:,} bytes)", file=sys.stderr)
    return problems


def check_hwp_optional() -> list[str]:
    # 함초롬 글꼴은 한컴 뷰어·한글이 자체 폴더에 함께 설치하므로 따로 확인하지 않는다.
    if sys.platform != "win32":
        return ["Windows가 아님 — 렌더링은 되지만 preview.ps1(한컴 뷰어 화면 확인)은 쓸 수 없음"]
    if not HWP_VIEWER.is_file():
        return [f"한컴 뷰어 없음({HWP_VIEWER}) — 결과 화면 확인 단계를 건너뛰게 됨"]
    return []


def check_hwp(smoke: bool) -> tuple[list[str], list[str]]:
    failures = check_java() + check_hwp_templates()
    if smoke and not failures:
        failures += render_hwp_samples()
    return failures, check_hwp_optional()


# --------------------------------------------------------------------------- #
# 삽화(코쇠)
# --------------------------------------------------------------------------- #

def check_illust() -> tuple[list[str], list[str]]:
    failures, warnings = [], []
    sheet = KOSOE_SKILL / "assets" / "kosoe-character-sheet.png"
    if not sheet.is_file():
        failures.append(f"코쇠 캐릭터 시트 없음: {sheet.relative_to(REPO_ROOT).as_posix()}")
    if not shutil.which("codex"):
        warnings.append("Codex CLI 없음 — 코쇠 삽화 생성 불가(npm install -g @openai/codex 후 codex login)")
    else:
        proc = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, errors="replace",
                              shell=sys.platform == "win32")
        if "ChatGPT" not in proc.stdout + proc.stderr:
            warnings.append("Codex가 ChatGPT 로그인 상태가 아님 — `codex login` 필요")
    if sys.platform == "win32" and not shutil.which("bash"):
        warnings.append("bash(Git Bash) 없음 — gen_image.sh 실행 불가")
    if preflight._module_missing("PIL"):
        warnings.append("Pillow 없음 — 투명 배경 보정과 여백 자르기 불가(pip install Pillow)")
    return failures, warnings


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="koscom-doc-pack 시작 점검: PPT·한글·삽화 경로 준비 상태 확인.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--only", nargs="+", choices=SECTIONS, metavar="SECTION",
                        help=f"일부만 점검 ({', '.join(SECTIONS)})")
    parser.add_argument("--smoke", action="store_true",
                        help="한글 예시 2건을 실제로 렌더링해 본다")
    parser.add_argument("--strict", action="store_true", help="경고도 실패로 본다")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    sections = args.only or list(SECTIONS)
    if sys.version_info < (3, 10):
        print("[doctor] FAIL — Python 3.10 이상 필요", file=sys.stderr)
        return 1

    results = {}
    if "ppt" in sections:
        results["PPT"] = check_ppt()
    if "hwp" in sections:
        results["한글"] = check_hwp(args.smoke)
    if "illust" in sections:
        results["삽화"] = check_illust()

    total_fail = 0
    total_warn = 0
    for label, (failures, warnings) in results.items():
        if args.strict:
            failures, warnings = failures + warnings, []
        state = "FAIL" if failures else ("WARN" if warnings else "OK")
        print(f"[{label}] {state}", file=sys.stderr)
        for f in failures:
            print(f"  ✗ {f}", file=sys.stderr)
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)
        total_fail += len(failures)
        total_warn += len(warnings)

    if total_fail:
        print(f"[doctor] FAIL ({total_fail}건)", file=sys.stderr)
        return 1
    suffix = f" (경고 {total_warn}건)" if total_warn else ""
    print(f"[doctor] PASS{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
