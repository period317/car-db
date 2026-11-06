# 주기 갱신 플레이북 (Claude가 예약 실행할 때 따르는 절차)

목표: 공식 사이트에서 최신 혜택·가격·시승 정보를 다시 읽어 `data/`를 갱신하고, 통합본을 만든 뒤 GitHub에 올린다.
작업 폴더: `car-db/` (이 파일의 상위). 브라우저는 Claude in Chrome(실제 Chrome) 사용.

## 목적과 수집 원칙
- **이 DB의 목적은 월별 혜택**(할인, 이벤트, 금융 프로모션, 시승 이벤트)이다. 차량 가격은 참고 정보이며 혜택 수집보다 앞서지 않는다.
- **대표값을 고르지 않는다.** 페이지에 트림·모델·조건이 여러 개면 전부 기록한다(중간값, 최저가, 최다판매 트림만 넣는 방식 금지). 트림 이름이 있으면 함께 적고, 없으면 없다고 `note`에 쓴다.
- 데이터가 늘어나도 있는 정보를 줄이지 않는다.

## 0. 안전 규칙
- **공식 브랜드/금융사 사이트만** 읽는다. 뉴스·블로그 수치는 넣지 않는다(넣더라도 `confidence: low`, '미확인' 표기).
- 쿠키 배너: 비필수 쿠키는 **거절/필수만 저장**. '전체 동의' 금지.
- 로그인, 견적·시승 **신청 폼 제출 금지**(읽기 전용). 개인정보 입력 금지.
- 한 사이트가 접속 실패/403이면 다음 브랜드로 넘어가고 `status`로 기록. 같은 사이트를 반복 재시도하지 않는다.
- 페이지에 없는 값은 추측하지 않는다. 읽지 못한 항목은 `미수집` 또는 `null`.

## 1. 우선순위 정하기
```
python -I scripts/check_stale.py
```
출력된 브랜드(기간 만료 / 14일 경과 / 데이터 없음)를 먼저 갱신. 매월 1일~5일엔 전 브랜드 전체 갱신(월 단위 프로모션이 바뀜).

## 2. 브랜드별 갱신
각 `data/offers/<브랜드>_*.json`의 `meta.source_url`(또는 `site`, `urls`)을 다시 열어 같은 필드 구조로 새 파일을 저장한다.
- 파일명: `<브랜드>_YYYY-MM-DD.json` (오늘 날짜). 이전 날짜 파일은 `data/archive/`로 옮겨 보관(통합본은 `data/offers/`만 읽음).
- 시승: `data/testdrive/index.json`의 해당 브랜드 항목(`can_apply_online`, `apply_url`, `models`, `has_event`, 이벤트 필드)을 직접 수정. 이벤트가 끝났으면 `has_event:false`.
- 텍스트 DOM으로 읽히면 `javascript_tool`로 `document.body.innerText` 추출(가장 정확). 이미지 페이지(쉐보레 이벤트, MINI 프로모션)는 스크린샷을 스크롤하며 읽는다.
- 기간 표기(`period_*`, `valid`)를 반드시 옮긴다. 기간이 지난 프로모션은 `STALE`로 표시하고 새 페이지가 올라왔는지 확인한다.

### 2.1 이벤트 목록 페이지도 반드시 연다 (르노에서 시승 이벤트를 놓친 교훈)
구매혜택 페이지만 읽으면 시승 이벤트·추첨 경품·제휴 프로모션이 빠진다. 브랜드마다 **이벤트 목록 페이지의 진행 중 항목 전부**를 DB와 대조한다.
- 목록에서 새로 찾은 이벤트는 `data/offers/<브랜드>_*.json` 의 `events_extra` 배열에 `{name, period, text, url, model(없으면 null), conf}` 로 넣는다(`build_db.py` 가 읽음).
- 목록 수준만 읽었으면 `text` 에 "(상세 미수집)"이라고 쓴다. 시승·할인·경품 이벤트는 상세 페이지까지 읽는다.
- 시승 이벤트는 `data/testdrive/index.json` 의 `has_event`, `event_name`, `event_benefit`, `event_period`, `event_url` 도 고친다(브랜드당 1건 슬롯, 나머지는 `note`).
- 이벤트 목록 주소·읽는 요령·확인 현황은 `docs/SITE_GUIDE.md`, 정책과 데이터 규칙은 `docs/COLLECTION_GUIDE.md`, 이어받는 순서는 `docs/HANDOFF.md`. 새로 알게 된 사이트 구조나 함정은 끝나기 전에 `SITE_GUIDE.md`/`LESSONS.md` 에 추가한다.

