# 주기 갱신 플레이북 (Claude가 예약 실행할 때 따르는 절차)

목표: 공식 사이트에서 최신 혜택·가격·시승 정보를 다시 읽어 `data/`를 갱신하고, 통합본을 만든 뒤 GitHub에 올린다.
작업 폴더: `car-db/` (이 파일의 상위). 브라우저는 Claude in Chrome(실제 Chrome) 사용.

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

## 3. 검증·생성·게시
```
python -I scripts/verify.py data/sources.json   # (선택) URL 접속 점검
powershell -ExecutionPolicy Bypass -File scripts\update_all.ps1
```
`update_all.ps1`가 통합본(`data/unified`, `dist/car_db_for_ai.md`) 생성 → 변경 있으면 커밋 → 푸시한다. 푸시 실패 시 오류를 사용자에게 보고(재시도 반복 금지).

## 4. 종료 보고
- 갱신한 브랜드 / 못 읽은 브랜드와 이유 / 기간 만료로 남은 항목 / 새로 생긴 이벤트(특히 시승 이벤트)를 5줄 이내로 요약.
