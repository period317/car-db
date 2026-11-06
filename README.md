# car-db — 국내 신차 시승·할인·구매정보 DB

기준일: 2026-11-06 (수집 후 갱신 필요). 다른 AI가 읽도록 만든 폴더입니다.
- **이어서 수집하려는 AI(웹 접속 가능)**: `docs/HANDOFF.md` → `docs/COLLECTION_GUIDE.md` → `docs/SITE_GUIDE.md` → `docs/LESSONS.md` 순서로 읽으세요.
- **데이터를 읽기만 하는 AI**: 이 문서 → `dist/car_db_for_ai.md`(맨 위에 표 작성 규칙) → 필요하면 `data/unified/benefits.csv`.

## 한눈에
- 이 DB의 목적은 **월별 혜택**(할인·이벤트·금융 프로모션·시승 혜택)입니다. 가격은 참고 정보입니다.
- 대상: 국내 판매 브랜드 37곳(국산 + 수입). 데이터가 있는 곳 35곳, 없는 곳: 타타대우(상용, 미수집), 혼다(자동차 철수 보도).
- 월별 혜택 205건(2026-11 기준), 통합 레코드 273건. 이벤트 목록 전수 확인은 기아·현대·제네시스·르노까지 했고 나머지는 `docs/SITE_GUIDE.md` 의 확인 현황 참고.
- 각 혜택은 `원문 대조 완료`/`원문 대조 안 됨` 표시가 붙습니다(공식 페이지 원문 `data/evidence/` 와 자동 대조).

## 파일 구조
| 경로 | 용도 |
|---|---|
| `data/unified/benefits.jsonl` / `benefits.csv` / `benefits.json` | **월별 혜택 정리본**(핵심). 기준년월·차종·세부모델·유형·할인/조건/증정·기간 상태·링크 |
| `docs/QUALITY_REPORT.md` | 수집 후 품질 점검 결과(ERROR가 있으면 게시 중단) |
| `data/unified/offers.jsonl` / `offers.csv` | 통합 레코드(가격·점검결과 포함 원자료). 1줄=1레코드 |
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

## 자동 갱신 · 다른 PC 동기화
- 저장소: https://github.com/period317/car-db (공개)
- **수집 PC(Claude)**: 예약 작업 `car-db-weekly-refresh`가 매주 일요일 오전 10시경 `docs/REFRESH_PLAYBOOK.md`대로 공식 사이트를 다시 읽고 `scripts/update_all.ps1`로 커밋·푸시. (PC가 켜져 있고 Claude 앱이 실행 중이어야 함. 꺼져 있으면 다음 실행 때 수행)
- **다른 PC(자동 내려받기)**
  - git 있는 PC: 한 번만 실행 → 이후 매일 자동 `git pull`
    `powershell -ExecutionPolicy Bypass -File setup_other_pc.ps1 -RepoUrl https://github.com/period317/car-db.git -Target C:\car-db -Time 09:00` (저장소의 `sync/` 폴더 파일)
  - git 없는 PC: `sync/sync_download.ps1 -Owner period317 -Repo car-db` (최신 md·csv만 ZIP으로 내려받음)
  - AI에게 읽힐 파일: `C:\car-db\dist\car_db_for_ai.md` (시승 정보 포함 단일 파일)
- 직접 주소(인터넷 되는 AI/도구용):
  - https://raw.githubusercontent.com/period317/car-db/main/dist/car_db_for_ai.md
  - https://raw.githubusercontent.com/period317/car-db/main/data/unified/offers.csv
  - https://raw.githubusercontent.com/period317/car-db/main/data/unified/testdrive.csv
- 갱신이 필요한 곳 점검: `python -I scripts/check_stale.py`

## 시승 정보 읽는 법
`data/unified/testdrive.csv|json`: 브랜드당 1행. `can_apply_online`(온라인 신청 가능), `apply_url`, `models`, `policy`, `has_event`(시승 이벤트/혜택), `event_*`, `detail_level`(full/partial/url_only/none).

## 알려진 공백
푸조(네이버 스토어 프로모션), 쉐보레 일부 모델, 아우디 Q3 Sportback·A3·Q7·Q8, 랜드로버 나머지 모델, 지프 캐러셀 5건, 토요타 RAV4 상세, 폴스타 3 상세, 포르쉐 브랜드 사이트 혜택, KGM 시승 정책, 상용차(타타대우 등).
메일(뉴스레터) 연동은 아직 미구현 — 방향 미정.
