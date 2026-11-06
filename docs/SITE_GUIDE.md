# 사이트 가이드 — 브랜드별 주소, 이벤트 목록 위치, 읽는 방법, 확인 현황

기준일 2026-11-06. 주소는 이 날 실제로 열어 본 것이다. 사이트가 바뀌면 이 표부터 고친다.
"이벤트 목록 확인"이 ✅ 이면 그 목록의 진행 중 이벤트를 모두 DB와 대조했다는 뜻이다.

## 우선 브랜드 (판매량 순으로 처리. 10월 집계는 못 찾아 4월 국산차 집계와 수입차 일반 순위를 참고)
| 브랜드 | 구매혜택 페이지 | 이벤트 목록 | 확인 | 읽는 방법 / 메모 |
|---|---|---|---|---|
| 기아 | /kr/buy/special-offers | https://www.kia.com/kr/event/list | ✅ 9건 | 목록 항목은 링크가 없고 클릭하면 `/kr/event/detail?eventId=N`. 상세 본문은 **이미지**(innerText에는 제목·기간만) → 스크롤 스크린샷으로 읽음. 상세는 스토어 방문, 전용카드(eventId=575), 서울시 PV5 WAV(eventId=525) 3건만 읽음. 「The new Carnival」 보증연장·인증중고차 항목은 **외부 링크(↗)**라 클릭해도 목록에 머문다(미수집). RE100·비즈·더드림·세일 페스타는 목록만 |
| 현대 | /kr/ko/e/vehicles/monthly-benefit | https://www.hyundai.com/kr/ko/event | ✅ 34건 | 진행중 34건이 **3페이지**(12/12/10). 페이지 번호 버튼을 JS로 클릭해 읽음. 상세 URL은 `/kr/ko/event/event-<slug>`(목록 항목의 가장 가까운 `a` 태그 href, 쿼리 제거). **상세 본문은 텍스트**라 innerText로 읽힘(`모든회원` 다음부터). 할인·시승 핵심 10건(K-세일 페스타, 아반떼 퍼스트 무브, 트레이드인, 싼타페·팰리세이드 무이자, N-FINANCE 할부, EV 부담 DOWN, 전용카드, 트럭/버스, 시승 이벤트 2건)은 상세까지 수집. 나머지 20여 건(N-FINANCE 렌트/리스, EV 렌트/리스, 어드밴티지 프로그램, 제휴 이벤트 등)은 목록만 |
| 제네시스 | /kr/ko/shopping/monthly-offer.html | https://www.genesis.com/kr/ko/support/genesis-events.html | ✅ 7건 | 텍스트. 상세 `/support/genesis-events/detail/<id>.html`. 6건은 목록만 |
| 르노코리아 | /ko/buy/tm_purchasing.jsp | https://www.renault.co.kr/ko/inside/salesfesta_list.jsp | ✅ 4건 | 카드 목록(세일 페스타 금융·구매·시승, 티켓 이벤트). 카드를 클릭하면 `/ko/inside/event_view.jsp?t_seq=N`, 본문은 **이미지**. 모델 이벤트는 `/ko/model/<model>_event.jsp`(텍스트). 구매혜택은 '열기' 아코디언 |
| KGM | /od/promotion/monthly-benefits | 홈 배너 → `/br/news/event/<id>` | ✅ 시승 이벤트 | 이벤트 목록 주소는 못 찾음(홈 배너 클릭으로 진입). 상세는 텍스트. K-세일 페스타(~11/15) 배너도 있음(미수집) |
| 쉐보레 | /purchase/offers-faq.gm (텍스트), /events/… (이미지) | https://www.chevrolet.co.kr/past-events (지난 이벤트), 홈 배너 | △ | 진행 중 이벤트는 **홈 배너 텍스트**로 읽힘(겨울준비 무상점검 응모, 코리아 그랜드 페스티벌). 홈에 "최대 200만원 혜택"이 텍스트로 있어 이미지 페이지 값과 일치. 시승 이벤트는 8월 썸머 드라이브(종료)뿐. `/offers` 는 404 |
| 벤츠 | /passengercars/buy/new-car/promotion.html | /passengercars/brand/news-events.html | △ | 뉴스·이벤트 페이지는 2025년까지만 올라와 있음. 금액 비공개, 쿠키 배너 처리 필요. 신한카드·AMG 구매상담·개별소비세 이벤트는 수집됨 |
| BMW | /ko/finance/special-offer/financial-promotion.html | 목록 주소 못 찾음. 검색으로 개별 페이지 확인 | △ | 금융 프로모션(모델 7페이지, 기간 10월 표기 주의), 시승 `/ko/fastlane/tda-experience.html`. **BEV 멤버십**(`/ko/discover/bmw-bev-membership.html`, 상시 7일 시승) 수집. 네이버 특별 프로모션(bmwexperience.bmw.co.kr)은 "운영기간이 아닙니다", M FEST는 4월 종료. 서비스 프로모션(11/2~12/12 타이어·휠)은 검색 결과로만 확인(미수집) |
| 테슬라 | /ko_kr/modely/design 등 | https://www.tesla.com/events/tesla-special-test-drive-event 등 | △ | 가격은 스크린샷. 시승 `/ko_kr/drive`, 트레이드인 `/ko_kr/tradein`. 시승 이벤트 페이지는 "No upcoming events nearby". `/ko_kr/campaign/zero-drive`(다짐 공유 추첨, 11/21~25, 연도 미표기)는 미수집 |
| 렉서스 | /purchase-benefit/ (탭: 이달의 구매혜택·하이브리드 혜택·밸류플러스·어메이징 스위치) | 별도 목록 없음. 시승회는 월별 페이지 `/2026-oct-test-drive/`(예전엔 `/contents/2025-oct-test-drive/`) | △ | 글자 단위로 쪼개져 있어 공백 결합 필요. **`/event/` 등 아무 주소나 200을 돌려주므로(SPA) 상태코드로 존재 여부를 판단하지 말 것**(없는 페이지는 본문에 "요청하신 페이지를 찾을 수 없습니다"). 2026 가을 시승회는 응모 10/6~10/31로 종료(시승 ~11/3, 발표 11/10)해 만료 행으로 기록. 11월 시승회 `/2026-nov-test-drive/` 는 없음. 매달 `/YYYY-<mon>-test-drive/` 패턴을 확인할 것 |
| 아우디 | 모델 페이지(월 납입금 롤링 숫자) | `/ko/event/`, `/ko/event/taste-drive/` 는 지금 404 | ❌ | 검색 기준 최근 시승 이벤트는 2025-11, 여름 투어(7/6~8/31)는 종료. 현재 진행 이벤트 목록은 못 찾음. 홈 링크 추출 시 도구가 쿼리스트링 출력을 막음(LESSONS 참고) |
| 볼보 | volvocar.co.kr 의 family_repurchase, ex90-test-drive-campaign-nov | – | △ | volvocars.com/kr 아님. 재구매·시승 캠페인 수집 |
| 미니 | /ko_KR/home/offers/… | 못 찾음 | ❌ | 이달의 프로모션 페이지가 읽기 어려움. 상시 `MINI BEV MEMBERSHIP`(`/ko_KR/home/BEV_Membership.html`, 7일 시승) 수집. `/ko_KR/home/offers.html` 는 오류 페이지. 특별 혜택은 `/ko_KR/home/offers/special-offers/*.html`(검색에 나온 것은 JCW 2024년식, Gen Z Edition 등 날짜 불명 → 미수집). 검색 기준 2026-11 시승 이벤트 없음 |
| 토요타 | /benefit/monthly/ | /seasonal-event/, /test-drive/event/ | ✅ 시승 이벤트 | 텍스트 |
| 폭스바겐 | 모델 페이지 | /app/local/testdrive/event | △ | Golf R Roadshow(2월 시작, 종료일 미표기) |
| 포르쉐 | `dealer.porsche.com/kr/seongsu/ko-KR/Porsche-Financial-Service`(911·타이칸 금융 프로모션, 조건은 센터 문의) | 딜러사 사이트 `dealer.porsche.com/kr/<딜러>/ko-KR/News-and-Events` | △ | /sitemap.xml 에 이벤트 주소 없음. 이벤트는 딜러사별이라 딜러 전부는 못 봄. **`/korea/ko/taycanpromotion/` 은 2024년 2~6월 기간의 오래된 페이지라 넣지 않음.** Porsche Vibe Seoul(10월)은 종료. 금액 비공개 성격 |

