"""혜택 항목을 '수집 당시 원문(증거)'과 대조한다. 사용: python -I scripts/verify_evidence.py  (build_benefits.py 다음)
증거 파일: data/evidence/<brand_id>/<YYYY-MM-DD>_<slug>.txt  (머리말 '# url:', '# captured:' 다음 '---' 아래가 공식 페이지 본문)
검사 대상 주장(claim):
  - 금액(만원/원), 퍼센트, 개월, 인원(명/분) 숫자, 모델명, 기간(시작·종료일)
  - 항목의 세부내용에 나온 주장이 증거 원문에 없으면 '미확인'이다.
결과:
  - benefits.jsonl/.csv/.json 에 verification, unverified_claims, evidence_files, evidence_date 칸을 더한다
  - data/unified/verification.json (브랜드별 통계), docs/VERIFY_CHECKLIST.md (사람/독립 재확인이 볼 목록)
검증 상태: 검증됨 / 일부 미확인 / 증거 없음
예외 승인: data/verify_ack.json 에 {"claims":[{"brand_id","title_contains","claim","reason"}]} 로 이유를 적으면 그 주장은 통과.
"""
import json, os, re, sys, glob, csv, calendar, datetime, collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, "data", "unified")
EV = os.path.join(ROOT, "data", "evidence")
TODAY = datetime.date.today()

rows = [json.loads(l) for l in open(os.path.join(U, "benefits.jsonl"), encoding="utf-8") if l.strip()]
ack_path = os.path.join(ROOT, "data", "verify_ack.json")
ACK = json.load(open(ack_path, encoding="utf-8")).get("claims", []) if os.path.exists(ack_path) else []

def norm(s):
    s = (s or "").lower().replace("\n", "¶")       # 줄 경계는 남겨 둔다(숫자가 이웃 줄 숫자와 붙어 보이는 것을 막음)
    s = re.sub(r"(?<=\d),(?=\d)", "", s)          # 1,000 -> 1000
    s = re.sub(r"만\s*원", "만원", s)
    return re.sub(r"[\s·\-–—_/()\[\]·'\"‘’“”]", "", s)

# --- 증거 읽기 (브랜드별, 같은 slug 는 최신 날짜만)
evidence = collections.defaultdict(dict)   # brand -> slug -> dict(text, date, url, file)
for path in glob.glob(os.path.join(EV, "*", "*.txt")):
    brand = os.path.basename(os.path.dirname(path))
    base = os.path.basename(path)[:-4]
    m = re.match(r"(\d{4}-\d{2}-\d{2})_(.+)", base)
    if not m:
        continue
    raw = open(path, encoding="utf-8").read()
    head, _, body = raw.partition("\n---\n")
    url = (re.search(r"# url:\s*(.*)", head) or [None, None])[1]
    cur = evidence[brand].get(m.group(2))
    if not cur or m.group(1) > cur["date"]:
        evidence[brand][m.group(2)] = dict(text=norm(body), date=m.group(1), url=url, file=os.path.relpath(path, ROOT).replace("\\", "/"))

# --- 주장 추출
MONEY = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*만\s*원?")
WON = re.compile(r"(\d[\d,]{4,})\s*원")
PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
MON = re.compile(r"(\d+)\s*개월")
CNT = re.compile(r"(\d+)\s*(명|분)")
SYNTH_MODEL = re.compile(r"전 모델|공통|전체")

def claims_of(r):
    text = " ".join(str(r.get(k) or "") for k in ("title", "discount", "conditions", "reward", "detail"))
    text = re.sub(r"만\s*km|\d+\s*km", " ", text)           # 주행거리 제외
    text = re.sub(r"\d{4}-\d{2}-\d{2}(\s*~\s*(\d{4}-)?\d{2}-\d{2})?", " ", text)  # 날짜 표기 제외(기간은 따로 검사)
    out = {}
    for m in MONEY.finditer(text):
        out[m.group(1).replace(",", "") + "만"] = "금액"
    for m in re.finditer(r"\(만원\)\s*:\s*(\d[\d,]*)", text):   # '최대혜택(만원): 200' 처럼 단위가 앞에 붙은 표기
        out[m.group(1).replace(",", "") + "만"] = "금액"
    for m in WON.finditer(text):
        out[m.group(1).replace(",", "") + "원"] = "금액"
    if r.get("max_benefit_krw"):   # 페이지가 제시한 최대혜택 금액도 원문에 있어야 한다
        out[f"{r['max_benefit_krw'] / 10000:g}만"] = "최대혜택"
    for m in PCT.finditer(text):
        out[m.group(1) + "%"] = "퍼센트"
    for m in MON.finditer(text):
        out[m.group(1) + "개월"] = "개월"
    for m in CNT.finditer(text):
        out[m.group(1) + m.group(2)] = "인원"
    return out

def present(claim, ev_text):
    """증거 본문(정규화됨)에 주장이 있는지. 만/만원 표기 차이를 허용한다."""
    if claim.endswith("만"):
        n = claim[:-1]
        return (n + "만") in ev_text or (n + "만원") in ev_text or _man_variants(n, ev_text)
    if claim.endswith(("명", "분")):   # '63분의 고객'과 '63명'은 같은 인원 표기
        return (claim[:-1] + "명") in ev_text or (claim[:-1] + "분") in ev_text
    if claim.endswith("원") and claim[:-1].isdigit():  # 표 머리말이 '금액(원)'이라 숫자만 있는 경우: 앞뒤가 숫자가 아닐 때만 인정
        return claim in ev_text or re.search(rf"(?<!\d){claim[:-1]}(?!\d)", ev_text) is not None
    return claim in ev_text

