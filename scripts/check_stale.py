"""갱신이 필요한 브랜드 점검. 실행: python -I scripts/check_stale.py [기준일 YYYY-MM-DD] [최대경과일=14]
출력: 기간 만료 / 수집 후 N일 경과 / 데이터 없음 브랜드 → 다음 수집 우선순위"""
import json, os, sys, datetime, collections
sys.stdout.reconfigure(encoding="utf-8")
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

# 매주 빠짐없이 다시 읽을 공식 페이지(이벤트 목록 + 구매혜택). 매월 1~7일에는 전 브랜드 전체 갱신.
wp = os.path.join(ROOT, "data", "watch_pages.json")
if os.path.exists(wp):
    watch = json.load(open(wp, encoding="utf-8"))["brands"]
    full_month = today.day <= 7
    print(f"\n[주간 필수 확인] {'매월 1~7일: 전 브랜드 전체 갱신(새 달 전환)' if full_month else '이번 주: 아래 모든 브랜드의 이벤트 목록·구매혜택 페이지를 다시 읽고 새로 생기거나 바뀐 것을 반영'} / 브랜드 {len(watch)}곳")
    for w in watch:
        pages = [("이벤트", u) for u in w["event_list"]] + [("혜택", u) for u in w["benefit_pages"]]
        print(f"- {w['brand_ko']}({w['brand_id']}): " + " | ".join(f"{k} {u}" for k, u in pages) + (f"   ※ {w['note']}" if w.get("note") else ""))
    # 종료 임박·종료된 이벤트(이력 기준 현재 유효한데 기간이 곧 끝나거나 이미 끝난 것)
    bp = os.path.join(U, "benefits.jsonl")
    if os.path.exists(bp):
        soon = []
        for l in open(bp, encoding="utf-8"):
            r = json.loads(l)
            if r.get("period_end"):
                left = (datetime.date.fromisoformat(r["period_end"]) - today).days
                if left <= 7:
                    soon.append((left, r["brand_ko"], r.get("event_name") or r["title"], r["period_end"]))
        if soon:
            print("\n[종료 임박/종료] 기간이 7일 안에 끝나거나 끝난 항목(페이지에서 아직 보이는지 확인)")
            for left, bk, nm, pe in sorted(soon)[:25]:
                print(f"- {bk} / {nm[:40]} — {pe} ({'종료됨' if left < 0 else f'{left}일 남음'})")
