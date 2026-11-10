"""오프라인 AI용 패키지 생성: dist/car_db_for_ai.md (단일 파일) + dist/car-db-bundle.zip
실행: python -I scripts/export_bundle.py   (build_db.py 실행 후)
"""
import json, os, re, zipfile, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, "data", "unified")
DIST = os.path.join(ROOT, "dist")
os.makedirs(DIST, exist_ok=True)

recs = [json.loads(l) for l in open(os.path.join(U, "offers.jsonl"), encoding="utf-8")]
brands = json.load(open(os.path.join(U, "brands.json"), encoding="utf-8"))
man = json.load(open(os.path.join(U, "manifest.json"), encoding="utf-8"))

def won(n):
    if n is None:
        return None
    return f"{n/10000:,.0f}만원"

by = collections.OrderedDict()
for b in brands:
    by[b["id"]] = []
for r in recs:
    by.setdefault(r["brand_id"], []).append(r)
order = {"price": 0, "benefit": 1, "finance": 2, "event": 3, "testdrive": 4, "status": 5}

L = []
L.append("# 국내 신차 시승·할인·구매정보 DB (오프라인 단일 파일)\n")
L.append(f"- 기준일: {max((r.get('captured') or '') for r in recs)} 수집 / 생성 {datetime.date.today().isoformat()} / 레코드 {len(recs)}건 / 브랜드 {len(brands)}곳")
L.append("- 출처: 각 브랜드 공식 홈페이지·공식 금융사 (수집 당시 화면). 인터넷 없이 이 파일만으로 답하세요.")
L.append("- **데이터 수집 방법·정책·사이트 가이드·검증 방식은 이 파일 맨 끝 '부록: 데이터 수집 가이드'에 있습니다.**")
L.append("- **과거 월 혜택은 같은 gist 의 `benefits_history.csv`(누적)에 있습니다.** 이 파일은 현재 월 기준이며, 월별 목차와 조회 규칙은 '월별 혜택 이력' 절에 있습니다.\n")
L.append("## AI 사용 지침")
L.append("1. 답할 때 **브랜드·모델·수치·기간**을 이 파일에서 그대로 인용하고, 없으면 '이 DB에 없음'이라고 말하세요. 추측 금지.")
L.append("2. 금액 단위: 만원(표기 그대로). 최대혜택은 조건 합산치(제휴금융 이용 등)이므로 개인 조건에 그대로 적용하지 말 것.")
L.append("3. **유효기간 주의**: BMW는 10월 프로모션(11월 만료 가능), 기아 기본혜택은 '26년 6~9월 생산분'. 기간이 없으면 '기간 불명' 명시.")
L.append("4. 벤츠·포르쉐·마세라티 등은 금액 비공개(딜러 문의)이며 '혜택 없음'이 아님.")
L.append("5. 혼다·시트로엥·맥라렌·재규어는 국내 신차 판매 여부 불확실.")
L.append("6. `[신뢰도]` high=페이지에서 수치 직접 확인, medium=해석 필요, low=점검 결과/추정.")
L.append("7. **같은 달 안에서도 종료일이 이 파일의 '생성' 날짜보다 앞서면 이미 끝난 이벤트**입니다(기간상태가 '기준월 해당'이어도). '지금 받을 수 있는' 혜택을 물으면 종료일이 오늘 이후이거나 기간 미표기인 것만 안내하세요.\n")