def _man_variants(n, ev_text):
    # 1,000,000원 == 100만원 같은 표기 차이
    try:
        won = str(int(float(n) * 10000))
        return won + "원" in ev_text or won in ev_text
    except Exception:
        return False

def date_present(d, ev_text, whole_month=False):
    y, mo, da = d.split("-")
    mo_i, da_i = int(mo), int(da)
    v = [d, f"{y}.{mo}.{da}", f"{y}/{mo}/{da}", f"{mo}.{da}", f"{mo}/{da}", f"{mo}-{da}", f"{mo_i}.{da_i}", f"{mo_i}/{da_i}", f"{mo_i}월{da_i}일", f"{mo_i}.{da_i}.", f"{y[2:]}.{mo}.{da}"]
    if whole_month:
        v.append(f"{mo_i}월")
    return any(norm(x) in ev_text for x in v)

def model_present(model, ev_text):
    if not model or SYNTH_MODEL.search(model):
        return True
    toks = [t for t in re.split(r"[\s/,]+", model) if t]
    key = norm(model)
    return key in ev_text or all(norm(t) in ev_text for t in toks)

def acked(r, claim):
    for a in ACK:
        if a.get("brand_id") == r["brand_id"] and a.get("title_contains", "") in (r.get("title") or "") and a.get("claim") == claim:
            return a.get("reason")
    return None

# --- 항목별 대조
stats = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    ev = evidence.get(r["brand_id"], {})
    if not ev:
        r.update(verification="증거 없음", unverified_claims=None, evidence_files=None, evidence_date=None)
        stats[r["brand_ko"]]["증거 없음"] += 1
        continue
    # 이 항목의 링크와 같은 URL의 증거를 우선 사용, 없으면 브랜드의 모든 증거를 합쳐서 본다
    own = [e for e in ev.values() if e.get("url") and r.get("link") and e["url"].split("#")[0].rstrip("/") == r["link"].split("#")[0].rstrip("/")]
    pool = own or list(ev.values())
    ev_text = "".join(e["text"] for e in pool)
    missing = []
    for c, kind in claims_of(r).items():
        if not present(c, ev_text) and not acked(r, c):
            missing.append(f"{kind} {c}")
    if not model_present(r.get("model"), ev_text) and not acked(r, "모델:" + (r.get("model") or "")):
        missing.append(f"모델명 {r.get('model')}")
    whole = False
    if r.get("period_start") and r.get("period_end"):
        s, e_ = r["period_start"], r["period_end"]
        y, mo, _ = e_.split("-")
        whole = s.endswith("-01") and int(e_.split("-")[2]) == calendar.monthrange(int(y), int(mo))[1] and s[:7] == e_[:7]
        for lab, d in (("기간 시작일", s), ("기간 종료일", e_)):
            if not date_present(d, ev_text, whole) and not acked(r, lab):
                missing.append(f"{lab} {d}")
    status = "검증됨" if not missing else "일부 미확인"
    r.update(verification=status, unverified_claims="; ".join(missing) or None,
             evidence_files=", ".join(e["file"] for e in pool), evidence_date=max(e["date"] for e in pool))
    stats[r["brand_ko"]][status] += 1

# --- 결과 쓰기
cols = [c for c in rows[0].keys()]
with open(os.path.join(U, "benefits.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
json.dump(rows, open(os.path.join(U, "benefits.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(U, "benefits.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

tot = collections.Counter(r["verification"] for r in rows)
summary = dict(date=str(TODAY), total=len(rows), counts=dict(tot), by_brand={k: dict(v) for k, v in stats.items()})
json.dump(summary, open(os.path.join(U, "verification.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

L = [f"# 검증 체크리스트 ({TODAY})", "",
     f"- 검증됨 {tot['검증됨']} · 일부 미확인 {tot['일부 미확인']} · 증거 없음 {tot['증거 없음']} (전체 {len(rows)}건)",
     "- **일부 미확인**: 항목의 숫자·모델명·기간이 수집한 원문(data/evidence)에 없다. 원문을 다시 열어 맞는지 확인하고 고치거나, 맞다면 data/verify_ack.json 에 이유를 적는다.",
     "- **증거 없음**: 그 브랜드의 원문 파일이 없다. 다음 갱신 때 공식 페이지 본문을 data/evidence 에 저장한다.", ""]
by = collections.defaultdict(list)
for r in rows:
    if r["verification"] == "일부 미확인":
        by[r["brand_ko"]].append(r)
for b, rs in by.items():
    L.append(f"## {b} — 확인할 항목 {len(rs)}건")
    for r in rs:
        L.append(f"- {r.get('model') or '브랜드 공통'} / {r['title'][:50]}: 미확인 → {r['unverified_claims']}  ({r.get('link')})")
    L.append("")
no_ev = sorted({r["brand_ko"] for r in rows if r["verification"] == "증거 없음"})
if no_ev:
    L.append("## 증거 파일이 없는 브랜드")
    L.append(", ".join(no_ev))
os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
open(os.path.join(ROOT, "docs", "VERIFY_CHECKLIST.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"증거 대조: 검증됨 {tot['검증됨']} / 일부 미확인 {tot['일부 미확인']} / 증거 없음 {tot['증거 없음']}  (docs/VERIFY_CHECKLIST.md)")
