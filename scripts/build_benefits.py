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
        detail=human[:1500], period_start=r.get("period_start"), period_end=r.get("period_end"),
        link=r.get("source_url"), confidence=r.get("confidence"), source_record_id=r["id"],
        extract_note="할인·조건·증정은 키워드로 나눈 값. 정확한 값은 detail·link 확인"))

# 시승 이벤트/혜택 (testdrive 인덱스에서)
for t in td:
    if not t.get("has_event"):
        continue
    ps, pe = None, None
    ds = re.findall(r"\d{4}-\d{2}-\d{2}", t.get("event_period") or "")
    if ds:
        ps = ds[0]
        pe = ds[-1] if len(ds) > 1 else None
    _ym = "2026-11"
    _st = "기간 미표기"
    if ps:
        _st = "기간 만료" if (pe or ps) < f"{_ym}-01" else ("시작 전" if ps > f"{_ym}-31" else "기준월 해당")
    rows.append(dict(
        ym=_ym, period_status=_st, brand_id=t["brand_id"], brand_ko=t["brand_ko"],
        model=None, sub_model=None, types="시승혜택", title=t.get("event_name") or "시승 이벤트",
        discount=None, conditions=t.get("policy"), reward=t.get("event_benefit"),
        detail=" / ".join(x for x in [t.get("event_benefit"), t.get("event_period"), t.get("note")] if x) or "세부 내용 미수집",
        period_start=ps, period_end=pe, link=t.get("event_url") or t.get("apply_url"), confidence="medium",
        source_record_id=None, extract_note="시승 인덱스(testdrive.json)에서 가져옴"))

rows.sort(key=lambda x: (x["brand_ko"] or "", x["model"] or "", x["title"] or ""))
for i, x in enumerate(rows, 1):
    x["id"] = i
cols = ["id", "ym", "period_status", "brand_id", "brand_ko", "model", "sub_model", "types", "title", "discount", "conditions", "reward",
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
from collections import Counter
print("benefits:", len(rows), dict(Counter(x["types"].split(",")[0] for x in rows)))
