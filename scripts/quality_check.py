"""수집 후 품질 점검. 사용: python -I scripts/quality_check.py
- 통합본(data/unified)을 읽어 규칙 위반을 ERROR / WARN / INFO 로 분류한다.
- 결과: data/unified/quality_report.json (기계용), docs/QUALITY_REPORT.md (사람용)
- ERROR 가 하나라도 있으면 종료 코드 1 (update_all.ps1 이 push 를 막는다).
- 직전 실행 결과와 비교해 레코드 급감, 브랜드 데이터 소실도 잡는다.
"""
import json, os, re, sys, datetime, collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, "data", "unified")
TODAY = datetime.date.today()

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8-sig") if l.strip()]

recs = load_jsonl(os.path.join(U, "offers.jsonl"))
td = json.load(open(os.path.join(U, "testdrive.json"), encoding="utf-8-sig"))
brands = json.load(open(os.path.join(U, "brands.json"), encoding="utf-8-sig"))
brand_ids = {b["id"] for b in brands}
prev_path = os.path.join(U, "quality_report.json")
prev = json.load(open(prev_path, encoding="utf-8")) if os.path.exists(prev_path) else None

CATS = {"benefit", "price", "finance", "event", "status", "testdrive"}
CONF = {"high", "medium", "low"}
RAW_KEYS = {"offers", "models", "promotions", "programs", "events", "finance_promotion", "common_warranty", "finance_example"}
BAD_MODEL_WORDS = ("점검", "결과", "미수집", "없음", "offers", "models", "promotions")
MODEL_REQUIRED = {"price"}  # 가격 레코드는 반드시 모델이 있어야 한다

issues = []  # (level, rule, id, brand, message)

def add(level, rule, r, msg):
    issues.append(dict(level=level, rule=rule, id=r.get("id"), brand=r.get("brand_ko") or r.get("brand_id"), message=msg))

def parse_date(s):
    try:
        return datetime.date.fromisoformat(s)
    except Exception:
        return None

seen = collections.defaultdict(list)
for r in recs:
    rid = r["id"]; title = r.get("title") or ""; model = r.get("model")
    # 필수값
    for f in ("brand_ko", "title", "category", "source_url", "captured"):
        if not r.get(f):
            # 국내 공식 사이트가 없는 브랜드의 '점검결과'는 출처가 없을 수 있다
            lvl = "WARN" if (f == "source_url" and r.get("category") == "status") else "ERROR"
            add(lvl, "required-field", r, f"{f} 비어 있음")
    if r.get("category") not in CATS:
        add("ERROR", "bad-category", r, f"알 수 없는 category: {r.get('category')}")
    if r.get("confidence") not in CONF:
        add("ERROR", "bad-confidence", r, f"알 수 없는 confidence: {r.get('confidence')}")
    # 제목·모델 이름 위생 (원본 JSON 키가 새는 문제)
    if title in RAW_KEYS or re.fullmatch(r"[a-z_]+", title) or re.match(r"^[a-z_]+ 점검 결과$", title):
        add("ERROR", "raw-key-title", r, f"제목이 내부 키/영문 ID: '{title}'")
    if model and any(w in model for w in BAD_MODEL_WORDS):
        add("ERROR", "bad-model-name", r, f"모델명에 상태/키 문구: '{model}'")
    if model and len(model) > 60:
        add("WARN", "long-model-name", r, f"모델명이 너무 김({len(model)}자): '{model[:40]}…'")
    if r["category"] in MODEL_REQUIRED and not model:
        add("ERROR", "price-without-model", r, "가격 레코드에 모델이 없음")
    # 깨진 글자
    blob = " ".join(str(r.get(k) or "") for k in ("title", "model", "text", "note"))
    if "�" in blob:
        add("ERROR", "mojibake", r, "깨진 글자(�) 포함")
    # 금액
    p, m = r.get("price_krw"), r.get("max_benefit_krw")
    if p is not None and not (3_000_000 <= p <= 500_000_000):
        add("ERROR", "price-range", r, f"가격이 상식 범위 밖: {p:,}원 (단위 오류 의심)")
    if m is not None and p:
        if m > p:
            add("ERROR", "benefit-gt-price", r, f"최대혜택 {m:,} > 가격 {p:,}")
        elif m / p > 0.35:
            add("WARN", "benefit-ratio-high", r, f"최대혜택이 가격의 {m / p:.0%}: 단위·조건 확인")
    if m is not None and p is None:
        add("WARN", "benefit-without-price", r, "최대혜택은 있는데 가격이 없어 할인율 계산 불가")
    # 출처·기간
    if r.get("source_url") and not str(r["source_url"]).startswith("http"):
        add("WARN", "bad-source-url", r, f"출처 URL 형식 이상: {r['source_url']}")
    ps, pe = parse_date(r.get("period_start") or ""), parse_date(r.get("period_end") or "")
    if ps and pe and pe < ps:
        add("ERROR", "period-order", r, f"종료일이 시작일보다 앞섬: {ps}~{pe}")
    if pe and pe < TODAY and r["category"] in ("benefit", "finance", "event"):
        add("WARN", "expired", r, f"기간 만료: {pe}")
    cap = parse_date(r.get("captured") or "")
    if cap:
        age = (TODAY - cap).days
        if age > 30:
            add("ERROR", "stale-30d", r, f"수집 후 {age}일 경과")
        elif age > 14:
            add("WARN", "stale-14d", r, f"수집 후 {age}일 경과")
    if r["category"] in ("benefit", "finance", "event") and not (r.get("text") or "").strip() and m is None:
        add("WARN", "empty-detail", r, "혜택 내용(text)과 금액이 모두 비어 있음")
    seen[(r.get("brand_id"), model, r.get("category"), title)].append(rid)