# 월별 혜택 (정규화): 이 DB의 핵심 목적
bp = os.path.join(U, "benefits.jsonl")
ben = [json.loads(l) for l in open(bp, encoding="utf-8")] if os.path.exists(bp) else []
if ben:
    ym = max(b["ym"] for b in ben if b.get("ym"))
    L.append(f"## 월별 혜택 ({ym} 기준)")
    L.append("- 항목마다 유형(할인/금융/증정/시승혜택/이벤트/보증·서비스), 차종·세부모델, 할인·금융 내용, 조건, 증정·경품, 기간, 링크를 적었습니다.")
    L.append("- `기간 상태`: 기준월 해당 / 기간 만료 / 시작 전 / 기간 미표기. **기간 만료는 지금 받을 수 있는 혜택이 아닙니다.**")
    L.append("- 할인·조건·증정 칸은 원문 문장을 키워드로 나눈 값이라 틀릴 수 있습니다. 정확한 금액과 조건은 '세부내용'과 링크 기준으로 답하세요.")
    L.append("- `검증`: 항목의 금액·%·개월·모델명·기간이 수집한 공식 페이지 원문에 실제로 있는지 자동 대조한 결과입니다. '원문 대조 완료'만 금액을 확정해서 말해도 됩니다. '원문 대조 안 됨'이면 \"공식 페이지에서 확인 필요\"라고 함께 안내하세요.\n")
    # ---- 표 형태(한 줄 = 혜택 하나). AI가 표를 만들어 달라는 요청에 이 열 구성을 그대로 쓰도록 한다
    def cell(v, n=110):
        s = "" if v is None else str(v)
        s = re.sub(r"\s+", " ", s).replace("|", "/").strip()
        return (s[:n] + "…") if len(s) > n else (s or "-")
    # ---- 표 작성 규칙: 다른 AI가 같은 표를 같은 방식으로 만들도록 열 정의·필터·정렬·예시를 못 박는다
    ex = next((x for x in ben if x["brand_id"] == "toyota" and x.get("model") == "CAMRY"), None)
    L.append("### 표 작성 규칙 (표·행·목록을 요청받으면 반드시 이 규칙대로)")
    L.append("1. **열 정의**: 아래 '유형별 혜택 표'(표 A 구매/표 B 금융/표 C 시승)의 열이 기준입니다. 열 이름·순서를 바꾸지 말고, 표를 새로 계산하거나 요약하지 말고 **해당 행을 그대로 복사**하세요. 빈 칸은 '-'.")
    L.append("2. **열 뜻**: 모델·세부모델=차량 이름만 / 연식=모델 연식 / 이벤트명=프로그램·행사 이름만(차량 이름 아님) / 유형=할인·금융·증정·시승혜택·이벤트·보증·서비스(여러 개 가능) / 할인구분=정액 할인·정률 할인·정액+정률 할인·금융 조건·할인 없음 / 할인금액(만원)=선택지 중 최대 정액 / 할인율(%)=선택지 중 최대 정률 / 할인 내용=선택지 전체 원문 / 시작·종료=혜택 기간(없으면 '-').")
    L.append("3. **필터 말뜻**: '모델이 선택된(지정된) 행' = 모델 열이 '-'가 아닌 행 / '브랜드 전체 이벤트' = 모델 열이 '-'인 행 / '할인 혜택' = 할인구분이 '정액 할인'·'정률 할인'·'정액+정률 할인'인 행 / '지금 받을 수 있는' = 기간상태가 '기간 만료'가 아닌 행 / '검증된' = 검증 열이 '검증됨'인 행.")
    L.append("4. **정렬**: 요청이 없으면 ID 순서(=브랜드 가나다·모델 순)를 유지. '할인 큰 순'이면 할인금액(만원) 내림차순(비어 있는 행은 맨 뒤), '할인율 순'이면 할인율(%) 내림차순.")
    L.append("5. **금지**: 값을 추정해 채우기, 금액 합산·평균·대표값 만들기, 없는 열 추가, 이 파일에 없는 브랜드·모델 언급. 값이 없으면 '이 DB에 없음'.")
    L.append("6. **검증 열**: '검증됨'만 금액을 확정해서 말해도 됩니다. '원문 대조 안 됨'이면 표 아래에 \"공식 페이지(링크 열)에서 확인 필요\"를 붙이세요.")
    L.append("### 유형별 혜택 표 — 구매 혜택 / 금융 혜택 / 시승 혜택 (한 줄 = 혜택 하나)")
    L.append("- **표를 요청받으면 아래 해당 표의 열 이름·열 순서·셀 값을 그대로 복사해서 보여주세요. 값을 바꾸거나 요약하거나 다른 열을 추가·삭제하지 마세요.** 비어 있는 칸은 '-'입니다.")
    L.append("- 요청 유형 → 표: '할인·증정·이벤트·구매 혜택' = 표 A / '금융·할부·리스·금리·월 납입금' = 표 B / '시승' = 표 C. 한 혜택이 여러 유형이면 여러 표에 같은 ID로 나옵니다(ID 는 모든 표에서 같음).")
    L.append("- '모델이 선택된 행' = 모델 칸이 '-'가 아닌 행, 모델 칸이 '-'이면 브랜드 전체 이벤트. 모델·세부모델에는 차량 이름만, 이벤트명에는 프로그램 이름만 있습니다. 할인금액(만원)·할인율(%)은 선택지가 여러 개면 가장 큰 값입니다(전체는 '할인 내용').")
    L.append("- 금융 표의 '월 납입금'·'금리'는 금융사 공식 페이지에 적힌 예시/범위 그대로이며, 개인 신용·선수금에 따라 달라집니다. 값이 없으면 공식 페이지에 텍스트로 없다는 뜻입니다.\n")
    vmap = {"검증됨": "검증됨", "일부 미확인": "불일치(확인 필요)", "증거 없음": "원문 대조 안 됨"}
    man = lambda v: f"{v / 10000:g}" if v else None
    pct = lambda v: f"{v:g}" if v else None
    base = [("ID", "id"), ("브랜드", "brand_ko"), ("모델", "model"), ("세부모델", "sub_model"), ("이벤트명", "event_name")]
    tail = [("시작", "period_start"), ("종료", "period_end"), ("기간상태", "period_status"), ("링크", "link"), ("검증", lambda b: vmap.get(b.get("verification"), "-"))]
    TB = [
        ("표 A. 구매 혜택 (할인·증정·이벤트)", lambda x: any(t in (x.get("types") or "") for t in ("할인", "증정", "이벤트", "기타")) or not any(t in (x.get("types") or "") for t in ("금융", "시승")),
         base + [("유형", "types"), ("할인구분", "discount_type"), ("할인금액(만원)", lambda b: man(b.get("discount_amount_krw"))), ("할인율(%)", lambda b: pct(b.get("discount_rate_pct"))), ("할인 내용", "discount"), ("조건", "conditions"), ("증정·경품", "reward"), ("대상", "target_scope")] + tail),
        ("표 B. 금융 혜택 (캐피탈·금융사 상품 포함)", lambda x: "금융" in (x.get("types") or "") or bool(x.get("finance_product")),
         base + [("금융사", "finance_company"), ("상품", "finance_product"), ("금리", "finance_rate"), ("기간", "finance_term"), ("선수율", "finance_down"), ("월 납입금 예시", "finance_monthly"), ("차량가(만원)", lambda b: man(b.get("vehicle_price_krw"))), ("조건", "conditions"), ("대상", "target_scope")] + tail),
        ("표 C. 시승 혜택", lambda x: "시승" in (x.get("types") or ""),
         base + [("제목", "title"), ("혜택", "reward"), ("조건", "conditions"), ("대상", "target_scope")] + tail),
    ]
    for tname, pred, spec in TB:
        sel = [b for b in ben if pred(b)]
        L.append(f"#### {tname} — {len(sel)}행")
        L.append("| " + " | ".join(h for h, _ in spec) + " |")
        L.append("|" + "---|" * len(spec))
        for b in sel:
            L.append("| " + " | ".join(cell(f(b) if callable(f) else b.get(f), 1500) for _, f in spec) + " |")
        L.append("")
    L.append("\n### 브랜드별 상세 (조건·증정·세부내용 전체)")
    grp = collections.OrderedDict()
    for b in ben:
        grp.setdefault(b["brand_ko"], []).append(b)
    for name, items in grp.items():
        L.append(f"### {name}")
        for b in items:
            who = " / ".join(x for x in [b.get("model"), b.get("sub_model")] if x) or b.get("target_scope") or "브랜드 공통"
            if b.get("model_year"):
                who += f" ({b['model_year']}년식)"
            per = f"{b['period_start'] or '?'}~{b['period_end'] or '?'}" if (b.get("period_start") or b.get("period_end")) else "기간 미표기"
            vtag = {"검증됨": "원문 대조 완료", "일부 미확인": "원문 대조 불일치(확인 필요)", "증거 없음": "원문 대조 안 됨"}.get(b.get("verification"), "")
            L.append(f"- **[{b['types']}] 이벤트명: {b['event_name']}** — 차종: {who} | 기준 {b['ym']} | 기간 {per} ({b['period_status']}) | 검증: {vtag}")
            dm = []
            if b.get("discount_amount_krw"):
                dm.append(f"최대 할인금액 {b['discount_amount_krw'] / 10000:g}만원")
            if b.get("discount_rate_pct"):
                dm.append(f"최대 할인율 {b['discount_rate_pct']:g}%")
            L.append(f"  - 할인 구분: {b.get('discount_type')}" + (" | " + ", ".join(dm) if dm else ""))
            if b.get("discount_options"):
                L.append(f"  - 할인 선택지(전체): {b['discount_options']}")
            # 할인 내용·조건·증정은 위 표에 전체가 있으므로 여기서는 세부내용(원문 풀이)만 싣는다
            L.append(f"  - 세부내용: {(b['detail'] or '')[:700]}")
        L.append("")

