---
name: koscom-doc-pack
description: koscom-doc-pack 워크스페이스(PPT·한글·코쇠 삽화 통합)의 시작 점검과 상류 저장소 갱신을 맡는다. "문서팩 점검", "doctor", "환경 확인", "한글 렌더러가 안 돼", "템플릿이 .pia로 바뀌었어", "상류 업데이트 받아줘", "deck-design-pack/한글 스킬/코쇠 스킬 최신으로" 같은 요청에 쓴다. PPT나 한글 문서를 만드는 요청 자체는 각 형식의 스킬(ppt-master, koscom-hwp-report)이 맡는다.
---

# koscom-doc-pack 운영

이 저장소는 세 저장소를 묶은 통합 워크스페이스다.

| 형식 | 스킬 | 진입 |
|---|---|---|
| PPT(.pptx) | `ppt-master` 외 4종 | `.claude/skills/ppt-master/workflows/routing.md` |
| 한글(.hwp) | `koscom-hwp-report` | `.claude/skills/koscom-hwp-report/SKILL.md` |
| 삽화(PNG) | `koscom-kosoe-illustrations` | `.claude/skills/koscom-kosoe-illustrations/SKILL.md` |

형식을 고르는 문서 라우터와 한글 템플릿 카탈로그는 다음 단계(P1·P2)에서 이 스킬에 추가한다. 계획은 저장소 밖의 `koscom-doc-pack_상세계획서.md`에 있다.

## 시작 점검

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
| `java가 PATH에 없음` | Java 8 이상 설치 후 터미널을 새로 연다 |
| 한컴 뷰어 없음 | 렌더링은 되지만 화면 확인을 건너뛴다. 결과 전달 시 확인하지 못했다고 알린다 |
| Codex CLI·로그인 경고 | 코쇠 삽화를 만들 수 없다. 사용자에게 `codex login`을 부탁한다 |

## 상류 갱신

가져온 방식과 기준 커밋은 루트의 `VENDOR.md`에 있다. 갱신은 `--dry-run`으로 먼저 보여 주고, 사용자가 원할 때만 실제로 적용한다.

```bash
python .claude/skills/koscom-doc-pack/scripts/update_vendor.py {deck|hwp|kosoe} --dry-run
```

갱신 후에는 Codex 스텁을 다시 만들고 `doctor.py --smoke`를 돌린다. 사내 서식이 든 변경은 공개 저장소로 보내지 않는다.
