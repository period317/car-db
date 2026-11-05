"""갱신이 필요한 브랜드 점검. 실행: python -I scripts/check_stale.py [기준일 YYYY-MM-DD] [최대경과일=14]
출력: 기간 만료 / 수집 후 N일 경과 / 데이터 없음 브랜드 → 다음 수집 우선순위"""
import json, os, sys, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = os.path.join(ROOT, "data", "unified")
today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
maxage = int(sys.argv[2]) if len(sys.argv) > 2 else 14
recs = [json.loads(l) for l in open(os.path.join(U, "offers.jsonl"), encoding="utf-8")]
brands = {b["id"]: b for b in json.load(open(os.path.join(U, "brands.json"), encoding="utf-8"))}

expired, old, seen = collections.defaultdict(list), {}, set()
for r in recs:
    seen.add(r["brand_id"])
    if r["period_end"] and datetime.date.fromisoformat(r["period_end"]) < today:
        expired[r["brand_id"]].append(r["period_end"])
    if r["captured"]:
        age = (today - datetime.date.fromisoformat(r["captured"])).days
        old[r["brand_id"]] = max(old.get(r["brand_id"], 0), age)
out = []
for b in brands:
    reasons = []
    if b in expired: reasons.append("기간만료 " + max(expired[b]))
    if old.get(b, 0) >= maxage: reasons.append(f"수집 후 {old[b]}일 경과")
    if b not in seen: reasons.append("데이터 없음")
    if reasons:
        out.append((b, brands[b]["brand_ko"], "; ".join(reasons)))
print(f"기준일 {today} / 갱신 필요 {len(out)}곳")
for b, ko, why in out:
    print(f"- {ko}({b}): {why}")