# 요약표: 현재 가격/최대혜택 있는 것
L.append("## 참고: 가격·최대혜택 숫자가 있는 레코드 (가격은 참고 정보)")
L.append("| 브랜드 | 모델 | 가격 | 최대혜택 | 비고 |")
L.append("|---|---|---|---|---|")
for r in recs:
    if r["price_krw"] or r["max_benefit_krw"]:
        nm = r['title'] if (not r['model'] or r['model'] in r['title']) else f"{r['model']} {r['title']}"
        nm = nm.replace(" 월 납입금(만원/월)", "")
        L.append(f"| {r['brand_ko']} | {nm} | {won(r['price_krw']) or '-'} | {won(r['max_benefit_krw']) or '-'} | {(r['note'] or '')[:40]} |")
L.append("")

tdp = os.path.join(U, "testdrive.json")
if os.path.exists(tdp):
    td = json.load(open(tdp, encoding="utf-8"))
    L.append("## 시승 정보 (신청 가능 여부 / 시승 이벤트 구분)")
    L.append("- 신청 가능 = 공식 사이트에 온라인 시승 신청 경로가 있음. 시승 이벤트 = 시승(완료)과 직접 연결된 혜택. 정책 상세 수집 정도는 detail_level 참조(full/partial/url_only/none).\n")
    L.append("### A. 온라인 시승 신청 가능한 브랜드")
    L.append("| 브랜드 | 신청 주소 | 신청 가능 모델 | 정책/비고 | 수집 정도 |")
    L.append("|---|---|---|---|---|")
    for t in td:
        if t["can_apply_online"]:
            L.append(f"| {t['brand_ko']} | {t['apply_url']} | {(t['models'] or '-')[:60]} | {(t['policy'] or '-')[:90]} | {t['detail_level']} |")
    L.append("\n### B. 시승 이벤트/시승 혜택이 있는 브랜드")
    L.append("| 브랜드 | 이벤트 | 혜택 | 기간 | 상세 수집 | 출처 |")
    L.append("|---|---|---|---|---|---|")
    for t in td:
        if t["has_event"]:
            L.append(f"| {t['brand_ko']} | {t['event_name']} | {t['event_benefit']} | {t['event_period'] or '기간 불명'} | {'예' if t['event_detail_collected'] else '아니오(부분)'} | {t['event_url']} |")
    L.append("\n### C. 온라인 시승 신청 경로를 확인하지 못했거나 없는 브랜드")
    L.append(", ".join(f"{t['brand_ko']}({'없음' if t['can_apply_online'] is False else '미확인'})" for t in td if not t["can_apply_online"]))
    L.append("")

