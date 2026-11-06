"""월별 혜택 정규화. 사용: python -I scripts/build_benefits.py   (build_db.py 다음에 실행)
통합 레코드(offers.jsonl)와 시승 이벤트(testdrive.json)에서 '혜택'만 뽑아 아래 칸으로 정리한다.
  기준년월 · 브랜드 · 차종 · 세부모델 · 유형 · 제목 · 할인내용 · 조건 · 증정/경품 · 세부내용 · 기간 · 링크
- 원문(text)은 버리지 않고 '세부내용'에 사람이 읽는 말로 바꿔 모두 싣는다.
- 할인내용/조건/증정은 문장 키워드로 나눈 것이라 틀릴 수 있다(extract_note에 표시). 정확한 값은 세부내용과 링크로 확인한다.
결과: data/unified/benefits.jsonl / benefits.csv / benefits.json
"""
import json, os, re, csv, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, "data", "unified")

recs = [json.loads(l) for l in open(os.path.join(U, "offers.jsonl"), encoding="utf-8-sig") if l.strip()]
td = json.load(open(os.path.join(U, "testdrive.json"), encoding="utf-8-sig"))

KEYS = {  # 원본 JSON의 영문 키 -> 읽을 수 있는 말
    "choose_one": "택1", "items": "혜택", "conditions": "조건", "eligibility": "대상", "period": "기간",
    "base_program": "기본 프로그램", "base_program_choose_one": "기본 프로그램(택1)", "custom_stackable": "중복 적용 가능",
    "delivery_gift": "출고 사은품", "repurchase_discount_pct": "재구매 할인율(%)", "benefit": "혜택",
    "benefit_1": "혜택1", "benefit_2": "혜택2", "headline": "요약", "max_benefit": "최대 혜택", "program": "프로그램",
    "note": "참고", "status": "상태", "years": "연식", "monthly_krw": "월 납입금(원)", "rate_pct": "금리(%)",
    "operating_lease": "운용리스", "low_rate_installment": "저금리 할부", "installment_examples": "할부 예시",
    "price_basis": "가격 기준", "trim": "트림", "residual": "잔존가치", "monthly": "월 납입금", "lease": "리스",
    "installment": "할부", "support": "지원", "source": "출처", "title": "이름", "since": "기준 시점",
    "benefit_krw_vat_included": "혜택 금액(원, VAT 포함)", "monthly_from": "월 납입금 시작", "tabs": "관련 모델",
    "value_plus_lease": "밸류+ 리스", "value_plus_installment": "밸류+ 할부", "models_seen": "확인한 모델",
    "models_note": "확인 범위", "text": "안내", "max_benefit_manwon": "최대혜택(만원)", "breakdown_manwon": "구성(만원)",
    "target_models": "대상 모델", "apply_period": "신청 기간", "onsite_test_drive_period": "현장 시승 기간",
    "selectable_models": "선택 가능 모델", "offers_faq_detail": "상세 안내", "breakdown_note": "구성 참고",
    "monthly_note": "월 납입금 참고", "MY_choose_one": "연식별 택1",
    "detail": "세부", "rules": "규칙", "benefits": "혜택", "example": "예시", "trade_in": "트레이드인", "models": "대상 모델", "samsung_card_installment": "삼성카드 할부", "ford": "포드", "lincoln": "링컨",
}
SPLIT = re.compile(r"\s*/\s*|\s*;\s*|\s*\|\s*")
DISC = re.compile(r"할인|현금|캐시백|지원금|보조금|월\s*납입금|무이자|금리|\d+(\.\d+)?\s*%|만원|리스료")
COND = re.compile(r"선수|선납|보증금|개월|잔존|잔가|대상|한정|이용 시|고객|조건|유의|생산분|출고|제외|선착순|단,|만\s*km|㎞|km|재고|택1|택일|소진|기간|가능|불가|필요|확인서")
GIFT = re.compile(r"경품|추첨|증정|사은품|선물|제공|지급|쿠폰|상품권|캐리어|굿즈|초대|Kit|무상|티켓|패스")

def humanize(text):
    t = text or ""
    m = re.match(r"^\s*(\{[^{}]*\})\s*(.*)$", t, re.S)  # BMW: 앞부분 JSON(월 납입금)
    if m:
        try:
            plans = json.loads(m.group(1))
            t = "월 납입금(만원/월): " + ", ".join(f"{k} {v}" for k, v in plans.items()) + (" ; 조건: " + m.group(2) if m.group(2) else "")
        except Exception:
            pass
    for k in sorted(KEYS, key=len, reverse=True):
        t = re.sub(rf"(?<![A-Za-z_]){k}(?=:)", KEYS[k], t)
    t = t.replace('{"', "").replace('"}', "").replace('":', ": ").replace(',"', ", ").replace('"', "").replace("{", "").replace("}", "")
    return t.strip()

