"""오프라인 AI용 패키지 생성: dist/car_db_for_ai.md (단일 파일) + dist/car-db-bundle.zip
실행: python -I scripts/export_bundle.py   (build_db.py 실행 후)
"""
import json, os, zipfile, datetime, collections

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
L.append(f"- 기준일: 2026-11-05 수집 / 생성 {datetime.date.today().isoformat()} / 레코드 {len(recs)}건 / 브랜드 {len(brands)}곳")
L.append("- 출처: 각 브랜드 공식 홈페이지·공식 금융사 (수집 당시 화면). 인터넷 없이 이 파일만으로 답하세요.\n")
L.append("## AI 사용 지침")
L.append("1. 답할 때 **브랜드·모델·수치·기간**을 이 파일에서 그대로 인용하고, 없으면 '이 DB에 없음'이라고 말하세요. 추측 금지.")
L.append("2. 금액 단위: 만원(표기 그대로). 최대혜택은 조건 합산치(제휴금융 이용 등)이므로 개인 조건에 그대로 적용하지 말 것.")
L.append("3. **유효기간 주의**: BMW는 10월 프로모션(11월 만료 가능), 기아 기본혜택은 '26년 6~9월 생산분'. 기간이 없으면 '기간 불명' 명시.")
L.append("4. 벤츠·포르쉐·마세라티 등은 금액 비공개(딜러 문의)이며 '혜택 없음'이 아님.")
L.append("5. 혼다·시트로엥·맥라렌·재규어는 국내 신차 판매 여부 불확실.")
L.append("6. `[신뢰도]` high=페이지에서 수치 직접 확인, medium=해석 필요, low=점검 결과/추정.\n")

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
    grp = collections.OrderedDict()
    for b in ben:
        grp.setdefault(b["brand_ko"], []).append(b)
    for name, items in grp.items():
        L.append(f"### {name}")
        for b in items:
            who = " / ".join(x for x in [b.get("model"), b.get("sub_model")] if x) or "브랜드 공통"
            per = f"{b['period_start'] or '?'}~{b['period_end'] or '?'}" if (b.get("period_start") or b.get("period_end")) else "기간 미표기"
            vtag = {"검증됨": "원문 대조 완료", "일부 미확인": "원문 대조 불일치(확인 필요)", "증거 없음": "원문 대조 안 됨"}.get(b.get("verification"), "")
            L.append(f"- **[{b['types']}] {b['title']}** — 차종: {who} | 기준 {b['ym']} | 기간 {per} ({b['period_status']}) | 검증: {vtag}")
            if b.get("discount"):
                L.append(f"  - 할인·금융: {b['discount'][:500]}")
            if b.get("conditions"):
                L.append(f"  - 조건: {b['conditions'][:500]}")
            if b.get("reward"):
                L.append(f"  - 증정·경품: {b['reward'][:400]}")
            if not (b.get("discount") or b.get("conditions") or b.get("reward")) or len(b.get("detail") or "") > 0:
                L.append(f"  - 세부내용: {(b['detail'] or '')[:700]}")
            if b.get("link"):
                L.append(f"  - 링크: {b['link']}")
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
