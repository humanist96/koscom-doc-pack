# CLAUDE.md

This file is the project entry point for Claude Code. This repository is **koscom-doc-pack**:
the deck-design-pack PPT workspace plus the Koscom Hangul (`.hwp`) report skill and the Kosoe
illustration skill. All skills live under `.claude/skills/` and are auto-discovered by Claude Code.

## Document format entry (koscom-doc-pack)

Pick the output format first, then follow that format's own entry. Each owner keeps its own gates.

| Request | Entry owner |
|---|---|
| PPT / slides / deck / `.pptx` | [`ppt-master/workflows/routing.md`](.claude/skills/ppt-master/workflows/routing.md) (rules below) |
| Hangul / `.hwp` / Koscom 요약보고·상세보고 / report for approval | [`koscom-hwp-report/SKILL.md`](.claude/skills/koscom-hwp-report/SKILL.md) |
| Body illustrations with the Kosoe character (either format) | [`koscom-kosoe-illustrations/SKILL.md`](.claude/skills/koscom-kosoe-illustrations/SKILL.md) |
| Environment check, `.pia`-encrypted templates, upstream updates | [`koscom-doc-pack/SKILL.md`](.claude/skills/koscom-doc-pack/SKILL.md) |

- A format-level router (PPT / Hangul / both from one blueprint) and a Hangul template catalog are
  planned additions to `koscom-doc-pack`; until then, an unstated format for "보고서" means Hangul,
  and "기획서·제안서" with no format named gets one question: Hangul, PPT, or both.
- This repository is **private**. The Hangul templates are Koscom internal forms: never copy them,
  or any change that touches them, into the public upstreams (see [`VENDOR.md`](VENDOR.md)).
- The company privacy tool may encrypt `.hwp` files to `.hwp.pia`. Never try to decrypt or bypass
  it; run `doctor.py` and ask the user to restore the file.

> **Cross-harness (dual-host)**: [`AGENTS.md`](AGENTS.md) is the Codex-side execution-rules layer — it references this file as SSOT and only adds enforcement, so content edits here do not need mirroring there. `.codex/skills/` holds **generated** Codex discovery stubs: after editing any `.claude/skills/<name>/SKILL.md` frontmatter, run `python3 .claude/skills/ppt-master/scripts/sync_codex_stubs.py` (never hand-edit stubs; `preflight.py` fails while they are stale). Skill content itself lives only in `.claude/skills/`.

**Route before full-load (mandatory)**: for a presentation request, first read
[`.claude/skills/ppt-master/workflows/routing.md`](.claude/skills/ppt-master/workflows/routing.md).
Select the route there, then read only the selected execution owner(s) in full.
Do not preload the main SVG skill for a direct-PPTX route. For a repository edit,
read the owner of the contract being changed; the main skill is authoritative only
for the main SVG family and the shared SVG steps that explicitly invoke it.

## Project Overview

PPT Master is a presentation workflow package with SVG-authoring and direct-PPTX
route families. The main SVG family uses Strategist → Image_Generator → Executor
to convert source documents into editable DrawingML. Direct-PPTX routes preserve
an existing PowerPoint package and use their own execution gates.

**Main SVG Pipeline**: `Source Document → Create Project → [Template] → Strategist confirmation stage → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export PPTX`

**Route selection authority**:
[`.claude/skills/ppt-master/workflows/routing.md`](.claude/skills/ppt-master/workflows/routing.md)
owns the complete matrix and wins over every summary below.

| Selected family | Full execution owner(s) |
|---|---|
| New SVG-authored deck or PPTX re-architecture | [Main `ppt-master/SKILL.md`](.claude/skills/ppt-master/SKILL.md) |
| Existing PPTX, strict 1:1 wording/page preservation with visual redesign | [`beautify-pptx.md`](.claude/skills/ppt-master/workflows/beautify-pptx.md), then the main skill only at its explicit shared-SVG handoff |
| Raw PPTX template plus new material/topic | [`ppt-template-fill/SKILL.md`](.claude/skills/ppt-template-fill/SKILL.md) only |
| Finished PPTX, stable visible content/layout, add notes/audio/timing/transitions | [`native-enhance-pptx/SKILL.md`](.claude/skills/native-enhance-pptx/SKILL.md), then its required execution workflow |
| Reusable template creation or another standalone workflow | The selected workflow; load another owner only at an explicit handoff |

An ambiguous PPTX optimization request stays in the router until its one
discriminator question resolves whether the deck is 1:1 beautify or
re-architectable source. Do not load either full owner before that answer.

## Execution Ownership

- The selected skill or workflow owns its confirmations, preflight, validation,
  recovery, export, and completion gates. This root file adds none.
- Shared scripts do not transfer gate ownership between SVG and direct-PPTX
  families.
- Topic research, template creation, and post-route workflows load the next
  owner only when their own procedure declares a handoff.

## Font Policy (install-local, standing preference)

- Scope: this policy covers PPT decks only. Hangul `.hwp` output keeps the fonts of its Koscom
  template (함초롬바탕·HY헤드라인M etc.); do not apply Pretendard there.
