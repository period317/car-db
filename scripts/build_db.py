"""data/sources.json + data/offers/*.json + data/testdrive/*.json -> data/unified/ (jsonl, csv, sqlite, brands.json, manifest.json)
실행: python -I scripts/build_db.py   (car-db 폴더에서)
"""
import json, csv, sqlite3, glob, os, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
OUT = os.path.join(D, "unified")
os.makedirs(OUT, exist_ok=True)

sources = json.load(open(os.path.join(D, "sources.json"), encoding="utf-8"))
BR = {b["id"]: b for b in sources["brands"]}
rows = []
manifest = {}

def man(n):  #万원 -> 원
    return int(round(n * 10000)) if isinstance(n, (int, float)) else None

def add(brand, file, cat, title, model=None, price=None, maxb=None, text=None,
        start=None, end=None, url=None, cap="2026-11-05", conf="medium", note=None):
    url = url or (BR.get(brand) or {}).get("site")  # 개별 URL이 없으면 브랜드 공식 사이트로 대체
    rows.append(dict(
        brand_id=brand, brand_ko=(BR.get(brand) or {}).get("brand_ko"), model=model, category=cat, title=title,
        price_krw=price, max_benefit_krw=maxb, text=(text or "")[:900], period_start=start, period_end=end,
        source_url=url, captured=cap, confidence=conf, note=note, raw_file=file))

KEY_LABEL = {"offers": "구매 혜택", "promotions": "프로모션", "programs": "프로그램", "models": "모델별 혜택",
             "events": "이벤트", "finance_promotion": "금융 프로모션", "common_warranty": "공통 보증"}

def label(brand, key):
    """원본 JSON의 영문 키가 제목으로 새지 않도록 사람이 읽는 제목으로 바꾼다."""
    return f"{(BR.get(brand) or {}).get('brand_ko', brand)} {KEY_LABEL.get(key, key)}"

def j(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))

def flat(x):
    if isinstance(x, list):
        return " / ".join(flat(i) for i in x if i not in ("-", "", None))
    if isinstance(x, dict):
        return "; ".join(f"{k}: {flat(v)}" for k, v in x.items() if v not in ("-", "", None))
    return str(x)

