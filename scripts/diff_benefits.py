"""이전 게시본과 비교해 바뀐 혜택을 적는다. 사용: python -I scripts/diff_benefits.py <이전 benefits.jsonl 경로>
결과: docs/CHANGES.md  (추가 / 삭제 / 금액·조건·기간이 바뀐 항목)
- 금액(만원·%·개월)이 바뀐 항목은 '금액 변경'으로 따로 모아 사람이 한 번 더 보게 한다.
- 이전 파일이 없으면 비교를 건너뛴다.
"""
import json, os, re, sys, datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cur_p = os.path.join(ROOT, "data", "unified", "benefits.jsonl")
prev_p = sys.argv[1] if len(sys.argv) > 1 else None
if not prev_p or not os.path.exists(prev_p) or os.path.getsize(prev_p) == 0:
    print("이전 게시본 없음: 변경 비교 생략")
    sys.exit(0)

def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8-sig") if l.strip()]

def key(r):
    return (r["brand_id"], r.get("model") or "", r.get("sub_model") or "", r["title"])

NUM = re.compile(r"\d[\d,.]*\s*(?:만원|만|원|%|개월|명|분)")
def nums(r):
    t = " ".join(str(r.get(k) or "") for k in ("discount", "conditions", "reward", "detail"))
    return sorted(set(re.sub(r"[\s,]", "", x) for x in NUM.findall(t)))

old = {key(r): r for r in load(prev_p)}
new = {key(r): r for r in load(cur_p)}
added = [new[k] for k in new if k not in old]
removed = [old[k] for k in old if k not in new]
amt, other = [], []
for k in new:
    if k in old:
        a, b = old[k], new[k]
        if nums(a) != nums(b) or a.get("max_benefit_krw") != b.get("max_benefit_krw"):
            amt.append((a, b))
        elif any((a.get(f) or "") != (b.get(f) or "") for f in ("conditions", "reward", "period_start", "period_end", "link")):
            other.append((a, b))

L = [f"# 변경 내역 ({datetime.date.today()})", "",
     f"- 추가 {len(added)} · 삭제 {len(removed)} · 금액·숫자 변경 {len(amt)} · 조건·기간 등 변경 {len(other)}",
     "- 금액·숫자가 바뀐 항목은 원문(data/evidence)과 다시 대조했는지 확인한다.", ""]
if amt:
    L.append("## 금액·숫자 변경")
    for a, b in amt:
        L.append(f"- {b['brand_ko']} / {b.get('model') or '공통'} / {b['title'][:40]}")
        L.append(f"  - 이전: {', '.join(nums(a)) or '-'} (최대 {a.get('max_benefit_krw')})")
        L.append(f"  - 지금: {', '.join(nums(b)) or '-'} (최대 {b.get('max_benefit_krw')})")
    L.append("")
for title, items in (("추가", added), ("삭제", removed)):
    if items:
        L.append(f"## {title} ({len(items)}건)")
        for r in items[:40]:
            L.append(f"- {r['brand_ko']} / {r.get('model') or '공통'} / {r['title'][:50]}")
        if len(items) > 40:
            L.append(f"- … 외 {len(items) - 40}건")
        L.append("")
if other:
    L.append("## 조건·기간·링크 변경")
    for a, b in other[:40]:
        L.append(f"- {b['brand_ko']} / {b.get('model') or '공통'} / {b['title'][:40]}")
    L.append("")
open(os.path.join(ROOT, "docs", "CHANGES.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"변경 비교: 추가 {len(added)} / 삭제 {len(removed)} / 금액 변경 {len(amt)} / 기타 변경 {len(other)}  (docs/CHANGES.md)")