for k, ids in seen.items():
    if len(ids) > 1:
        add("WARN", "duplicate", {"id": ids[0], "brand_id": k[0]}, f"같은 레코드 {len(ids)}건 중복: id {ids}")

# 시승
for t in td:
    r = {"id": None, "brand_ko": t.get("brand_ko"), "brand_id": t.get("brand_id")}
    if t.get("brand_id") not in brand_ids:
        add("ERROR", "td-unknown-brand", r, f"시승 정보의 brand_id가 브랜드 목록에 없음: {t.get('brand_id')}")
    if t.get("can_apply_online") and not t.get("apply_url"):
        add("ERROR", "td-no-apply-url", r, "온라인 신청 가능인데 신청 URL이 없음")
    if t.get("has_event"):
        if not t.get("event_name"):
            add("ERROR", "td-event-no-name", r, "시승 이벤트 있음인데 이름이 없음")
        if not t.get("event_period"):
            add("WARN", "td-event-no-period", r, "시승 이벤트 기간 미표기")
        else:
            # 종료일만 본다: '~' 뒤의 날짜. 'MM-DD'만 있으면 앞쪽 전체 날짜의 연도를 쓴다. 종료일 표기가 없으면 판단하지 않는다.
            s = t["event_period"]
            first = re.search(r"(\d{4})-\d{2}-\d{2}", s)
            ends = []
            for x in re.findall(r"~\s*(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})", s):
                if len(x) == 5 and first:
                    x = f"{first.group(1)}-{x}"
                d_ = parse_date(x)
                if d_:
                    ends.append(d_)
            if ends and max(ends) < TODAY:
                add("WARN", "td-event-expired", r, f"시승 이벤트 기간 만료: {s}")
    if t.get("detail_level") in ("url_only", "none"):
        add("INFO", "td-thin", r, f"시승 상세 미수집({t.get('detail_level')}): 신청 URL만 있음")

# 정규화된 월별 혜택(benefits.jsonl) 점검
bp = os.path.join(U, "benefits.jsonl")
if os.path.exists(bp):
    ben = load_jsonl(bp)
    for b in ben:
        r = {"id": b.get("id"), "brand_ko": b.get("brand_ko"), "brand_id": b.get("brand_id")}
        for f in ("ym", "brand_ko", "title", "types", "detail"):
            if not b.get(f):
                add("ERROR", "benefit-required", r, f"혜택 항목에 {f} 없음")
        if not b.get("link"):
            add("WARN", "benefit-no-link", r, f"링크 없음: {b.get('title')}")
        if b.get("types") == "기타":
            add("WARN", "benefit-type-unknown", r, f"유형을 분류하지 못함: {b.get('title')}")
        if "미수집" in (b.get("detail") or "") and len(b["detail"]) < 60:
            add("WARN", "benefit-no-detail", r, f"세부내용 미수집: {b.get('title')}")
        if b.get("period_status") == "기간 만료":
            add("WARN", "benefit-expired", r, f"기준월에 받을 수 없는 혜택(기간 만료): {b.get('title')}")
        if re.search(r"[a-z]+_[a-z]+", b.get("detail") or ""):
            add("WARN", "benefit-raw-key", r, f"세부내용에 영문 내부 키가 남음: {b.get('title')}")
        if (b.get("model") or "").strip() == "" and b.get("types") in ("할인",) and not b.get("detail"):
            add("WARN", "benefit-no-scope", r, f"어느 모델 혜택인지 불명: {b.get('title')}")
    stats_ben = len(ben)