for path in sorted(glob.glob(os.path.join(D, "offers", "*.json"))):
    fn = os.path.relpath(path, D).replace("\\", "/")
    d = json.load(open(path, encoding="utf-8"))
    m = d.get("meta", {})
    bid = m.get("brand_id")
    src = m.get("source_url") or m.get("site") or m.get("index_url")
    n0 = len(rows)

    if bid == "kia":
        for o in d["offers"]:
            add("kia", fn, "price", f"{o['model']} 최다판매 트림 가격", o["model"], price=o.get("price"), url=src, conf="high")
            t = flat([o.get("basic"), o.get("special"), o.get("raw_other")])
            add("kia", fn, "benefit", f"{o['model']} 구매혜택", o["model"], text=t, url=src, conf="medium",
                note="기본혜택은 26년 6~9월 생산분 기준 표기. 라벨 일부 모호")
    elif bid == "hyundai":
        for o in d["offers"]:
            add("hyundai", fn, "benefit", f"{o['model']} 11월 구매혜택", o["model"], price=man(o["price_min_manwon"]),
                maxb=man(o["max_benefit_manwon"]), text=("K-세일 페스타 대상" if o.get("k_sale_festa") else ""),
                start="2026-11-01", end="2026-11-30", url=src, conf="high")
        for e in m.get("related_events", []):
            p = re.findall(r"\d{4}-\d{2}-\d{2}", e["period"])
            add("hyundai", fn, "event", e["name"], text=e["period"], start=p[0] if p else None, end=p[1] if len(p) > 1 else None, url=e["url"], conf="high")
    elif bid == "genesis":
        for o in d["offers"]:
            add("genesis", fn, "benefit", f"{o['model']} 11월 구매혜택", o["model"], price=man(o["base_price_manwon"]),
                maxb=man(o["max_benefit_manwon"]), text=flat([o.get("special_offer"), o.get("tradein")]), start="2026-11-01", end="2026-11-30", url=src, conf="high")
        for e in d.get("events", []):
            add("genesis", fn, "event", e["name"], text=flat([e.get("event1"), e.get("event2")]), start="2026-11-01", end="2026-11-30", url=e["url"], conf="high")
    elif bid == "kgm":
        add("kgm", fn, "finance", "11월 공통 금융 프로모션", text=flat(d["finance_promotion"]) + " | " + flat(d["other_benefits"]), start="2026-11-01", end="2026-11-30", url=src, conf="high")
        for o in d["models"]:
            add("kgm", fn, "price", f"{o['model']} 시작가", o["model"], price=o["price_from"], text=o.get("trims"), url=src, conf="high")
            if o.get("special_benefit"):
                add("kgm", fn, "benefit", f"{o['model']} 스페셜 혜택", o["model"], text=o["special_benefit"], start="2026-11-01", end="2026-11-30", url=src, conf="high")
    elif bid == "bmw":
        for o in d["offers"]:
            for t in o.get("trims", []):
                plans = {k: t[k] for k in ("일반 할부", "스마트 리스", "스마트 할부") if k in t}
                add("bmw", fn, "finance", f"{t['trim']} 월 납입금(만원/월)", o["model"], price=man(t["price"]),
                    text=j(plans) + " " + (t.get("detail") or ""), start="2026-10-01", end="2026-10-31", url=src, conf="medium",
                    note="페이지 적용기간 2026-10 표기, 11월 유효 불명")
    elif bid == "renault":
        for o in d["models"]:
            p = o.get("price_from") or o.get("price_gasoline_from")
            add("renault", fn, "benefit", f"{o['model']} 11월 르노 세일 페스타", o["model"], price=p,
                text=flat([o.get("installment"), o.get("limited_discount_26MY") or o.get("limited_discount"), o.get("special")]), start="2026-11-01", end="2026-11-30", url=src, conf="high")
    elif bid == "tesla":
        for o in d["prices_krw"]:
            add("tesla", fn, "price", f"{o['model']} {o['trim']}", o["model"], price=o["price"], url=d["meta"]["site"], conf="high", note="보조금 미반영")
    elif bid == "byd":
        for o in d["prices_manwon"]:
            if "trims" in o:
                for k, v in o["trims"].items():
                    add("byd", fn, "price", k, o["model"], price=man(v), url=d["meta"]["site"], conf="medium")
            else:
                for v in o["prices"]:
                    add("byd", fn, "price", f"{o['model']} ({v}만원 트림)", o["model"], price=man(v), url=d["meta"]["site"], conf="medium")
        for e in d.get("events", []):
            ps_ = re.findall(r"\d{4}-\d{2}-\d{2}", e["period"])
            mdl = "BYD SEALION 6 DM-i" if "SEALION 6 DM-i" in e["name"] else None  # 이벤트가 특정 모델 대상이면 모델 표기
            add("byd", fn, "event", e["name"], mdl, text=e["period"], start=ps_[0] if ps_ else None, end=ps_[1] if len(ps_) > 1 else None,
                url=d["meta"]["urls"]["events"], conf="high")
    elif bid == "chevrolet":  # 혜택이 적용되는 모델별로 레코드를 나눈다
        for o in d["offers"]:
            for mdl in o["models"]:
                add("chevrolet", fn, "benefit", f"{mdl} 11월 구매혜택", mdl, maxb=man(o.get("max_benefit_manwon")),
                    text=flat({"offers_faq_detail": o.get("offers_faq_detail"), "breakdown_manwon": o.get("breakdown_manwon"), "trade_in": o.get("trade_in")}),
                    start="2026-11-01", end="2026-11-30", url=src, conf="high", note=o.get("breakdown_note"))
    elif bid == "mini":  # 내연기관 / 전기차 대상을 나눈다
        fp = d["finance_promotion"]
        ev = [x for x in fp["target_models"] if x.startswith("올일렉트릭")]
        ice = [x for x in fp["target_models"] if not x.startswith("올일렉트릭")]
        add("mini", fn, "finance", "MINI 스마일 운용리스 최대 3개월 월 납입금 0원", "26년식 내연기관 전 모델",
            text=flat({"headline": fp["headline"], "support": fp["support"], "benefit": fp["benefit_1"], "conditions": fp["conditions"],
                       "example": fp["example"], "대상 모델": ", ".join(ice)}), url=src, conf="medium", note="이달 프로모션 페이지(this-month-special-offer)는 본문이 비어 있어 읽지 못함")
        add("mini", fn, "finance", "MINI 전기차 운용리스 이용 시 풀케어 1년 제공", "MINI 전기차 전 모델",
            text=flat({"benefit": fp["benefit_2"], "대상 모델": ", ".join(ev)}), url=src, conf="medium")
    elif bid == "mercedes":
        for p in d["promotions"]:
            if p.get("models_seen"):
                for mdl in p["models_seen"]:
                    add("mercedes", fn, "benefit", f"{mdl} {p['name']}", mdl, text=flat(p["text"]), url=src, conf="medium", note=p.get("models_note"))
            else:
                mdl = "AMG 전 모델" if "AMG" in p["name"] else None
                add("mercedes", fn, "benefit", p["name"], mdl, text=flat(p.get("text")), start="2026-11-01" if p.get("period") else None,
                    end="2026-11-30" if p.get("period") else None, url=src, conf="medium")
    elif bid == "volvo":
        for p in d["programs"]:
            if p.get("benefit_krw_vat_included"):
                for names, amt in p["benefit_krw_vat_included"].items():
                    for mdl in [x.strip() for x in names.split(",")]:
                        add("volvo", fn, "benefit", f"{mdl} {p['name']}", mdl, maxb=amt, text=flat({"since": p.get("since"), "eligibility": p.get("eligibility"), "혜택": f"{amt:,}원(VAT 포함)"}),
                            url=m.get("other_urls", {}).get("family_repurchase") or src, conf="high")
            else:
                ps_ = re.findall(r"\d{4}-\d{2}-\d{2}", p.get("apply_period") or "")
                add("volvo", fn, "event" if p.get("benefits") else "benefit", p["name"], text=flat({k: v for k, v in p.items() if k != "name"}),
                    start=ps_[0] if ps_ else None, end=ps_[1] if len(ps_) > 1 else None,
                    url=(m.get("other_urls", {}).get("ex90_campaign") if p.get("benefits") else None) or src, conf="high")
    elif bid is None and m.get("brand_ids") == ["ford", "lincoln"]:
        ended = flat([f"{e['name']} {e['period']} ({e['status']})" for e in d.get("ended_campaigns", [])])
        for bi in m["brand_ids"]:
            add(bi, fn, "status", f"{(BR.get(bi) or {}).get('brand_ko', bi)} 현재 진행 중인 공식 프로모션 없음",
                text=f"공식 사이트 프로모션 페이지에 진행 중인 이벤트 없음. 종료된 캠페인: {ended}. 판매 모델: {', '.join(d['models'][bi])}", url=m["urls"].get(f"{bi}_promotion") or src, conf="medium")
    elif bid == "cadillac":
        for o in d["offers"]:
            add("cadillac", fn, "benefit", f"{o['model']} 11월 프로모션", o["model"], text=flat({k: v for k, v in o.items() if k != "model"}), start="2026-11-01", end="2026-11-30", url=src, conf="high")
    elif bid == "landrover":
        for o in d["offers"]:
            add("landrover", fn, "finance", f"{o['model']} 금융 예시", o["model"], price=o.get("price_from_krw"), text=flat({k: v for k, v in o.items() if k not in ("model", "price_from_krw")}), url=m["offers_index"], conf="medium")
    elif "brands" in d:  # others_*.json
        for b in d["brands"]:
            add(b["id"], fn, "status", f"{(BR.get(b['id']) or {}).get('brand_ko', b['id'])} 공식 사이트 점검 결과", text=f"{b['status']}: {b['finding']}", url=b.get("site"), conf="low")
    else:
        # 일반 폴백: 대표 리스트 키의 각 원소를 한 레코드로
        ids = m.get("brand_ids") or [bid]
        keys = [k for k in ("offers", "promotions", "programs", "models", "events", "finance_promotion", "common_warranty") if k in d and isinstance(d[k], (list, dict))]
        for bid0 in ids:
            made = 0
            for k in keys:
                items = d[k] if isinstance(d[k], list) else [d[k]]
                for it in items:
                    cat = "event" if k == "events" else ("finance" if k == "finance_promotion" else "benefit")
                    if isinstance(it, dict):
                        name = it.get("model") or it.get("name") or it.get("program") or it.get("title") or label(bid0, k)
                        add(bid0, fn, cat, str(name), it.get("model"), text=flat({a: b for a, b in it.items() if a not in ("model", "name")}), url=src, conf="medium")
                        made += 1
                    elif isinstance(it, str) or k == "finance_promotion":
                        add(bid0, fn, cat, label(bid0, k), text=flat(items if isinstance(d[k], list) else d[k]), url=src, conf="medium")
                        made += 1
                        break
            if made == 0 and m.get("finding"):
                add(bid0, fn, "status", f"{(BR.get(bid0) or {}).get('brand_ko', bid0)} 공식 사이트 점검 결과", text=m["finding"], url=src, conf="low")
    manifest[fn] = dict(brand_id=bid or m.get("brand_ids"), records=len(rows) - n0, captured=m.get("captured"),
                        source=src, caveat=(m.get("caveat") or m.get("caveats") or m.get("STALE_WARNING") or m.get("finding")))