L.append("## 브랜드별 상세")
for bid, rs in by.items():
    b = next(x for x in brands if x["id"] == bid) if any(x["id"] == bid for x in brands) else None
    name = b["brand_ko"] if b else bid
    L.append(f"\n### {name} ({bid})")
    if b:
        fin = "; ".join(f"{f['name']} {f.get('url') or ''}".strip() for f in (b.get("finance") or []))
        L.append(f"- 공식 사이트: {b.get('site')} / 금융사: {fin or '-'}" + (f" / 비고: {b.get('note') or b.get('status')}" if (b.get('note') or b.get('status')) else ""))
    if not rs:
        L.append("- (수집 데이터 없음)")
        continue
    for r in sorted(rs, key=lambda x: order.get(x["category"], 9)):
        if ben and r["category"] in ("benefit", "finance", "event"):
            continue  # 혜택류는 위 '월별 혜택' 섹션에 정리돼 있음
        parts =[f"[{r['category']}][{r['confidence']}] {r['title']}"]
        if r["price_krw"]:
            parts.append(f"가격 {won(r['price_krw'])}")
        if r["max_benefit_krw"]:
            parts.append(f"최대혜택 {won(r['max_benefit_krw'])}")
        if r["period_start"] or r["period_end"]:
            parts.append(f"기간 {r['period_start'] or '?'}~{r['period_end'] or '?'}")
        L.append("- " + " | ".join(parts))
        if r["text"]:
            L.append(f"  - {r['text']}")
        if r["note"]:
            L.append(f"  - 비고: {r['note']}")
        if r["source_url"]:
            L.append(f"  - 출처: {r['source_url']}")

