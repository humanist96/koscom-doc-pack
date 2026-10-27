#!/usr/bin/env python3
"""
koscom-doc-pack - 상류 저장소 갱신

이 팩이 가져온 세 저장소의 새 변경을 받아 온다. 가져오는 방식이 저장소마다 다르다
(VENDOR.md 참고).

- deck   : 이 저장소의 바탕. `upstream-deck` 리모트를 병합한다.
- hwp    : `git subtree pull`로 .claude/skills/koscom-hwp-report를 갱신한다.
- kosoe  : 상류의 스킬 하위 폴더만 복사하고 VENDOR.md의 커밋을 바꾼다.

deck·hwp는 작업 트리가 깨끗해야 하며, 결과는 git이 커밋한다. kosoe는 파일만 바꾸므로
차이를 확인한 뒤 직접 커밋한다.

Usage:
    python .claude/skills/koscom-doc-pack/scripts/update_vendor.py {deck,hwp,kosoe} [options]

Examples:
    python .claude/skills/koscom-doc-pack/scripts/update_vendor.py kosoe --dry-run
    python .claude/skills/koscom-doc-pack/scripts/update_vendor.py hwp --source ../koscom-hwp-report
    python .claude/skills/koscom-doc-pack/scripts/update_vendor.py deck

Dependencies:
    None (only uses standard library; needs git on PATH)
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# scripts/update_vendor.py: [0]=scripts [1]=koscom-doc-pack [2]=skills [3]=.claude [4]=repo
REPO_ROOT = Path(__file__).resolve().parents[4]
PPT_SCRIPTS = REPO_ROOT / ".claude" / "skills" / "ppt-master" / "scripts"
if str(PPT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PPT_SCRIPTS))

from console_encoding import configure_utf8_stdio  # noqa: E402

VENDOR_MD = REPO_ROOT / "VENDOR.md"
HWP_PREFIX = ".claude/skills/koscom-hwp-report"
HWP_SOURCE = "https://github.com/humanist96/koscom_hangul_skill.git"
KOSOE_SOURCE = "https://github.com/humanist96/koscom-kosoe-illustrations.git"
KOSOE_DIR = REPO_ROOT / ".claude" / "skills" / "koscom-kosoe-illustrations"
# 상류 저장소 루트에서 스킬 폴더 옆에 함께 가져오는 파일(MIT 고지 유지용)
KOSOE_EXTRA = ("LICENSE", "NOTICE.md")


def git(*args: str, cwd: Path = REPO_ROOT, capture: bool = False) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, encoding="utf-8", errors="replace",
                          capture_output=capture)
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip() if capture else ""
        raise RuntimeError(f"git {' '.join(args)} 실패{': ' + detail if detail else ''}")
    return proc.stdout if capture else ""


def require_clean_tree() -> None:
    if git("status", "--porcelain", capture=True).strip():
        raise RuntimeError("작업 트리에 커밋하지 않은 변경이 있음 — 먼저 커밋하거나 치울 것")


def update_deck(ref: str, dry_run: bool) -> None:
    git("fetch", "upstream-deck")
    log = git("log", "--oneline", f"HEAD..upstream-deck/{ref}", capture=True).strip()
    if not log:
        print("deck: 새 커밋 없음", file=sys.stderr)
        return
    print(f"deck: 새 커밋\n{log}", file=sys.stderr)
    if dry_run:
        return
    require_clean_tree()
    git("merge", "--no-edit", f"upstream-deck/{ref}")


def update_hwp(source: str, ref: str, dry_run: bool) -> None:
    print(f"hwp: {source} {ref} → {HWP_PREFIX}", file=sys.stderr)
    if dry_run:
        return
    require_clean_tree()
    git("subtree", "pull", "--prefix", HWP_PREFIX, source, ref, "--squash",
        "-m", f"Update koscom-hwp-report from koscom_hangul_skill ({ref})")


def changed_files(src: Path, dst: Path) -> list[str]:
    """줄바꿈(CRLF/LF) 차이는 무시하고 내용이 다른 파일과 추가·삭제 파일을 찾는다."""
    def files(root: Path) -> set[str]:
        return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}

    def same(a: Path, b: Path) -> bool:
        if filecmp.cmp(a, b, shallow=False):
            return True
        return a.read_bytes().replace(b"\r\n", b"\n") == b.read_bytes().replace(b"\r\n", b"\n")

    left, right = files(src), files(dst)
    out = [f"+ {f}" for f in sorted(left - right)] + [f"- {f}" for f in sorted(right - left)]
    out += [f"~ {f}" for f in sorted(left & right) if not same(src / f, dst / f)]
    return out


def update_kosoe(source: str, ref: str, dry_run: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="kosoe-") as tmp:
        clone = Path(tmp) / "src"
        git("clone", "-q", "--depth", "1", "--branch", ref, source, str(clone), cwd=Path(tmp))
        sha = git("rev-parse", "HEAD", cwd=clone, capture=True).strip()
        staged = Path(tmp) / "staged"
        shutil.copytree(clone / "koscom-kosoe-illustrations", staged)
        for name in KOSOE_EXTRA:
            shutil.copy2(clone / name, staged / name)

        diff = changed_files(staged, KOSOE_DIR)
        print(f"kosoe: 상류 {sha[:7]}, 바뀐 파일 {len(diff)}개", file=sys.stderr)
        for line in diff:
            print(f"  {line}", file=sys.stderr)
        if dry_run or not diff:
            return
        shutil.rmtree(KOSOE_DIR)
        shutil.copytree(staged, KOSOE_DIR)

    text = VENDOR_MD.read_text(encoding="utf-8")
    new_text, count = re.subn(r"(<!-- kosoe-sha -->)`[0-9a-f]+`", rf"\g<1>`{sha}`", text)
    if count != 1:
        raise RuntimeError("VENDOR.md에서 kosoe 커밋 표시(<!-- kosoe-sha -->)를 찾지 못함")
    VENDOR_MD.write_text(new_text, encoding="utf-8")
    print("kosoe: 파일과 VENDOR.md를 갱신함 — 차이를 확인하고 커밋할 것", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="koscom-doc-pack 상류 저장소 갱신.")
    parser.add_argument("target", choices=("deck", "hwp", "kosoe"), help="갱신할 상류")
    parser.add_argument("--source", help="hwp·kosoe 상류 경로나 URL (기본: GitHub)")
    parser.add_argument("--ref", default="main", help="브랜치 (기본: main)")
    parser.add_argument("--dry-run", action="store_true", help="바뀔 내용만 보여 주고 쓰지 않음")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        if args.target == "deck":
            update_deck(args.ref, args.dry_run)
        elif args.target == "hwp":
            update_hwp(args.source or HWP_SOURCE, args.ref, args.dry_run)
        else:
            update_kosoe(args.source or KOSOE_SOURCE, args.ref, args.dry_run)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