- Every SVG-authored deck uses **Pretendard** as the fixed font family — do not propose or pick other families unless the user explicitly asks in the current conversation. Hierarchy comes from weight/size, not family switching. Direct-PPTX routes preserve source fonts unless their selected owner says otherwise. Full contract: [`strategist.md §g` install-local font lock](.claude/skills/ppt-master/references/strategist.md).
- Stack: `Pretendard, "Malgun Gothic", sans-serif`; intermediate weights use installed family names (`"Pretendard Medium"`, `"Pretendard SemiBold"`, etc.).
- Font files are bundled at [`.claude/skills/ppt-master/assets/fonts/Pretendard/`](.claude/skills/ppt-master/assets/fonts/Pretendard/) (SIL OFL) and installed user-level on this machine. PPTX does not embed fonts — decks shared to other machines need Pretendard installed there.

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`.claude/skills/ppt-master/references/`](.claude/skills/ppt-master/references/), Python under [`.claude/skills/ppt-master/scripts/`](.claude/skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Markdown language consistency** — Markdown files under `.claude/skills/ppt-master/workflows/`, `.claude/skills/ppt-master/references/`, and `docs/` are currently single-language per directory. New files mirror the language of their siblings; do not mix English scaffolding with Chinese paragraphs (or vice versa) inside one file. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize the selected repo-local
  execution owner. The main [`ppt-master/SKILL.md`](.claude/skills/ppt-master/SKILL.md)
  has that role only when routing selected the main SVG family or an explicit
  shared-SVG handoff.

## Execution Pointers

Commands and defaults belong to the selected owner; use these pointers instead
of treating a root-level command list as a gate checklist.

| Work | Runtime authority |
|---|---|
| Route selection | [`routing.md`](.claude/skills/ppt-master/workflows/routing.md) |
| Main SVG generation and re-architecture | [`ppt-master/SKILL.md`](.claude/skills/ppt-master/SKILL.md) |
| Strict 1:1 SVG beautify | [`beautify-pptx.md`](.claude/skills/ppt-master/workflows/beautify-pptx.md) and only the shared main steps it invokes |
| Raw template fill | [`ppt-template-fill/SKILL.md`](.claude/skills/ppt-template-fill/SKILL.md) |
| Finished-PPTX native enhancement | [`native-enhance-pptx/SKILL.md`](.claude/skills/native-enhance-pptx/SKILL.md) |
| Standalone workflow inventory | [`workflows/index.md`](.claude/skills/ppt-master/workflows/index.md) |

## Core Directories

- `.claude/skills/ppt-master/SKILL.md` — main SVG workflow authority.
- `.claude/skills/ppt-template-fill/SKILL.md` — raw-template direct-PPTX authority.
- `.claude/skills/native-enhance-pptx/SKILL.md` — finished-PPTX enhancement entry owner.
- `.claude/skills/ppt-master/references/` — role definitions and technical specifications.
- `.claude/skills/ppt-master/scripts/` — runnable tool scripts.
- `.claude/skills/ppt-master/scripts/docs/` — topic-focused script docs.
- `.claude/skills/ppt-master/templates/` — layout templates, chart templates, icon library, brand presets.
- `.claude/skills/ppt-master/workflows/` — standalone workflow files.
- `docs/` — user-facing documentation (FAQ, installation, technical design, templates guide, audio narration).
- `docs/rules/` — repo-wide style rules.
- `projects/` — user project workspace.

## Base workspace: deck-design-pack

koscom-doc-pack is built on [humanist96/deck-design-pack](https://github.com/humanist96/deck-design-pack)
(git remote `upstream-deck`; other sources and update steps in [`VENDOR.md`](VENDOR.md)) — the
ppt-master workflow above, vendored from
[byungjunjang/slide-master](https://github.com/byungjunjang/slide-master) (MIT, © 2025-2026 Hugo He;
see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)), with seven additional deck templates
already installed and registered.

- Seven pack templates live alongside the bundled ones in
  `.claude/skills/ppt-master/templates/decks/`: `midnight-panel`, `polarity`, `gradient-mesh`,
  `warm-doc`, `open-road`, `signal-green`, `koscom-chevron`. Each is a 10-page roster —
  1 Master + 9 Layouts, the two chart pages sharing `chart_linear`. Matching identity-only
  presets sit in `templates/brands/`.
- **The templates are the source of truth in place.** There is no separate `decks/` or `brands/`
  directory at the repository root; editing a template means editing it under
  `.claude/skills/ppt-master/templates/`.
- After changing a template's `design_spec.md` frontmatter, re-run
  `python3 install.py <some-other-workspace> --dry-run` only if you are exporting; the in-repo
  index entries are maintained by hand or by re-running the installer against a scratch workspace.
  Never re-register these ids with `register_template.py` — it drops the `defaults` anchor block
  the Confirm UI reads.
- `install.py` exports this pack into a *different* ppt-master workspace. It refuses to target
  this repository.
- Authoring rules for the pack's own 10-page spine: [`docs/authoring.md`](docs/authoring.md).
  Per-template detail: [`docs/gallery.md`](docs/gallery.md).