# 월별 이력 목차 + 과거 월 조회 방법 (이 파일의 월별 혜택 표는 '현재 월'만, 과거는 benefits_history.csv 에 누적)
hp = os.path.join(ROOT, "data", "history", "benefits_history.jsonl")
if os.path.exists(hp):
    import calendar
    hist = [json.loads(l) for l in open(hp, encoding="utf-8") if l.strip()]
    byk = collections.defaultdict(list)
    for h_ in hist:
        byk[h_["key"]].append(h_)
    vers = []
    for k_, vs_ in byk.items():
        vs_.sort(key=lambda x: x["valid_from"])
        for i_, v_ in enumerate(vs_):
            vers.append(dict(v_, valid_to=vs_[i_ + 1]["valid_from"] if i_ + 1 < len(vs_) else (v_["valid_from"] if v_["change"] == "ended" else "")))
    cands = [m_ for m_ in ((v_.get("period_start") or "")[:7] for v_ in vers) if m_] + [v_["valid_from"][:7] for v_ in vers]
    if cands:
        y0, m0 = map(int, min(cands).split("-")); y1, m1 = map(int, max(cands).split("-"))
        L.append("\n---\n")
        L.append("## 월별 혜택 이력 (과거 월 조회)")
        L.append("- **이 파일의 '월별 혜택 표'는 현재 월 혜택만** 담습니다. 과거 월 혜택은 같은 gist 의 **`benefits_history.csv`**(누적, 지우지 않음)에 있습니다. 과거 월을 물으면 그 파일을 기준으로 답하세요.")
        L.append("- `benefits_history.csv` 열: key, change(new 처음 관측/changed 내용 변경/ended 사라짐/expired 기간 지난 채 관측), valid_from(이 버전을 처음 본 날), valid_to(다음 버전을 본 날, 비면 현재), row_status, ym(수집 월), period_month, 브랜드·모델·세부모델·이벤트명·할인 열, 기간, 링크, 검증.")
        L.append("- **월 판단 규칙**: 공식 기간(period_start~period_end)이 있으면 그 기간이 해당 월과 겹치는 항목이 그 월의 혜택. 기간이 없으면 우리가 관측한 구간(valid_from~valid_to)이 그 월과 겹치는 항목. 같은 항목의 여러 버전(change=changed)은 그 월 말 시점에 유효했던 하나만 봅니다. ended 행은 혜택이 아니라 '사라진 시점' 표시입니다.")
        first_obs = min(v_["valid_from"][:7] for v_ in vers)
        L.append(f"- 이력은 매주 일요일 갱신 때마다 새 항목·변경·종료만 덧붙입니다(덮어쓰기 없음). **수집·누적은 {first_obs}부터 시작**했습니다. 그 이전 월에는 공식 기간이 그 달부터 이어지는 장기 이벤트만 잡혀 있어 **완전하지 않습니다**(예: 10월 BMW 금융 프로모션처럼 기간이 지난 채 관측된 것은 기간 기준으로 해당 월에 잡힘).\n")
        L.append("| 월 | 해당 월 혜택 항목 수 | 브랜드 수 | 비고 |")
        L.append("|---|---|---|---|")
        y, m = y0, m0
        while (y, m) <= (y1, m1):
            lo_, hi_ = f"{y}-{m:02d}-01", f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"
            seen_ = {}
            for v_ in vers:
                if v_["change"] == "ended":
                    continue
                if v_.get("period_start") or v_.get("period_end"):
                    ok_ = (v_.get("period_start") or "0000-00-00") <= hi_ and (v_.get("period_end") or "9999-99-99") >= lo_
                else:
                    ok_ = v_["valid_from"] <= hi_ and (not v_["valid_to"] or v_["valid_to"] >= lo_)
                if ok_:
                    seen_[v_["key"]] = v_.get("brand_ko")
            L.append(f"| {y}-{m:02d} | {len(seen_)} | {len(set(seen_.values()))} | {'수집 시작 전: 기간이 이어진 장기 이벤트만(불완전)' if f'{y}-{m:02d}' < first_obs else ('수집 중' if f'{y}-{m:02d}' == first_obs else '')} |")
            m += 1
            if m > 12:
                y, m = y + 1, 1

