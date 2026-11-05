# car-db — 국내 신차 시승·할인·구매정보 DB

기준일: 2026-11-05 (수집 후 갱신 필요). 다른 AI가 읽도록 만든 폴더입니다. **처음 읽는 AI는 이 문서 → `data/unified/manifest.json` → 질문에 맞는 파일 순서로 보세요.**

## 한눈에
- 대상: 국내 판매 브랜드 37곳(국산 + 수입). 데이터가 있는 곳 35곳, 없는 곳: 타타대우(상용, 미수집), 혼다(자동차 철수 보도).
- 레코드 213건: benefit(혜택) 117 · price(가격) 52 · finance(금융) 19 · event(이벤트) 9 · status(점검결과) 12 · testdrive(시승) 4

## 파일 구조
| 경로 | 용도 |
|---|---|
| `data/unified/offers.jsonl` / `offers.csv` | **통합 레코드**(AI는 이것부터). 1줄=1레코드 |
| `data/unified/cardb.sqlite` | 같은 데이터의 SQLite (`records`, `brands` 테이블) |
| `data/unified/brands.json` | 브랜드별 공식 사이트·공식 금융사·수집 현황 |
| `data/unified/manifest.json` | 원본 파일별 레코드 수·한계(caveat) |
| `data/sources.json` | 브랜드·금융사 URL 마스터(검증 결과 포함) |
| `data/offers/*.json` | 브랜드별 원본(상세, 통합본에서 잘린 내용은 여기) |
| `data/testdrive/*.json` | 시승 정책 원본(기아·현대·제네시스·KGM) |
| `scripts/build_db.py` | 원본 → 통합본 재생성 |
| `scripts/verify.py` | sources.json URL 접속 검증 |
| `scripts/query_examples.py` | SQL 조회 예시 |

## 통합 레코드 필드
`id, brand_id, brand_ko, model, category, title, price_krw, max_benefit_krw, text, period_start, period_end, source_url, captured, confidence, note, raw_file`
- 금액은 **원 단위**. `price_krw`=차량/시작가, `max_benefit_krw`=페이지가 제시한 최대혜택(있는 브랜드만).
- `text`: 혜택 조건 요약(900자 제한). 전체는 `raw_file`의 원본 JSON.
- `confidence`: high(페이지에서 수치 직접 읽음) / medium(해석 필요·일부 라벨 모호) / low(상태·추정).
- `category=status`: 수치를 못 얻은 브랜드의 점검 결과(예: 벤츠 '전시장 문의', 푸조 프로모션 404).

## AI가 지켜야 할 주의사항
1. **기간을 확인하세요.** `period_*`가 비어 있으면 유효기간 불명. BMW는 페이지가 10월 프로모션 그대로(11월 만료 가능), 기아 기본혜택은 '26년 6~9월 생산분' 표기.
2. **가격은 보조금·세금 조건이 브랜드마다 다릅니다.** 테슬라는 보조금 미반영, 현대·제네시스는 시작가 기준, 기아는 '최다 판매 트림'.
3. 최대혜택은 조건 합산치(예: 지프 1,270만원=제휴금융 이용 시). 개인 조건에 그대로 적용 금지.
4. 벤츠·포르쉐·마세라티 등은 금액 비공개(딜러 문의) → 수치가 없는 것이지 혜택이 없다는 뜻이 아님.
5. 혼다·시트로엥·맥라렌·재규어는 국내 신차 판매 여부가 공식 확인되지 않음(철수/불확실).
6. 공식 사이트만 근거. 블로그·뉴스는 `sources`나 note에 '미확인'으로 표시.

## 갱신 방법
1. 브라우저(Chrome)로 `data/offers/<브랜드>_*.json`의 `source_url`을 다시 읽어 새 날짜 파일로 저장(이미지 페이지는 스크린샷으로 읽음. 기아·현대·BMW·KGM 등은 텍스트 DOM으로 충분).
2. `python -I scripts/build_db.py` 로 통합본 재생성.
3. `python -I scripts/verify.py data/sources.json` 로 URL 점검.

## 알려진 공백
푸조(네이버 스토어 프로모션), 쉐보레 일부 모델, 아우디 Q3 Sportback·A3·Q7·Q8, 랜드로버 나머지 모델, 지프 캐러셀 5건, 토요타 RAV4 상세, 폴스타 3 상세, 포르쉐 브랜드 사이트 혜택, KGM 시승 정책, 상용차(타타대우 등).
메일(뉴스레터) 연동은 아직 미구현 — 방향 미정.
