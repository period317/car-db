"""월별 혜택 누적 이력. 사용: python -I scripts/update_history.py   (verify_evidence.py 다음에 실행)

원칙: **지우거나 덮어쓰지 않고 덧붙이기만 한다.**
- data/history/benefits_history.jsonl : 항목의 '버전'을 한 줄씩 덧붙이는 로그(append-only).
    change = new(처음 관측) / changed(내용이 바뀜) / ended(공식 페이지에서 사라짐) / expired(기간이 지난 채 관측)
- data/history/index.json           : 항목별 최신 상태(다음 실행에서 비교용). 로그에서 다시 만들 수 있다.
- data/history/snapshots/benefits_YYYY-MM-DD.jsonl.gz : 그 날짜의 benefits.jsonl 통째 사본(같은 날 재실행이면 그 날짜 사본만 갱신).
- data/history/benefits_history.csv : 로그를 사람이 보기 좋게 펼친 표(매 실행마다 다시 생성, 원본은 jsonl).
    valid_from = 이 버전을 처음 본 날, valid_to = 다음 버전을 본 날(또는 종료일), 비어 있으면 현재 유효.
- 과거 월 조회(scripts/query_history.py --ym 2026-11): 공식 기간(period_start/end)이 적힌 항목은 기간이 그 월과 겹치면 그 월의 혜택,
  기간이 없는 항목은 우리가 관측한 구간(valid_from ~ valid_to)이 그 월과 겹치면 그 월의 혜택으로 본다.
"""
import json, os, sys, csv, gzip, hashlib, datetime, shutil

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, "data", "unified")
H = os.path.join(ROOT, "data", "history")
os.makedirs(os.path.join(H, "snapshots"), exist_ok=True)
TODAY = datetime.date.today().isoformat()

HASH_FIELDS = ["types", "discount_type", "discount_amount_krw", "discount_rate_pct", "discount_options", "discount", "conditions", "reward",
               "period_start", "period_end", "link", "model_year", "target_scope",
               "finance_company", "finance_product", "finance_rate", "finance_term", "finance_down", "finance_monthly", "vehicle_price_krw"]
COLS = ["key", "change", "valid_from", "valid_to", "row_status", "ym", "period_month", "brand_id", "brand_ko", "model", "sub_model", "model_year", "target_scope",
        "event_name", "title", "types", "discount_type", "discount_amount_krw", "discount_rate_pct", "discount_options", "max_benefit_krw", "discount", "conditions",
        "reward", "finance_company", "finance_product", "finance_rate", "finance_term", "finance_down", "finance_monthly", "vehicle_price_krw", "period_start", "period_end", "period_status", "link", "confidence", "verification", "evidence_date", "detail"]


def load(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def key_of(r):
    # 월(ym)은 키에 넣지 않는다: 같은 이벤트가 여러 달 이어져도 한 항목의 버전들로 이어진다
    return "|".join(str(r.get(k) or "") for k in ("brand_id", "model", "sub_model", "title"))


def hash_of(r):
    return hashlib.sha1(json.dumps([r.get(k) for k in HASH_FIELDS], ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def period_month(r):
    return (r.get("period_start") or "")[:7] or (r.get("period_end") or "")[:7] or r.get("ym")


cur_rows = load(os.path.join(U, "benefits.jsonl"))
exp_rows = [r for r in load(os.path.join(U, "benefits_excluded.jsonl")) if str(r.get("exclude_reason") or "").startswith("대상 월")]  # 기간이 지난 것만(범위 밖 서비스는 제외)
current = {}
for r in cur_rows:
    current[key_of(r)] = (r, "active")
for r in exp_rows:
    current.setdefault(key_of(r), (r, "expired"))

idx_path = os.path.join(H, "index.json")
index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
log_path = os.path.join(H, "benefits_history.jsonl")
appended = {"new": 0, "changed": 0, "ended": 0, "expired": 0}
lines = []

for k, (r, status) in current.items():
    h = hash_of(r)
    prev = index.get(k)
    if prev is None or prev.get("ended"):
        change = "expired" if status == "expired" else "new"
    elif prev["hash"] != h or prev.get("row_status") != status:
        change = "changed"
    else:
        prev["last_seen"] = TODAY
        continue
    rec = {c: r.get(c) for c in COLS if c in r}
    rec.update(key=k, change=change, valid_from=TODAY, row_status=status, period_month=period_month(r))
    lines.append(rec)
    appended[change] += 1
    index[k] = {"hash": h, "row_status": status, "first_seen": (prev or {}).get("first_seen", TODAY), "last_seen": TODAY, "ended": False, "row": rec}

for k, v in index.items():
    if k not in current and not v.get("ended") and v.get("row_status") == "active":
        rec = dict(v["row"])
        rec.update(change="ended", valid_from=TODAY, row_status="ended")
        lines.append(rec)
        appended["ended"] += 1
        v.update(ended=True, row_status="ended", last_seen=TODAY)

if lines:
    with open(log_path, "a", encoding="utf-8") as f:
        for rec in lines:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
json.dump(index, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 그 날짜의 전체 사본
snap = os.path.join(H, "snapshots", f"benefits_{TODAY}.jsonl.gz")
with open(os.path.join(U, "benefits.jsonl"), "rb") as src, gzip.open(snap, "wb") as dst:
    shutil.copyfileobj(src, dst)

# 로그를 펼친 표(valid_to 채움)
log = load(log_path)
by_key = {}
for rec in log:
    by_key.setdefault(rec["key"], []).append(rec)
out = []
for k, versions in by_key.items():
    versions.sort(key=lambda x: x["valid_from"])
    for i, v in enumerate(versions):
        v = dict(v)
        v["valid_to"] = versions[i + 1]["valid_from"] if i + 1 < len(versions) else (v["valid_from"] if v["change"] == "ended" else "")
        out.append(v)
out.sort(key=lambda x: (x.get("brand_ko") or "", x.get("model") or "", x.get("title") or "", x["valid_from"]))
with open(os.path.join(H, "benefits_history.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    w.writeheader()
    for v in out:
        w.writerow({c: v.get(c) for c in COLS})

print(f"이력 누적: 신규 {appended['new']} / 변경 {appended['changed']} / 종료 {appended['ended']} / 기간만료 기록 {appended['expired']}  (누적 {len(log)}행, 항목 {len(by_key)}개)")