# 시승 파일은 요약만
for path in sorted(glob.glob(os.path.join(D, "testdrive", "*.json"))):
    if os.path.basename(path) == "index.json":
        continue
    fn = os.path.relpath(path, D).replace("\\", "/")
    d = json.load(open(path, encoding="utf-8"))
    n0 = len(rows)
    base = os.path.basename(path)
    ids = ["genesis", "kgm"] if "genesis_kgm" in base else [d.get("brand_id", base.split("_")[0])]
    for b in ids:
        sub = d.get(b, d) if b in d else d
        add(b, fn, "testdrive", f"{(BR.get(b) or {}).get('brand_ko', b)} 시승 신청 정보", text=j(sub), url=(sub.get("apply") if isinstance(sub, dict) else None) or (d.get("sources") or {}).get("apply"), conf="medium")
    manifest[fn] = dict(brand_id=ids, records=len(rows) - n0, captured=d.get("captured"), source=None, caveat=None)

# 정리: 카테고리/브랜드 별 통계
for r in rows:
    r["id"] = None
for i, r in enumerate(rows, 1):
    r["id"] = i

cols = ["id", "brand_id", "brand_ko", "model", "category", "title", "price_krw", "max_benefit_krw", "text",
        "period_start", "period_end", "source_url", "captured", "confidence", "note", "raw_file"]
