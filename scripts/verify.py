"""sources.json의 모든 URL 접속 검증. 결과를 verified 필드에 기록."""
import json, ssl, sys, datetime, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

PATH = sys.argv[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
ctx = ssl.create_default_context()

def check(url):
    if not url:
        return None
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            body = r.read(200000).decode("utf-8", "ignore")
            return {"status": r.status, "final_url": r.geturl(), "html_bytes": len(body), "error": None}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": url, "html_bytes": 0, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"status": None, "final_url": url, "html_bytes": 0, "error": type(e).__name__ + ": " + str(e)[:120]}

data = json.load(open(PATH, encoding="utf-8"))
targets = []
for b in data["brands"]:
    targets.append((b, "site", b["site"]))
    for f in b["finance"]:
        targets.append((f, "url", f["url"]))

with ThreadPoolExecutor(12) as ex:
    results = list(ex.map(lambda t: check(t[2]), targets))

today = datetime.date.today().isoformat()
for (obj, key, url), res in zip(targets, results):
    if res:
        res["checked"] = today
        obj["verified" if key == "url" else "site_verified"] = res

json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for (obj, key, url), res in zip(targets, results):
    if res:
        print(res["status"], url, "->", res["final_url"] if res["final_url"] != url else "", res["error"] or "")