def segs(text):
    """괄호 밖의 ' / ', ';', '|' 에서만 나눈다. '(36개월 / 선수금 30%)' 같은 괄호 안 내용은 한 문장으로 유지."""
    t = humanize(text)
    out, buf, depth = [], [], 0
    for i, ch in enumerate(t):
        if ch in "([（":
            depth += 1
        elif ch in ")]）":
            depth = max(0, depth - 1)
        cut = depth == 0 and (ch in ";|" or (ch == "/" and 0 < i < len(t) - 1 and t[i - 1] == " " and t[i + 1] == " "))
        if cut:
            out.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return [s.strip() for s in out if len(s.strip()) > 1]

# 한 문장은 한 칸에만 들어간다. 우선순위: 증정/경품 > 할인·금융 조건 > 적용 조건. 기간·대상 모델 문장은 칸에서 뺀다(세부내용·기간 칸에 있음).
REWARD = re.compile(r"경품|추첨|증정|사은품|선물|쿠폰|상품권|캐리어|굿즈|초대|Kit|티켓|패스|풀케어|충전 멤버십")
MONEY = re.compile(r"할인|현금|캐시백|지원금|보조금|인센티브|무이자|금리|\d(\.\d+)?\s*%|월 납입금|월 리스료|리스료|\d+만원")
SKIP = re.compile(r"^(기간|대상 모델|출처|확인 범위|확인한 모델|기준 시점|안내)\s*:")

def classify(text):
    reward, money, cond = [], [], []
    for s in segs(text):
        if SKIP.match(s):
            continue
        bucket = reward if REWARD.search(s) else money if MONEY.search(s) else cond if COND.search(s) else None
        if bucket is not None and s not in bucket:
            bucket.append(s)
    return money, cond, reward

def won(n):
    return f"{n / 10000:,.0f}만원" if n >= 10000 else f"{n:,}원"

def month_of(r):
    """기준년월 = 수집한 달. 혜택 기간이 그 달과 겹치는지는 period_status로 따로 적는다."""
    c = r.get("captured") or ""
    ym = c[:7] if c else None
    ps, pe = r.get("period_start"), r.get("period_end")
    if not ym or not (ps or pe):
        return ym, "기간 미표기"
    first, last = f"{ym}-01", f"{ym}-31"
    if pe and pe < first:
        return ym, "기간 만료"
    if ps and ps > last:
        return ym, "시작 전"
    return ym, "기준월 해당"

SUFFIX = ("Hybrid", "HEV", "하이브리드", "Black", "Coupe", "Sportback", "Plus", "Label", "Magma")
def split_model(model, title, cat):
    """차종 / 세부모델 분리. 괄호의 연식·MY, 끝의 하이브리드 같은 표기, BMW류 트림 제목을 세부모델로 뺀다."""
    if not model:
        return None, None
    sub = []
    m = model
    paren = re.findall(r"\(([^)]*)\)", m)
    if paren:
        sub += paren
        m = re.sub(r"\s*\([^)]*\)", "", m).strip()
    for suf in SUFFIX:
        if m.endswith(" " + suf) and len(m) > len(suf) + 1:
            sub.append(suf)
            m = m[: -(len(suf) + 1)].strip()
            break
    if cat == "finance" and title and "월 납입금" in title:  # BMW: 제목 앞부분이 트림(세부모델)
        t = re.sub(r"\s*월 납입금.*$", "", title).strip()
        if t:
            sub.append(t)
    return m, (" / ".join(x for x in sub if x) or None)

def types_of(r, text):
    t = []
    cat, blob = r["category"], f"{r.get('title') or ''} {text}"
    if cat == "event":
        t.append("시승혜택" if "시승" in blob else "이벤트")
    if cat == "finance":
        t.append("금융")
    if re.search(r"현금|할인|캐시백|지원금|보조금|인센티브", blob) or r.get("max_benefit_krw") or (cat == "benefit" and re.search(r"\d+\s*만", blob)):
        t.append("할인")
    if re.search(r"무이자|금리|할부|리스|월 납입금|월\s*\d+만원", blob) and "금융" not in t:
        t.append("금융")
    if cat == "benefit" and re.search(r"증정|사은품|쿠폰|상품권|캐리어|Kit|티켓|경품|추첨", blob):
        t.append("증정")
    if re.search(r"보증|엔진오일|오일|무상 점검|PMS|SMS|풀케어", blob):
        t.append("보증·서비스")
    seen = []
    for x in t:
        if x not in seen:
            seen.append(x)
    return seen or ["기타"]