else:
    stats_ben = 0
    add("ERROR", "benefits-missing", {"id": None, "brand_ko": "전체"}, "benefits.jsonl 이 없음: build_benefits.py 를 먼저 실행")

# 커버리지
per_brand = collections.Counter(r["brand_id"] for r in recs if r["category"] != "status")
benefit_brand = collections.Counter(r["brand_id"] for r in recs if r["category"] in ("benefit", "event", "finance"))
benefit_model = collections.Counter(r["brand_id"] for r in recs if r["category"] in ("benefit", "event", "finance") and r.get("model"))
for b in brands:
    if per_brand.get(b["id"], 0) == 0:
        add("INFO", "no-data-brand", {"id": None, "brand_ko": b.get("brand_ko"), "brand_id": b["id"]}, "수집된 혜택·가격 레코드 없음(점검결과만 있거나 미수집)")
    elif benefit_brand.get(b["id"], 0) > 0 and benefit_model.get(b["id"], 0) == 0:
        # 어느 모델이 혜택 중인지가 핵심인데, 브랜드 공통 혜택만 있으면 모델별 확인이 안 된다
        add("WARN", "benefit-no-model", {"id": None, "brand_ko": b.get("brand_ko"), "brand_id": b["id"]}, "혜택은 있으나 어느 모델에 적용되는지(model) 정보가 없음")
    elif benefit_brand.get(b["id"], 0) == 0:
        # 이 DB의 목적은 월별 혜택(할인·이벤트·금융). 가격만 있는 브랜드는 핵심 정보가 빠진 것
        add("WARN", "no-benefit-brand", {"id": None, "brand_ko": b.get("brand_ko"), "brand_id": b["id"]}, "가격만 있고 혜택(할인·이벤트·금융) 레코드가 없음")

# 직전 실행과 비교
stats = dict(date=str(TODAY), records=len(recs), by_category=dict(collections.Counter(r["category"] for r in recs)),
             brand_counts={k: v for k, v in per_brand.items()})
if prev:
    ps_ = prev.get("stats", {})
    if ps_.get("records") and len(recs) < ps_["records"] * 0.8:
        add("ERROR", "records-dropped", {"id": None, "brand_ko": "전체"}, f"레코드 수 급감: {ps_['records']} → {len(recs)}")
    for bid, n in (ps_.get("brand_counts") or {}).items():
        now = per_brand.get(bid, 0)
        if n > 0 and now == 0:
            add("ERROR", "brand-lost", {"id": None, "brand_ko": bid}, f"이전에 {n}건이던 브랜드 데이터가 0건이 됨")
        elif n >= 5 and now < n * 0.5:
            add("WARN", "brand-shrunk", {"id": None, "brand_ko": bid}, f"브랜드 레코드 감소: {n} → {now}")

cnt = collections.Counter(i["level"] for i in issues)
by_rule = collections.defaultdict(list)
for i in issues:
    by_rule[(i["level"], i["rule"])].append(i)

report = dict(stats=stats, counts=dict(cnt), issues=issues)
json.dump(report, open(prev_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 사람용 요약
order = {"ERROR": 0, "WARN": 1, "INFO": 2}
lines = [f"# 품질 점검 보고서 ({TODAY})", "",
         f"- 레코드 {len(recs)}건 / 시승 {len(td)}곳 / ERROR **{cnt['ERROR']}** · WARN {cnt['WARN']} · INFO {cnt['INFO']}",
         "- ERROR가 있으면 GitHub·gist 게시를 멈춘다. 고친 뒤 다시 실행한다.", ""]
for (lv, rule), items in sorted(by_rule.items(), key=lambda x: (order[x[0][0]], x[0][1])):
    lines.append(f"## [{lv}] {rule} ({len(items)}건)")
    for i in items[:12]:
        lines.append(f"- id {i['id']} · {i['brand']}: {i['message']}")
    if len(items) > 12:
        lines.append(f"- … 외 {len(items) - 12}건")
    lines.append("")
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
open(os.path.join(ROOT, "docs", "QUALITY_REPORT.md"), "w", encoding="utf-8").write("\n".join(lines))

print(f"품질 점검: ERROR {cnt['ERROR']} / WARN {cnt['WARN']} / INFO {cnt['INFO']}  (docs/QUALITY_REPORT.md)")
for (lv, rule), items in sorted(by_rule.items(), key=lambda x: (order[x[0][0]], x[0][1])):
    print(f"  [{lv}] {rule}: {len(items)}건")
sys.exit(1 if cnt["ERROR"] else 0)
