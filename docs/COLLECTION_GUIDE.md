# 수집 가이드 — 정책, 데이터 규칙, 검증

## 1. 수집 정책 (안전 규칙)
- **공식 브랜드 사이트와 공식 금융사 사이트만** 읽는다. 뉴스·블로그 수치는 넣지 않는다(넣어야 하면 `confidence: low`, "미확인").
- 쿠키 배너는 **필수만 저장/거절**. '전체 동의' 금지.
- **읽기 전용.** 로그인, 시승·견적 신청 폼 제출, 개인정보 입력 금지.
- 접속 실패/403이면 다음 브랜드로 넘어가고 `status` 로 남긴다. 같은 사이트를 반복 재시도하지 않는다.
- 페이지에 없는 값은 **추측하지 않는다**. 읽지 못한 값은 `미수집` 또는 `null`.
- 사이트에 부담을 주지 않도록 페이지는 필요한 만큼만 연다.

## 2. 수집 단위와 읽는 법
브랜드마다 아래 **두 종류 페이지를 모두** 연다.
1. **구매혜택(월별 프로모션) 페이지** — 모델별 할인·금융 조건.
2. **이벤트 목록 페이지** — 시승 이벤트, 추첨·경품, 제휴 프로모션. (놓치기 쉽다. 르노는 구매혜택 페이지만 보고 시승 이벤트 2건을 놓쳤다.)
읽는 방법:
- 텍스트가 DOM에 있으면 `document.body.innerText` 로 읽는다(가장 정확).
- 본문이 **이미지**이면 스크린샷을 스크롤하며 눈으로 읽고, 읽은 문구를 그대로 증거 파일에 적는다(`# method:` 에 "스크린샷 육안").
- 목록이 여러 페이지면(현대 3페이지) 페이지 번호 버튼을 클릭해 모두 읽는다.
- 목록 항목이 링크가 아니라 클릭 핸들러이면(기아) 항목을 클릭해 상세로 들어간다.
- 모델 탭/아코디언은 하나씩 열어 읽는다(KGM 모델 탭, 르노 '열기').
- 기간 표기는 반드시 옮긴다. 기간이 지난 프로모션은 만료로 처리한다.

## 3. 증거(원문) 저장
파일: `data/evidence/<brand_id>/<YYYY-MM-DD>_<slug>.txt`
```
# url: <읽은 페이지 주소>
# captured: <일시>
# method: <읽은 방법(innerText / 스크린샷 육안 등)과 한계>
---
<본문(가공·요약 금지. 메뉴·푸터는 빼도 됨)>
```
- 원본 JSON에는 **증거 파일에 있는 내용만** 옮긴다.
- 항목의 `link` 와 증거의 `# url:` 이 같으면 그 증거로 대조한다(쿼리스트링 포함 동일해야 함).

## 4. 자동 대조 (`scripts/verify_evidence.py`)
항목의 금액(만원/원), %, 개월, 인원(명/분), 모델명, 기간(시작·종료일), 최대혜택 금액이 증거 원문에 있는지 확인한다.
- `검증됨` / `일부 미확인`(→ **게시 중단**) / `증거 없음`(게시는 되지만 AI용 파일에 "원문 대조 안 됨" 표시).
- 같은 주소의 증거가 없는 항목이 다른 페이지 증거와 안 맞아도 '불일치'가 아니라 '증거 없음'으로 처리한다.
- 원문과 같은 내용인데 표기만 다른 경우(영문/한글 모델명, 월을 줄여 쓴 기간 등)에만 `data/verify_ack.json` 에 **이유를 적어** 예외 승인한다. 예: `{"brand_id","title_contains","claim","reason"}`, `claim` 은 `"모델:Filante"`, `"기간 종료일"`, `"200만"` 같은 형태.
- 금액이 바뀐 항목과 새 항목은 수집한 AI가 아닌 **다른 AI(서브에이전트)에게 원문과 해당 행만 주고 재확인**시킨다.

## 5. 데이터 규칙 (`scripts/build_benefits.py`)
`data/unified/benefits.*` 컬럼:
`id, ym, period_status, brand_id, brand_ko, model, sub_model, model_year, target_scope, event_name, types, title, discount_type, discount_amount_krw, discount_rate_pct, discount_options, max_benefit_krw, discount, conditions, reward, detail, period_start, period_end, link, confidence, source_record_id, extract_note` + 검증 컬럼 `verification, unverified_claims, evidence_files, evidence_date`.
- `ym`=수집한 달. `period_status`=기준월 해당 / 기간 만료 / 시작 전 / 기간 미표기.
- **model / sub_model**: 차량 이름만. 혜택·이벤트·금융 단어, 연식(2026, 26MY, 26년식)이 들어가면 ERROR. 연식은 `model_year`, "전 모델" 같은 묶음은 `target_scope`(모델은 비움).
- **event_name**: 프로그램·행사 이름. 이벤트 행은 원래 이름 그대로, 이벤트명이 따로 없으면 "월 구매 혜택(이벤트명 미표기)" 같은 대체 이름을 쓴다(INFO로 표시).
- **할인 금액은 별도 컬럼**: `discount_type`(정액 할인 / 정률 할인 / 정액+정률 할인 / 금융 조건 / 할인 없음), `discount_amount_krw`(선택지 중 최대 정액), `discount_rate_pct`(최대 정률), `discount_options`(선택지 전체 원문). 월 납입금·금리·선납률은 할인이 아니다. 숫자는 문장에서 뽑으므로 틀릴 수 있다(`extract_note`).
- 한 문장은 한 칸에만: 증정·경품 > 할인·금융 > 조건. 기간·대상 모델 문장은 칸에서 뺀다(`detail` 에 있음).
- 시승 이벤트는 `data/testdrive/index.json` 에서 가져오며, 같은 이름의 이벤트 행이 이미 있으면 새 행을 만들지 않고 합친다(이름이 통째로 같은 행 우선).

## 6. 품질 점검 (`scripts/quality_check.py`) — ERROR가 있으면 게시하지 않는다
필수 필드, 영문 내부 키 노출, 모델명 이상(점검·결과 등), 모델에 혜택/연식 섞임, 이벤트명 누락·모델명과 동일, 정액/정률 할인인데 숫자 컬럼 비어 있음, 가격 범위, 혜택>가격, 기간 순서·만료, 중복, 시승 일관성, 브랜드 커버리지, 이전 실행 대비 감소(브랜드 소실은 `data/quality_ack.json` 에 이유 필요), 원문 대조 결과.

## 7. 게시 (`scripts/update_all.ps1`)
`build_db` → `build_benefits` → `verify_evidence` → `diff_benefits`(직전 커밋과 비교, `docs/CHANGES.md`) → `export_bundle`(`dist/car_db_for_ai.md`) → `quality_check`(게이트) → 통과 시 git 커밋·푸시 → gist 3개 파일 갱신.
AI용 파일 맨 위에는 **표 작성 규칙**(열 정의, 필터 말뜻, 정렬, 금지, 예시)이 들어간다. 회사 AI가 표를 달라고 하면 이 열을 그대로 복사하도록 유도하기 위해서다.