## 그 외
- 캐딜락 `/campaign/…`, 랜드로버 `landroverkorea.co.kr/offers/`(월 납입금 롤링 숫자는 마지막 합산값만), 지프 `jeep.co.kr`, 폴스타 `polestar.com/kr/offers/…`, BYD `/brand/events`, 푸조(프로모션 404, 네이버 스토어 확인 필요), 포드·링컨(`flak.co.kr`, 현재 프로모션 없음) 등은 `data/offers/*.json` 의 `meta` 에 주소와 방법이 있다.
- 시승 신청 주소와 정책은 `data/testdrive/index.json`.

## 이벤트 목록을 찾는 요령 (홈페이지 링크가 안 나오는 사이트)
1. 홈페이지 `a` 태그에서 이벤트·프로모션·혜택·시승 단어를 찾는다(기아·현대·KGM·르노는 이걸로 충분).
2. 안 나오면 메뉴가 JS로 열리는 것이다. 스크린샷으로 메뉴를 눌러 들어간다(**주소 추측으로 `fetch`하면 SPA는 전부 200이라 속는다**).
3. `/sitemap.xml` 에 이벤트 주소가 있는지 본다(포르쉐는 없었다).
4. **웹 검색을 도메인 한정으로** 한다(예: `allowed_domains: bmw.co.kr`, 질의 "이벤트 진행중 시승"). 개별 이벤트 페이지 주소가 나오면 그 페이지를 직접 열어 확인한다(BMW BEV 멤버십, 쉐보레 지난 이벤트가 이렇게 나왔다). 검색 요약문의 날짜·금액은 근거로 쓰지 말고 반드시 페이지를 열어 읽는다.
5. 홈페이지 본문 텍스트에도 배너 형태로 진행 중 이벤트가 있는 경우가 있다(쉐보레 홈).
6. 그래도 못 찾으면 "확인 못 함"으로 `status` 에 남기고 넘어간다. "이벤트 없음"이라고 쓰지 않는다.
