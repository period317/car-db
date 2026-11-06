"""과거·현재 월별 혜택 조회. 사용 예:
  python -I scripts/query_history.py --ym 2026-11                      # 2026-11 에 게시돼 있던 혜택 전체
  python -I scripts/query_history.py --ym 2026-10 --brand BMW          # 브랜드(한글/영문 부분일치)
  python -I scripts/query_history.py --ym 2026-11 --model 그랜저 --discount-only
  python -I scripts/query_history.py --as-of 2026-11-06 --brand 기아   # 특정 날짜 기준
  python -I scripts/query_history.py --changes --since 2026-11-01       # 그 날 이후 바뀐 것(신규·변경·종료)
  python -I scripts/query_history.py --months                           # 누적된 월 목차
데이터: data/history/benefits_history.jsonl (누적 로그). 지우거나 고치지 않는다.
"""
import json, os, sys, argparse, calendar, collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "history", "benefits_history.jsonl")

ap = argparse.ArgumentParser()
ap.add_argument("--ym"); ap.add_argument("--as-of"); ap.add_argument("--brand"); ap.add_argument("--model"); ap.add_argument("--event")
ap.add_argument("--discount-only", action="store_true"); ap.add_argument("--changes", action="store_true"); ap.add_argument("--since")
ap.add_argument("--months", action="store_true"); ap.add_argument("--limit", type=int, default=300)
a = ap.parse_args()

log = [json.loads(l) for l in open(LOG, encoding="utf-8") if l.strip()]
by_key = collections.defaultdict(list)
for r in log:
    by_key[r["key"]].append(r)
versions = []
for k, vs in by_key.items():
    vs.sort(key=lambda x: x["valid_from"])
    for i, v in enumerate(vs):
        v = dict(v)
        v["valid_to"] = vs[i + 1]["valid_from"] if i + 1 < len(vs) else (v["valid_from"] if v["change"] == "ended" else "")
        versions.append(v)

def match(v):
    if a.brand and a.brand.lower() not in f"{v.get('brand_ko') or ''} {v.get('brand_id') or ''}".lower():
        return False
    if a.model and a.model.lower() not in f"{v.get('model') or ''} {v.get('sub_model') or ''}".lower():
        return False
    if a.event and a.event.lower() not in (v.get("event_name") or "").lower():
        return False
    if a.discount_only and not (v.get("discount_amount_krw") or v.get("discount_rate_pct")):
        return False
    return True

if a.months:
    c = collections.Counter()
    for v in versions:
        if v["change"] in ("new", "changed", "expired"):
            c[v["valid_from"][:7]] += 1
    for ym, n in sorted(c.items()):
        print(f"{ym}: 새로 기록·변경된 항목 {n}건")
    sys.exit(0)

if a.changes:
    since = a.since or "0000-00-00"
    rows = [v for v in versions if v["valid_from"] >= since and match(v)]
else:
    if a.as_of:
        lo = hi = a.as_of
    elif a.ym:
        y, m = map(int, a.ym.split("-"))
        lo, hi = f"{a.ym}-01", f"{a.ym}-{calendar.monthrange(y, m)[1]:02d}"
    else:
        ap.error("--ym 또는 --as-of 또는 --changes 중 하나가 필요합니다")
    # 그 기간의 혜택: 공식 기간(period_start/end)이 적힌 항목은 기간이 그 월과 겹치면 포함(수집이 늦어도 과거 월로 잡힘),
    # 기간이 없는 항목은 우리가 관측한 구간(valid_from ~ valid_to)이 그 월과 겹치면 포함. 종료(ended) 행 자체는 제외.
    def in_range(v):
        if v.get("period_start") or v.get("period_end"):
            return (v.get("period_start") or "0000-00-00") <= hi and (v.get("period_end") or "9999-99-99") >= lo
        return v["valid_from"] <= hi and (not v["valid_to"] or v["valid_to"] >= lo)
    cand = collections.defaultdict(list)
    for v in versions:
        if v["change"] != "ended" and in_range(v) and match(v):
            cand[v["key"]].append(v)
    rows = []
    for k, vs in cand.items():   # 같은 항목의 여러 버전 중 그 기간 끝 시점에 유효했던 것(없으면 가장 이른 것) 하나만
        upto = [x for x in vs if x["valid_from"] <= hi]
        rows.append(max(upto, key=lambda x: x["valid_from"]) if upto else min(vs, key=lambda x: x["valid_from"]))
    rows.sort(key=lambda x: (x.get("brand_ko") or "", x.get("model") or "", x.get("title") or ""))

print("| 브랜드 | 모델 | 세부모델 | 이벤트명 | 할인구분 | 할인금액(만원) | 할인율(%) | 기간 | 변경 | 기록일 | 종료·교체일 |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for v in rows[:a.limit]:
    amt = f"{v['discount_amount_krw'] / 10000:g}" if v.get("discount_amount_krw") else "-"
    rate = f"{v['discount_rate_pct']:g}" if v.get("discount_rate_pct") else "-"
    per = f"{v.get('period_start') or '?'}~{v.get('period_end') or '?'}" if (v.get("period_start") or v.get("period_end")) else "기간 미표기"
    print(f"| {v.get('brand_ko') or '-'} | {v.get('model') or '-'} | {v.get('sub_model') or '-'} | {v.get('event_name') or '-'} | {v.get('discount_type') or '-'} | {amt} | {rate} | {per} | {v['change']} | {v['valid_from']} | {v['valid_to'] or '현재'} |")
print(f"\n총 {len(rows)}건" + (f" (상위 {a.limit}건만 표시)" if len(rows) > a.limit else ""))
