"""쿠팡 파트너스 링크 채우기 — deals.json에서 링크(cp)가 없는 상품만 쿠팡 검색 딥링크로 채움.

사용:  COUPANG_ACCESS_KEY=... COUPANG_SECRET_KEY=... python3 tools/coupang_links.py [--max-calls 10]
키는 절대 저장소에 넣지 말 것(.env는 .gitignore에 있음). 키 원본은 사용자 집 컴퓨터 Documents/golla/coupang_keys.txt.

호출 제한 주의: 공식 확인 전까지 '1시간 30회 이하'로 운영(넘기면 정지될 수 있다는 자료가 있음).
  - 딥링크 1번 호출에 URL 20개씩 묶음 → 기본 최대 10번(=200개)만 부르고 멈춤
  - 같은 검색 주소는 tools/data/link_cache.json에 저장해 다음 주에 재사용(새 상품만 호출)
"""
import argparse, hashlib, hmac, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DEALS = os.path.join(ROOT, "deals.json"); CACHE = os.path.join(HERE, "data", "link_cache.json")
HOST = "https://api-gateway.coupang.com"; PATH = "/v2/providers/affiliate_open_api/apis/openapi/deeplink"


def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1); os.environ.setdefault(k.strip(), v.strip())


def keyword(name):
    n = unicodedata.normalize("NFKC", name)
    n = re.sub(r"\(.*?\)", " ", n); n = re.sub(r"[#*]", " ", n)
    n = re.sub(r"\s+\d+(\.\d+)?\s*(개|입|매|캔|팩|PK|PR|CT|C|KG|G|ML|L|M|롤|봉|EA|구|P|정|X\d+).*$", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip() or name


def call(urls, ak, sk):
    dt = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
    sig = hmac.new(sk.encode(), (dt + "POST" + PATH).encode(), hashlib.sha256).hexdigest()
    req = urllib.request.Request(HOST + PATH, method="POST", data=json.dumps({"coupangUrls": urls}).encode(), headers={
        "Authorization": f"CEA algorithm=HmacSHA256, access-key={ak}, signed-date={dt}, signature={sig}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return {o["originalUrl"]: o["shortenUrl"] for o in json.load(r).get("data", [])}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--max-calls", type=int, default=10); ap.add_argument("--wait", type=float, default=5)
    a = ap.parse_args(); load_env()
    ak, sk = os.environ.get("COUPANG_ACCESS_KEY"), os.environ.get("COUPANG_SECRET_KEY")
    D = json.load(open(DEALS, encoding="utf-8")); cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    todo = {}
    for x in D["items"]:
        if x.get("cp"): continue
        u = "https://www.coupang.com/np/search?q=" + urllib.parse.quote(keyword(x["n"]))
        if u in cache: x["cp"] = cache[u]
        else: todo.setdefault(u, []).append(x)
    print(f"캐시로 채움 후 남은 검색 주소 {len(todo)}개")
    urls = list(todo); calls = 0
    if urls and not (ak and sk): sys.exit("COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 가 없어요 (.env 또는 환경변수)")
    for i in range(0, len(urls), 20):
        if calls >= a.max_calls: print(f"호출 {calls}번에서 멈춤(제한 보호). 남은 {len(urls)-i}개는 다음에."); break
        got = call(urls[i:i + 20], ak, sk); calls += 1
        for u, s in got.items():
            cache[u] = s
            for x in todo.get(u, []): x["cp"] = s
        time.sleep(a.wait)
    json.dump(D, open(DEALS, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True); json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"API 호출 {calls}번 · 링크 있는 상품 {sum(1 for x in D['items'] if x.get('cp'))}/{len(D['items'])}")


if __name__ == "__main__":
    main()