with open(os.path.join(OUT, "offers.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps({c: r.get(c) for c in cols}, ensure_ascii=False) + "\n")
with open(os.path.join(OUT, "offers.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c) for c in cols})

# brands.json: 사이트·금융사 + 수집 현황
cov = {}
for r in rows:
    cov.setdefault(r["brand_id"], set()).add(r["category"])
brands_out = []
for b in sources["brands"]:
    brands_out.append(dict(id=b["id"], brand_ko=b["brand_ko"], brand_en=b["brand_en"], group=b.get("group"), origin=b.get("origin"),
                           site=b.get("site"), finance=b.get("finance"), status=b.get("status"), note=b.get("note"),
                           collected_categories=sorted(cov.get(b["id"], [])), has_data=b["id"] in cov))
json.dump(brands_out, open(os.path.join(OUT, "brands.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(dict(generated=datetime.date.today().isoformat(), total_records=len(rows), files=manifest),
          open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# SQLite
dbp = os.path.join(OUT, "cardb.sqlite")
if os.path.exists(dbp):
    os.remove(dbp)
con = sqlite3.connect(dbp)
con.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, brand_id TEXT, brand_ko TEXT, model TEXT, category TEXT, title TEXT, price_krw INTEGER, max_benefit_krw INTEGER, text TEXT, period_start TEXT, period_end TEXT, source_url TEXT, captured TEXT, confidence TEXT, note TEXT, raw_file TEXT)")
con.executemany("INSERT INTO records VALUES(%s)" % ",".join("?" * len(cols)), [[r.get(c) for c in cols] for r in rows])
con.execute("CREATE TABLE brands(id TEXT PRIMARY KEY, brand_ko TEXT, brand_en TEXT, grp TEXT, origin TEXT, site TEXT, finance_json TEXT, note TEXT, has_data INTEGER)")
con.executemany("INSERT INTO brands VALUES(?,?,?,?,?,?,?,?,?)", [(b["id"], b["brand_ko"], b["brand_en"], b["group"], b["origin"], b["site"], json.dumps(b["finance"], ensure_ascii=False), b.get("note") or b.get("status"), int(b["has_data"])) for b in brands_out])
# 시승 색인: 신청 가능 여부 vs 시승 이벤트 구분
td_path = os.path.join(D, "testdrive", "index.json")
td_rows = []
if os.path.exists(td_path):
    td = json.load(open(td_path, encoding="utf-8"))
    for t in td["brands"]:
        b = BR.get(t["brand_id"]) or {}
        td_rows.append(dict(
            brand_id=t["brand_id"], brand_ko=b.get("brand_ko"),
            can_apply_online=t.get("can_apply_online"), apply_url=t.get("apply_url"),
            models=", ".join(t["models"]) if t.get("models") else None, policy=t.get("policy"),
            has_event=bool(t.get("has_event")), event_name=t.get("event_name"), event_benefit=t.get("event_benefit"),
            event_period=t.get("event_period"), event_url=t.get("event_url"),
            event_detail_collected=t.get("event_detail_collected"), detail_level=t.get("detail_level"), note=t.get("note")))
    json.dump(td_rows, open(os.path.join(OUT, "testdrive.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    tcols = list(td_rows[0].keys())
    with open(os.path.join(OUT, "testdrive.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=tcols)
        w.writeheader()
        for r in td_rows:
            w.writerow(r)
    con.execute("CREATE TABLE testdrive(%s)" % ",".join(tcols))
    con.executemany("INSERT INTO testdrive VALUES(%s)" % ",".join("?" * len(tcols)), [[r[c] for c in tcols] for r in td_rows])
    print("testdrive rows:", len(td_rows), "| apply:", sum(1 for r in td_rows if r["can_apply_online"]), "| events:", sum(1 for r in td_rows if r["has_event"]))
con.commit()
con.close()
print("records:", len(rows))
by = {}
for r in rows:
    by[r["category"]] = by.get(r["category"], 0) + 1
print(by)
print("brands with data:", sum(1 for b in brands_out if b["has_data"]), "/", len(brands_out))
print("no data:", [b["id"] for b in brands_out if not b["has_data"]])