rows = []
for r in recs:
    if r["category"] not in ("benefit", "finance", "event"):
        continue
    text = r.get("text") or ""
    human = humanize(text)
    if not human and r.get("max_benefit_krw"):
        human = f"최대 {won(r['max_benefit_krw'])} 혜택 (세부 항목은 공식 페이지 확인)"
    if not human:
        human = "세부 내용 미수집 (공식 페이지 확인)"
    model, sub = split_model(r.get("model"), r.get("title"), r["category"])
    ym, basis = month_of(r)
    disc, cond, gift = classify(text)
    rows.append(dict(
        ym=ym, period_status=basis, brand_id=r["brand_id"], brand_ko=r["brand_ko"], model=model, sub_model=sub,
        types=",".join(types_of(r, text)), title=re.sub(r"\(만원/월\)", "", r["title"] or "").strip(),
        discount="; ".join(disc[:6]) or (f"최대 {won(r['max_benefit_krw'])}" if r.get("max_benefit_krw") else None),
        conditions="; ".join(cond[:6]) or None, reward="; ".join(gift[:6]) or None,
        _cat=r["category"], max_benefit_krw=r.get("max_benefit_krw"), detail=human[:1500], period_start=r.get("period_start"), period_end=r.get("period_end"),
        link=r.get("source_url"), confidence=r.get("confidence"), source_record_id=r["id"],
        extract_note="할인·조건·증정은 키워드로 나눈 값. 정확한 값은 detail·link 확인"))

# 시승 이벤트/혜택 (testdrive 인덱스에서)
for t in td:
    if not t.get("has_event"):
        continue
    ps, pe = None, None
    s_ = t.get("event_period") or ""
    ds = re.findall(r"\d{4}-\d{2}-\d{2}", s_)
    if ds:
        ps = ds[0]
        # 종료일은 '~' 뒤의 날짜만 본다. 'MM-DD' 표기면 시작일의 연도를 붙인다
        ends = [x if len(x) == 10 else f"{ps[:4]}-{x}" for x in re.findall(r"~\s*(\d{4}-\d{2}-\d{2}|\d{2}-\d{2})", s_)]
        pe = ends[0] if ends else None
    # 혜택 레코드에 같은 이벤트가 이미 있으면 새 행을 만들지 않고 시승 정보로 채운다(중복 방지)
    def norm(s):
        return re.sub(r"[\s\-—·'‘’\"()]", "", s or "")
    key = norm(t.get("event_name"))[:6]
    _types = ("이벤트", "시승혜택", "할인", "증정", "기타")
    full = norm(t.get("event_name"))
    # 이벤트명이 통째로 같은 행을 먼저 찾고(르노처럼 '세일 페스타'가 여러 행 제목에 들어간 경우 오병합 방지), 없으면 앞 6글자로 찾는다
    dup = next((x for x in rows if x["brand_id"] == t["brand_id"] and full and full in norm(x["title"]) and x["types"].split(",")[0] in _types), None) \
        or next((x for x in rows if x["brand_id"] == t["brand_id"] and key and key in norm(x["title"]) and x["types"].split(",")[0] in _types), None)
    if dup:
        dup["reward"] = dup.get("reward") or t.get("event_benefit")
        dup["conditions"] = dup.get("conditions") or t.get("policy")
        if "시승혜택" not in dup["types"]:
            dup["types"] = "시승혜택," + dup["types"]
        if not dup.get("period_start") and ps:
            dup["period_start"], dup["period_end"] = ps, pe
        dup["detail"] = (dup["detail"] + " / 시승 정보: " + (t.get("event_benefit") or "") + " " + (t.get("event_period") or "")).strip()[:1500]
        dup["link"] = dup.get("link") or t.get("event_url")
        continue
    _ym = "2026-11"
    _st = "기간 미표기"
    if ps and pe:
        _st = "기간 만료" if pe < f"{_ym}-01" else ("시작 전" if ps > f"{_ym}-31" else "기준월 해당")
    rows.append(dict(
        ym=_ym, period_status=_st, brand_id=t["brand_id"], brand_ko=t["brand_ko"],
        model=None, sub_model=None, types="시승혜택", title=t.get("event_name") or "시승 이벤트",
        discount=None, conditions=t.get("policy"), reward=t.get("event_benefit"),
        detail=" / ".join(x for x in [t.get("event_benefit"), t.get("event_period"), t.get("note")] if x) or "세부 내용 미수집",
        period_start=ps, period_end=pe, link=t.get("event_url") or t.get("apply_url"), confidence="medium",
        source_record_id=None, extract_note="시승 인덱스(testdrive.json)에서 가져옴"))

