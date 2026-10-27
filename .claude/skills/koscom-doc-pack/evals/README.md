# 형식 라우팅 평가

`doc-routing.md`가 문서 요청의 출력 형식을 맞게 정하는지 보는 과제 9개다. `claude plugin eval` 형식(`case.yaml`, `prompt.md`, `graders/`)으로 썼다. 채점은 실행 기록(trace)만 본다: 무엇을 먼저 읽었는지, 형식 질문을 했는지, 어느 담당으로 넘겼는지.

| 과제 | 요청 | 기대 |
|---|---|---|
| routing-01-ppt-explicit | 실적 자료로 임원 보고용 PPT | PPT, 질문 없음 |
| routing-02-ppt-template-fill | .pptx 양식에 새 내용 채우기 | PPT → 템플릿 채우기 |
| routing-03-ppt-screen-report | 고객 미팅에서 화면에 띄울 보고 자료 | PPT (8번 단서) |
| routing-04-hwp-summary | 회의 메모로 요약보고 | 한글 |
| routing-05-hwp-approval | 팀장님 결재 올릴 결과 보고서 | 한글 |
| routing-06-hwp-report-only | 장애 건 보고서 | 한글 (보고서 기본값) |
| routing-07-ask-plan | 도입 기획서 | 형식 질문 한 번 |
| routing-08-ask-proposal | 회사 소개 제안서 | 형식 질문 한 번 |
| routing-09-both | 같은 내용으로 한글 보고서와 PPT | 둘 다, 한글 먼저 |

## 결과

**2026-10-28 (P1): 9/9 통과.**

- 실행 방식은 대리 실행이다. 서브에이전트 3개에 과제를 3개씩 섞어 주고, 새 세션처럼 `CLAUDE.md`와 스킬 목록에서 시작해 내용 작업 직전까지만 진행하게 했다. 기대 답은 알려 주지 않았다.
- 9건 모두 `doc-routing.md`를 담당 파일보다 먼저 읽었다. 형식 질문은 07·08에서만 정확히 한 번 했다.
- 실행 중 드러난 빈틈 세 가지를 고쳤다.
  - 8번 줄에 "보고 자료"를 추가했다.
  - "기획안"을 9번(질문)에 넣고 한글 스킬 설명과 맞췄다.
  - `CLAUDE.md`에 "일반 문서 스킬(pptx·docx·docs)로 보내지 않는다"는 줄을 추가했다.
- `claude plugin eval`로 실제 세션을 돌리는 정식 실행은 아직 하지 않았다. 그때는 담당 스킬이 실제 작업을 시작하므로 `max_turns: 12`에서 끊긴다. 채점은 그 앞의 라우팅 부분만 본다.
