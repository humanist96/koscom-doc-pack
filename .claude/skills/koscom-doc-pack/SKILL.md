---
name: koscom-doc-pack
description: 사내 문서를 만들어 달라는 요청에서 출력 형식(PPT .pptx · 한글 .hwp · 둘 다)을 먼저 정하는 최상위 라우터이자 koscom-doc-pack 워크스페이스 운영 스킬. 보고서·기획서·제안서·계획서·발표자료·장표·요약보고·결과보고·소개자료처럼 문서를 새로 만들거나 채우는 요청이면 형식 담당 스킬을 읽기 전에 workflows/doc-routing.md로 형식을 정한다. "기획서 만들어줘"처럼 형식이 애매하면 한 번만 묻고, "보고서랑 발표자료 둘 다"면 두 형식을 같은 내용으로 만든다. "문서팩 점검", "doctor", "한글 렌더러가 안 돼", "템플릿이 .pia로 바뀌었어", "상류 업데이트 받아줘" 같은 환경·운영 요청에도 쓴다.
---

# koscom-doc-pack

이 저장소는 PPT·한글·삽화 스킬을 묶은 통합 워크스페이스다. 이 스킬은 두 가지를 맡는다.

1. **형식 라우팅**: 문서 요청의 출력 형식을 정하고 담당 스킬로 넘긴다.
2. **운영**: 시작 점검과 상류 저장소 갱신.

## 형식 라우팅

문서를 만들거나 채우는 요청이면 [`workflows/doc-routing.md`](workflows/doc-routing.md)를 **전부 읽고** 그 표대로 형식을 정한다. 형식을 정하기 전에는 담당 스킬 파일을 읽지 않는다.

| 형식 | 담당 | 넘긴 뒤 |
|---|---|---|
| PPT(.pptx) | `ppt-master/workflows/routing.md` | PPT 안의 경로 선택과 모든 확인 단계는 그 파일이 정한다 |
| 한글(.hwp) | `koscom-hwp-report/SKILL.md` | 보고 유형 선택부터 결과 확인까지 그 스킬 절차대로 |
| 둘 다 | `doc-routing.md` 5장 | 한글 먼저 → 원고 넘기기 → PPT, 삽화는 한 번 만들어 재사용 |
| 삽화만 | `koscom-kosoe-illustrations/SKILL.md` | 그 스킬 절차대로 |

- 형식이 애매한 경우(기획서·제안서 등)에만 질문을 **한 번** 한다. 질문 문구는 `doc-routing.md` 3장에 있다.
- 한글 양식 채우기, 기존 `.hwp` 고치기, `.hwpx`·Word 출력은 아직 지원하지 않는다. `doc-routing.md` 4장대로 알리고 대안을 제시한다.
- 한글로 정해지면 `koscom-hwp-report`가 문서 유형 템플릿 13종(결과보고·계획보고·이슈 보고·제안서 등) 중 하나를 고른다(그 스킬의 1-1단계).
- 공통 설계도(`doc.json`)는 다음 단계(P5)에서 추가된다.

## 운영

### 시작 점검

PPT·한글·삽화 경로가 이 PC에서 돌아가는지 확인한다. 저장소 루트에서 실행한다.

```bash
python .claude/skills/koscom-doc-pack/scripts/doctor.py --smoke
```

- `--smoke`: 한글 예시 2건(요약·상세)을 임시 폴더에 실제로 렌더링한다.
- `--only ppt hwp illust`: 일부만 점검한다.
- 마지막 줄이 `[doctor] PASS`면 준비된 것이다. `FAIL`은 그 경로를 쓸 수 없는 문제, `!`로 시작하는 줄은 결과 확인만 못 하게 되는 경고다.

| 자주 나오는 결과 | 대응 |
|---|---|
| `Codex stubs are stale` | `python .claude/skills/ppt-master/scripts/sync_codex_stubs.py` |
| 템플릿이 `.pia`로 암호화됨 | 사내 보호 도구가 암호화한 것이다. **해제하거나 우회하려 하지 않는다.** 사용자에게 해제를 요청하거나 `git checkout -- <경로>`로 다시 받게 한다 |
| python-pptx 기본 템플릿을 쓸 수 없음 | 보호 도구가 `default.pptx`를 암호화한 경우가 많다. 사용자 동의를 받아 `pip install --force-reinstall python-pptx` |
| `java가 PATH에 없음` | Java 8 이상 설치 후 터미널을 새로 연다 |
| 한컴 뷰어 없음 | 렌더링은 되지만 화면 확인을 건너뛴다. 결과 전달 시 확인하지 못했다고 알린다 |
| Codex CLI·로그인 경고 | 코쇠 삽화를 만들 수 없다. 사용자에게 `codex login`을 부탁한다 |

### 상류 갱신

가져온 방식과 기준 커밋은 루트의 `VENDOR.md`에 있다. 갱신은 `--dry-run`으로 먼저 보여 주고, 사용자가 원할 때만 실제로 적용한다.

```bash
python .claude/skills/koscom-doc-pack/scripts/update_vendor.py {deck|hwp|kosoe} --dry-run
```

갱신 후에는 Codex 스텁을 다시 만들고 `doctor.py --smoke`를 돌린다. 사내 서식이 든 변경은 공개 저장소로 보내지 않는다.