# ---------- 차량 모델 / 이벤트명 분리, 할인 금액 컬럼 ----------
# model·sub_model 에는 차량 이름만, event_name 에는 이벤트(프로그램)명만 둔다. 연식은 model_year, 적용 범위는 target_scope.
BRAND_PREFIX = re.compile(r"^(THE NEW BMW|BMW|Audi|아우디)\s+", re.I)
YEAR_PAT = re.compile(r"\(?\s*(?:(20\d\d)\s*년식?|(\d\d)\s*년식|(\d\d)\s*MY|(20\d\d))\s*\)?", re.I)
GROUP_PAT = re.compile(r"전\s*모델|전기차 전|내연기관")
NOT_MODEL = re.compile(r"혜택|프로모션|이벤트|금융|할인|리스|할부|납입|프로그램|캠페인|무이자|지원|쿠폰|경품")
DEFAULT_EVENT = {"toyota": "이달의 구매 혜택", "audi": "금융 프로모션(리스·할부)"}

def year_of(*texts):
    for t in texts:
        m = YEAR_PAT.search(t or "")
        if m:
            y = m.group(1) or m.group(4) or ("20" + (m.group(2) or m.group(3)))
            return y
    return None

def strip_year(s):
    return re.sub(r"\s{2,}", " ", YEAR_PAT.sub(" ", s or "")).strip(" /-—·()")

def clean_vehicle(r):
    model, sub, title = r.get("model"), r.get("sub_model"), r.get("title") or ""
    year = year_of(model, sub, title)
    scope = None
    if model and GROUP_PAT.search(model):          # 'AMG 전 모델', 'MINI 전기차 전 모델' 같은 묶음은 모델이 아니라 적용 범위
        scope = strip_year(model)
        model = None
    if model:
        model = strip_year(BRAND_PREFIX.sub("", model))
    if sub:
        sub_parts = [strip_year(p) for p in re.split(r"\s*/\s*", sub)]
        sub_parts = [p for p in sub_parts if p and p.lower() != "label" and not NOT_MODEL.search(p) and not re.fullmatch(r"20\d\d|\d\d?MY", p, re.I)]
        sub = " / ".join(sub_parts) or None
    if not model and not scope:
        scope = "브랜드 공통(모델 미지정)"
    elif model:
        scope = scope or "특정 모델"
    r["model"], r["sub_model"], r["model_year"], r["target_scope"] = model, sub, year, scope

def event_name_of(r):
    t = re.sub(r"\(만원/월\)", "", r.get("title") or "")
    if r.get("_cat") == "event":      # 이벤트는 이름 자체가 이벤트명이다(모델명이 이름 일부여도 자르지 않는다)
        return re.sub(r"\s{2,}", " ", t).strip()
    raw_model = r.get("_raw_model") or ""
    for s in sorted(filter(None, {raw_model, r.get("model"), r.get("sub_model"), BRAND_PREFIX.sub("", raw_model)}), key=len, reverse=True):
        t = re.sub(re.escape(s), " ", t, flags=re.I)
    t = strip_year(re.sub(r"\(\s*\)", " ", t))
    t = re.sub(r"\s{2,}", " ", t).strip(" -—·/")
    if "월 납입금" in t and len(t.replace("월 납입금", "").strip()) < 3:
        t = "월 납입금 프로모션"
    if len(re.sub(r"[\s()]", "", t)) < 2 or t in {r.get("brand_ko")}:
        base = DEFAULT_EVENT.get(r["brand_id"])
        t = base or ("금융 프로모션(리스·할부)" if r.get("types") == "금융" else "월 구매 혜택(이벤트명 미표기)")
    return t

FIN = re.compile(r"금리|이자|선수|선납|잔존|잔가|리스|납입|무이자|\d\s*개월")
AMT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*만\s*원?")
CTX = re.compile(r"할인|현금|지원|캐시백|인센티브|최대|보조|혜택")
RATE = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*(?:까지\s*)?할인|할인율\(%\):\s*(\d+(?:\.\d+)?)")