사이트별 힌트(이전 수집에서 확인):
| 브랜드 | 위치 | 방식 |
|---|---|---|
| 기아 | /kr/buy/special-offers | 모델 카드(최다 판매 트림 가격) 25개가 DOM에 전부 있음 |
| 현대 | /kr/ko/e/vehicles/monthly-benefit | 승용 탭 텍스트, 상용 탭은 별도 클릭 |
| 제네시스 | /kr/ko/shopping/monthly-offer.html | 텍스트 |
| KGM | /od/promotion/monthly-benefits | 모델 탭 버튼을 하나씩 클릭해 '스페셜 혜택' 읽기 |
| BMW | /ko/finance/special-offer/financial-promotion/*.html | 모델 7페이지, 적용기간 확인 |
| 르노코리아 | /ko/buy/tm_purchasing.jsp | '열기' 아코디언을 모델별로 열기 |
| 쉐보레 | /purchase/offers-faq.gm(텍스트), /events/...(이미지) | 혜택 게시 모델만 |
| 벤츠 | /passengercars/buy/new-car/promotion.html | 금액 비공개, 쿠키 배너 필수 처리 |
| 토요타 | /benefit/monthly/, /seasonal-event/ | 텍스트 |
| 렉서스 | /purchase-benefit/monthly/ | 글자 단위로 쪼개져 있어 공백 결합 |
| 볼보 | volvocar.co.kr (volvocars.com/kr 아님) | 재구매·시승 캠페인 |
| 랜드로버 | landroverkorea.co.kr/offers/ | 월 납입금 롤링 숫자(마지막 합산값만) |
| 푸조 | epeugeot.co.kr/Sales/promotion 이 404 | 네이버 공식 스토어 확인 필요(접근 제한 가능) |
| 테슬라 | /ko_kr/modely/design 등 | 가격은 스크린샷 |
나머지 브랜드는 해당 `data/offers/*.json`의 `meta`에 URL과 방법이 적혀 있다.

## 2.5 증거(원문) 저장과 검증 — 틀리면 안 되는 부분이므로 생략하지 않는다
1. **원문 저장**: 브랜드의 혜택 페이지를 읽을 때마다, 읽은 본문 텍스트를 `data/evidence/<brand_id>/<오늘날짜>_<slug>.txt` 로 Write 한다.
   맨 위에 `# url: <페이지 주소>`, `# captured: <일시>`, `# method: <읽은 방법>`, 다음 줄에 `---`, 그 아래에 본문(가공·요약 금지, 혜택과 관련 없는 메뉴·푸터는 빼도 됨).
   이미지 페이지는 텍스트가 없으므로 스크린샷에서 읽은 문구를 그대로 옮겨 적고 `# method:` 에 '스크린샷 육안'이라 쓴다.
2. 원본 JSON(`data/offers/`)에는 **증거 파일에 있는 내용만** 옮긴다. 증거에 없는 숫자는 쓰지 않는다.
3. `update_all.ps1` 이 `verify_evidence.py` 로 항목의 금액·%·개월·인원·모델명·기간이 증거 원문에 있는지 자동 대조한다.
   - **일부 미확인** → 게시 중단(ERROR). `docs/VERIFY_CHECKLIST.md` 의 항목을 원문과 다시 비교해 고친다. 원문과 일치하는데 표기만 다른 경우(영문/한글 모델명 등)에만 `data/verify_ack.json` 에 **이유를 적어** 예외 승인한다.
   - **증거 없음** → 게시는 되지만 AI용 파일에 '원문 대조 안 됨'으로 표시된다. 증거 없는 브랜드를 다음 갱신 때 우선 채운다.
4. **독립 재확인(새 에이전트)**: 금액이 바뀐 항목(`docs/CHANGES.md`의 '금액·숫자 변경')과 새로 생긴 항목은, 수집한 에이전트가 아닌 **새 서브에이전트**에게 `data/evidence` 원문과 해당 항목 행만 주고 "숫자·조건·기간이 원문과 일치하는가"를 묻는다. 불일치가 있으면 고친 뒤 다시 실행한다.
5. 게시 후 `docs/CHANGES.md`(추가·삭제·금액 변경)를 종료 보고에 요약한다.

## 2.8 누적 이력과 월 전환 — 덮어쓰지 않는다
- `data/history/`(benefits_history.jsonl/.csv, snapshots, index.json)는 **절대 삭제·수정하지 않는다.** `update_all.ps1` 이 갱신 때마다 새 항목·변경·종료만 자동으로 덧붙인다(별도 작업 불필요).
- **새 달(매월 1~7일 첫 실행)**: 모든 브랜드를 새로 읽어 새 날짜 파일(`<브랜드>_YYYY-MM-DD.json`)로 저장하고, 이전 달 파일은 `data/archive/` 로 **옮긴다(삭제 금지)**. 기준월과 월별 프로모션 기간은 파일의 `captured` 날짜에서 자동 계산되므로 코드를 고치지 않는다. 이전 달에 있던 혜택이 새 달 페이지에서 사라지면 이력에 ended 로 기록된다.
- 수집 범위(구매 혜택: 할인·시승·금융)와 공식 페이지 원칙은 `docs/COLLECTION_GUIDE.md`. 범위 밖 서비스성 항목이 새로 나오면 `data/scope_exclude.json` 에 규칙을 추가한다.
- 과거 조회: `python -I scripts/query_history.py --ym YYYY-MM [--brand ...]`.

## 3. 검증·생성·게시
```
python -I scripts/verify.py data/sources.json   # (선택) URL 접속 점검
powershell -ExecutionPolicy Bypass -File scripts\update_all.ps1
```
`update_all.ps1`가 통합본(`data/unified`, `dist/car_db_for_ai.md`) 생성 → **품질 점검(`scripts/quality_check.py`)** → 통과하면 커밋·푸시·gist 갱신한다.
품질 점검에서 ERROR가 나오면 게시하지 않는다. `docs/QUALITY_REPORT.md`를 읽고 원본 JSON(`data/offers/`)이나 `build_db.py`를 고친 뒤 다시 실행한다. WARN은 게시하되 종료 보고에 적는다. 푸시 실패 시 오류를 사용자에게 보고(재시도 반복 금지).

## 4. 종료 보고
- 갱신한 브랜드 / 못 읽은 브랜드와 이유 / 기간 만료로 남은 항목 / 새로 생긴 이벤트(특히 시승 이벤트)를 5줄 이내로 요약.
