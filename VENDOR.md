# 가져온 저장소 (Vendor)

koscom-doc-pack은 세 저장소를 하나로 묶은 비공개 워크스페이스다. 각 저장소를 가져온 방식, 기준 커밋, 갱신 방법을 여기에 기록한다.

| 출처 | 공개 범위 | 들어간 위치 | 방식 | 기준 커밋 |
|---|---|---|---|---|
| [humanist96/deck-design-pack](https://github.com/humanist96/deck-design-pack) | 공개(MIT) | 저장소 전체(바탕) | 이력 공유, 리모트 `upstream-deck` | `07794bf` |
| [humanist96/koscom_hangul_skill](https://github.com/humanist96/koscom_hangul_skill) | **비공개** | `.claude/skills/koscom-hwp-report/` | `git subtree --squash` | `19bd93b` |
| [humanist96/koscom-kosoe-illustrations](https://github.com/humanist96/koscom-kosoe-illustrations) | 공개(MIT) | `.claude/skills/koscom-kosoe-illustrations/` | 스킬 하위 폴더 복사 + `LICENSE`·`NOTICE.md` | <!-- kosoe-sha -->`7026e62deea48ce0f757e4c16bb1b24e7031c9a2` |

- 코쇠 저장소의 `character/`·`examples/` 원본 폴더는 가져오지 않는다. 스킬이 쓰는 캐릭터 시트와 예시는 스킬 폴더 안에 이미 있다.
- 한글 스킬 subtree의 기준 커밋은 subtree 병합 커밋 메시지의 `git-subtree-split` 값과 같다.

## 상류 파일을 고친 곳

상류에서 온 파일 중 이 저장소가 고친 곳이다. 상류 갱신 때 충돌이 나면 이 목록을 보고 우리 변경을 다시 적용한다.

| 파일 | 고친 내용 |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | 형식 결정(doc-routing.md) 진입, 비공개·`.pia` 규칙, Pretendard 규칙을 PPT로 한정 |
| `README.md` | 맨 위 koscom-doc-pack 안내 |
| `.gitattributes`, `.gitignore` | hwp·jar 바이너리, ps1·sh 줄바꿈, `*.pia` 제외 |
| `.claude/skills/ppt-master/SKILL.md` | description 끝에 "형식이 애매하면 koscom-doc-pack 라우터 먼저" 한 문장 |
| `.claude/skills/koscom-hwp-report/SKILL.md` | description 끝에 같은 취지 한 문장 |

- 코쇠 스킬 폴더는 고치지 않는다. `update_vendor.py kosoe`가 폴더를 통째로 덮어쓰기 때문이다. 고칠 것이 있으면 상류 저장소에서 고친 뒤 가져온다.

## 갱신

모두 `scripts/update_vendor.py`로 한다. `--dry-run`으로 먼저 확인한다.

```bash
python .claude/skills/koscom-doc-pack/scripts/update_vendor.py deck  --dry-run
python .claude/skills/koscom-doc-pack/scripts/update_vendor.py hwp   --source ../koscom-hwp-report
python .claude/skills/koscom-doc-pack/scripts/update_vendor.py kosoe --dry-run
```

| 대상 | 하는 일 | 주의 |
|---|---|---|
| `deck` | `upstream-deck` 리모트를 받아 병합 | 작업 트리가 깨끗해야 함 |
| `hwp` | `git subtree pull --squash` | 비공개 저장소라 git 자격 증명이 필요하다. 없으면 로컬 클론 경로를 `--source`로 준다 |
| `kosoe` | 상류 스킬 폴더를 받아 덮어쓰고 이 문서의 기준 커밋을 갱신 | 줄바꿈 차이는 무시하고 내용 차이만 보여 준다. 확인 후 직접 커밋 |

갱신한 뒤에는 Codex 스텁을 다시 만들고 시작 점검을 돌린다.

```bash
python .claude/skills/ppt-master/scripts/sync_codex_stubs.py
python .claude/skills/koscom-doc-pack/scripts/doctor.py --smoke
```

## 상류로 되돌려 보내기

- 이 저장소에서 고친 내용 중 상류에도 맞는 것(렌더러 보강, 삽화 스크립트 등)은 상류 저장소에도 올린다.
- 한글 스킬은 `git subtree push --prefix .claude/skills/koscom-hwp-report <원격> <브랜치>`로 보낼 수 있다.
- **사내 서식(`.hwp` 템플릿)이 들어간 변경은 공개 저장소(deck-design-pack, koscom-kosoe-illustrations)에 절대 올리지 않는다.**