# 부록: 수집 방법·정책·사이트 가이드 (웹 접속이 안 되는 AI도 읽을 수 있게 같은 파일에 싣는다)
APPX = [("PROGRESS_SUMMARY.md", "작업 요약 — 무엇을 어떻게 만들었고 지금 어디까지 왔는지"),
        ("COLLECTION_GUIDE.md", "수집 가이드 — 정책, 데이터 규칙, 검증, 누적 이력"),
        ("SITE_GUIDE.md", "사이트 가이드 — 브랜드별 주소·읽는 방법·확인 현황"),
        ("HANDOFF.md", "인수인계 — 목적, 파일 지도, 이어서 작업하는 법, 남은 일"),
        ("LESSONS.md", "작업하며 얻은 지식 — 사용자 선호, 실수와 교훈, 도구 함정")]
L.append("\n---\n")
L.append("# 부록: 데이터 수집 가이드 (이 DB를 어떻게 모으고 검증했는지)")
L.append("- 아래는 저장소 `docs/` 문서를 그대로 옮긴 것입니다. 혜택이 어디서 왔는지, 어떤 규칙으로 정리했는지, 어떻게 검증했는지 물으면 이 부록으로 답하세요.\n")
for fn_, title_ in APPX:
    p_ = os.path.join(ROOT, "docs", fn_)
    if not os.path.exists(p_):
        continue
    L.append(f"\n## 부록 · {title_}\n")
    for ln in open(p_, encoding="utf-8").read().splitlines():
        L.append(("##" + ln) if ln.startswith("#") else ln)

md = os.path.join(DIST, "car_db_for_ai.md")
open(md, "w", encoding="utf-8").write("\n".join(L) + "\n")

# zip
zp = os.path.join(DIST, "car-db-bundle.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(md, "car_db_for_ai.md")
    z.write(os.path.join(ROOT, "README.md"), "README.md")
    for rel in ["data/unified/offers.csv", "data/unified/offers.jsonl", "data/unified/brands.json", "data/unified/manifest.json", "data/unified/cardb.sqlite", "data/sources.json"]:
        z.write(os.path.join(ROOT, rel), rel)
    for sub in ("offers", "testdrive"):
        d = os.path.join(ROOT, "data", sub)
        for f in sorted(os.listdir(d)):
            z.write(os.path.join(d, f), f"data/{sub}/{f}")
    for f in ("build_db.py", "export_bundle.py", "verify.py", "query_examples.py"):
        z.write(os.path.join(ROOT, "scripts", f), f"scripts/{f}")
print("md chars:", os.path.getsize(md), "zip bytes:", os.path.getsize(zp))