def parse_discount(r):
    """할인 금액·율을 숫자 컬럼으로. 선택지가 여러 개면 전부 discount_options 에 두고, discount_amount_krw/rate 는 그중 최대값(=최대 할인)."""
    amts, rates, opts = [], [], []
    for seg in re.split(r"\s*;\s*", r.get("discount") or ""):
        if re.search(r"월 납입금", seg) and not re.search(r"할인|현금", seg):
            continue
        hit = False
        for m in AMT.finditer(seg):
            pre, post = seg[max(0, m.start() - 10):m.start()], seg[m.end():m.end() + 6]
            if re.search(r"월\s*(최대\s*)?$", pre) or post.startswith("대") or post.lstrip().startswith("상당"):
                continue
            if CTX.search(pre + post):
                amts.append(round(float(m.group(1).replace(",", "")) * 10000)); hit = True
        for m in RATE.finditer(seg):
            rates.append(float(m.group(1) or m.group(2))); hit = True
        if not hit and r.get("max_benefit_krw") and not FIN.search(seg):   # 제네시스 '... 5%' 처럼 '할인' 글자 없이 %만 있는 경우
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", seg):
                rates.append(float(m.group(1))); hit = True
        if hit and seg.strip() not in opts:
            opts.append(seg.strip()[:80])
    if r.get("max_benefit_krw"):
        amts.append(int(r["max_benefit_krw"]))
    amt = max(amts) if amts else None
    rate = max(rates) if rates else None
    types = r.get("types") or ""
    if amt and rate:
        dt = "정액+정률 할인"
    elif amt:
        dt = "정액 할인"
    elif rate:
        dt = "정률 할인"
    elif "금융" in types or FIN.search(r.get("discount") or ""):
        dt = "금융 조건(금리·월납입금, 할인 금액 없음)"
    else:
        dt = "할인 없음"
    r["discount_type"], r["discount_amount_krw"], r["discount_rate_pct"] = dt, amt, rate
    r["discount_options"] = " | ".join(opts) or None

for x in rows:
    x["_raw_model"] = x.get("model")
    clean_vehicle(x)
    x["event_name"] = event_name_of(x)
    parse_discount(x)

# 대상 월(수집한 달)과 기간이 겹치지 않는 항목(기간 만료 / 시작 전)은 월별 혜택 표에서 뺀다. 지우지 않고 benefits_excluded.* 에 이유와 함께 보관한다.
excluded = [x for x in rows if x["period_status"] in ("기간 만료", "시작 전")]
rows = [x for x in rows if x["period_status"] not in ("기간 만료", "시작 전")]
for x in excluded:
    x["exclude_reason"] = f"대상 월({x['ym']})과 기간이 겹치지 않음: {x['period_status']} ({x.get('period_start') or '?'}~{x.get('period_end') or '?'})"

rows.sort(key=lambda x: (x["brand_ko"] or "", x["model"] or "", x["title"] or ""))
for i, x in enumerate(rows, 1):
    x["id"] = i
cols = ["id", "ym", "period_status", "brand_id", "brand_ko", "model", "sub_model", "model_year", "target_scope", "event_name", "types", "title",
        "discount_type", "discount_amount_krw", "discount_rate_pct", "discount_options", "max_benefit_krw", "discount", "conditions", "reward",
        "detail", "period_start", "period_end", "link", "confidence", "source_record_id", "extract_note"]
with open(os.path.join(U, "benefits.jsonl"), "w", encoding="utf-8") as f:
    for x in rows:
        f.write(json.dumps({c: x.get(c) for c in cols}, ensure_ascii=False) + "\n")
json.dump([{c: x.get(c) for c in cols} for x in rows], open(os.path.join(U, "benefits.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(U, "benefits.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for x in rows:
        w.writerow({c: x.get(c) for c in cols})
excols = [c for c in cols if c != "id"] + ["exclude_reason"]
with open(os.path.join(U, "benefits_excluded.jsonl"), "w", encoding="utf-8") as f:
    for x in excluded:
        f.write(json.dumps({c: x.get(c) for c in excols}, ensure_ascii=False) + "\n")
with open(os.path.join(U, "benefits_excluded.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=excols)
    w.writeheader()
    for x in excluded:
        w.writerow({c: x.get(c) for c in excols})
from collections import Counter
print("benefits:", len(rows), "| 제외(기간 불일치):", len(excluded), dict(Counter(x["types"].split(",")[0] for x in rows)))
