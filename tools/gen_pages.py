# 골라골라 검색용 정적 페이지 생성기
# 사용: python3 tools/gen_pages.py  (저장소 루트에서, deals.json 기준)
# 만드는 것: /this-week/, /ending/, /c/<분류>/, 홈 TOP20 미리 그리기, sitemap.xml
import json, re, html, os
from datetime import date, datetime, timedelta, timezone

SITE = "https://gollagolla.kr"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "deals.json"), encoding="utf-8"))
META = D.get("meta", {})
TODAY = datetime.now(timezone(timedelta(hours=9))).date()

def to_d(s):
    if not s: return None
    a = [int(v) for v in s.split("-")]
    if len(a) == 3: return date(*a)
    d = date(TODAY.year, a[0], a[1])
    if (d - TODAY).days > 180: d = date(TODAY.year - 1, a[0], a[1])
    elif (TODAY - d).days > 180: d = date(TODAY.year + 1, a[0], a[1])
    return d

items = []
for x in D["items"]:
    e = to_d(x.get("e"))
    if e and e < TODAY: continue
    x = dict(x); x["_e"] = e; x["_s"] = to_d(x.get("s"))
    x["pc"] = round((x["o"] - x["p"]) / x["o"] * 100) if x.get("o", 0) > x["p"] else 0
    items.append(x)
items.sort(key=lambda x: x.get("rk") or 10**9)
ok = [x for x in items if not x.get("chk")]

esc = lambda s: html.escape(str(s or ""), quote=True)
won = lambda n: f"{n:,}원"
md = lambda d: f"{d.month}.{d.day}" if d else ""
mon = TODAY - timedelta(days=TODAY.weekday()); sun = mon + timedelta(days=6)
PERIOD = f"{mon.month}월 {mon.day}일~{sun.month}월 {sun.day}일"
WEEK = META.get("week") or f"{TODAY.month}월 {(TODAY.day-1)//7+1}주차"

KW = [(r"논알콜|무알콜", "논알콜"), (r"맥주|와인|샤도네|위스키|짐빔|하이네켄|코젤|소주", "홈술"), (r"하겐다즈|교자|만두|아이스크림|냉동", "냉동실 쟁여템"),
      (r"삼겹|돈육|목살|소고기|한우|닭|갈비", "고기 특가"), (r"단감|사과|귤|딸기|샤인|포도|바나나", "제철 과일"), (r"하리보|젤리|과자|초콜릿|킨더|프링글스|맛밤|견과|쿠키", "간식 쟁이기"),
      (r"커피|캡슐|원두", "홈카페"), (r"햇반|즉석|주먹밥|라면|스팸|통조림", "자취템"), (r"세제|다우니|페브리즈|휴지|티슈|크리넥스|치약|센소다인|리스테린|건전지|듀라셀", "생필품 쟁이기"),
      (r"핫팩|담요|패딩|다운|스타킹|양말|부츠|기모", "추위 대비"), (r"트리|장식|리스|크리스마스", "크리스마스")]
UNIT = {"개": "개", "입": "개", "캔": "캔", "봉": "봉", "롤": "롤", "매": "매", "PR": "켤레", "PK": "개", "P": "개", "팩": "개", "CT": "개", "정": "정"}
def tags(x):
    T = []; n = x["n"].upper()
    m = re.search(r"(\d+)\s*(개|입|캔|봉|롤|매|PR|PK|팩|CT|정|P)(?![A-Z])", n)
    if m and int(m.group(1)) >= 2 and x["p"] / int(m.group(1)) >= 50:
        T.append(f"1{UNIT[m.group(2)]} {round(x['p']/int(m.group(1))):,}원꼴")
    kw = next((t for r, t in KW if re.search(r, x["n"])), None)
    if kw: T.append(kw)
    if x["_e"] and (x["_e"] - TODAY).days <= 3: T.append("곧 마감")
    elif x["pc"] >= 30: T.append(f"{x['pc']}% 할인")
    if len(T) < 3 and x["p"] <= 10000: T.append("만원 이하")
    return T[:3]

def buy(x):
    if not x.get("cp"): return ""
    same = "AFFSDP" in x["cp"]
    return f'<a class="cp" href="{esc(x["cp"])}" target="_blank" rel="noopener sponsored">{"쿠팡 같은 상품 보기" if same else "쿠팡에서 검색"}</a>'

def row(i, x):
    tg = "".join(f'<span class="tg">#{esc(t)}</span>' for t in tags(x))
    end = f'{md(x["_e"])}까지' if x["_e"] else "온라인 상시"
    was = f'<s>{won(x["o"])}</s> ' if x["o"] > x["p"] else ""
    code = f' · 상품코드 {esc(x["id"])}' if x.get("id") else ""
    return (f'<li class="it" data-id="{esc(x.get("id",""))}"><span class="no">{i}</span><div class="bd"><h3>{esc(x["n"])}</h3>'
            f'<p class="mt">{esc(x["c"])}{code} · {end}</p>{f"<p class=tgs>{tg}</p>" if tg else ""}</div>'
            f'<div class="pr"><span class="sl">코스트코 매장가</span>{was}<b>{won(x["p"])}</b>'
            f'{f"<em>-{x[chr(112)+chr(99)]}%</em>" if x["pc"] else ""}{buy(x)}</div></li>')

CSS = """:root{color-scheme:light dark;--bg:light-dark(#f4f1ea,#15110f);--paper:light-dark(#fff,#211b18);--ink:light-dark(#16110f,#f7f2ec);--mute:light-dark(#4f4741,#cdc3b9);--red:light-dark(#d4211a,#ff6a5e);--line:light-dark(#e3dbd0,#3d342f)}
*{box-sizing:border-box;min-width:0}body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.6 "Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif;word-break:keep-all}
a{color:inherit}.top{background:var(--red);color:#fff;padding:12px max(5vw,16px)}.top a{color:#fff;font-weight:900;font-size:22px;text-decoration:none}
.disc{background:#ffd400;color:#16110f;font-size:13px;font-weight:700;text-align:center;padding:6px 12px}
main{max-width:980px;margin:0 auto;padding:28px max(4vw,16px) 40px}h1{font-size:clamp(28px,5vw,40px);line-height:1.2;margin:0 0 8px;font-weight:900}
.lead{color:var(--mute);margin:0 0 18px}.nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}.nav a{border:2px solid var(--line);border-radius:20px;padding:6px 14px;text-decoration:none;font-weight:700;font-size:15px;background:var(--paper)}
ol{list-style:none;margin:0;padding:0}.it{display:grid;grid-template-columns:36px minmax(0,1fr) auto;gap:12px;padding:14px;background:var(--paper);border:1px solid var(--line);border-radius:12px;margin-bottom:10px;align-items:start}
.no{font-weight:900;font-size:20px;text-align:center;background:var(--bg);border-radius:8px;line-height:36px}.it h3{margin:0;font-size:17px;line-height:1.4}.mt{margin:2px 0 0;color:var(--mute);font-size:14px}
.tgs{margin:6px 0 0;display:flex;flex-wrap:wrap;gap:4px}.tg{font-size:13px;font-weight:700;color:var(--red);background:light-dark(#fdecea,#3a1d1a);padding:2px 8px;border-radius:4px}
.pr{text-align:right;white-space:nowrap}.sl{display:block;font-size:12px;color:var(--mute);font-weight:700}.pr s{color:var(--mute);font-size:14px}.pr b{display:block;font-weight:900;font-size:21px;color:var(--red)}
.pr em{font-style:normal;font-weight:900;background:#ffd400;color:#16110f;padding:1px 6px;border-radius:4px;font-size:13px}.cp{display:inline-flex;margin-top:8px;min-height:40px;align-items:center;padding:0 12px;border-radius:8px;background:var(--ink);color:var(--paper);text-decoration:none;font-weight:700;font-size:14px}
.cta{display:block;text-align:center;margin:24px 0;padding:16px;border-radius:12px;background:var(--red);color:#fff;font-weight:900;text-decoration:none;font-size:18px}
footer{color:var(--mute);font-size:14px;text-align:center;padding:20px}
@media(max-width:600px){.it{grid-template-columns:32px minmax(0,1fr)}.pr{grid-column:2;text-align:left;white-space:normal;display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}.pr .sl{width:100%}.pr b{display:inline}.pr .cp{margin-top:4px}}"""

PAGES = []  # (path, title)
def page(path, title, desc, h1, lead, rows, extra_nav=True):
    url = f"{SITE}/{path}" if path else f"{SITE}/"
    nav = "".join(f'<a href="/{p}">{esc(t)}</a>' for p, t in NAV if p != path) if extra_nav else ""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": x["n"]} for i, x in enumerate(rows[:20])]}
    body = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="골라골라"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og.png"><meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap" rel="stylesheet">
<script data-goatcounter="https://gollagolla.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script><script>/* 구매 버튼 클릭 집계(이동은 막지 않음) */document.addEventListener("click",e=>{{const a=e.target.closest("a.cp,a.gbtn");if(!a)return;const card=a.closest("article,.row,.it,.hot,.pick");const code=(card&&(card.dataset.id||(card.querySelector(".code")||{{}}).textContent)||"").replace(/[^\\d]/g,"");const who=a.classList.contains("naver")?"naver":"coupang";try{{window.goatcounter&&window.goatcounter.count&&window.goatcounter.count({{path:"click/"+who,event:true}}),window.goatcounter.count({{path:"click/"+who+(code?"/"+code:""),title:(card&&(card.querySelector("b,.nm,h3")||{{}}).textContent||"").trim().slice(0,60),event:true}})}}catch(_){{}}}},true);</script><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script><style>{CSS}</style></head><body>
<div class="disc">이 사이트는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</div>
<header class="top"><a href="/">골라골라</a></header><main><h1>{esc(h1)}</h1><p class="lead">{esc(lead)}</p><nav class="nav">{nav}</nav>
<p class="mt">가격은 코스트코 매장 행사가예요. 지점마다 행사·재고가 다를 수 있어요. ‘쿠팡’ 버튼은 제휴 링크이고 쿠팡 가격·용량은 다를 수 있어요.</p>
<ol>{''.join(row(i+1, x) for i, x in enumerate(rows))}</ol>
<a class="cta" href="/">이번 주 할인 {len(items)}개 전체 보기 →</a></main>
<footer>골라골라는 코스트코 공식 사이트가 아니에요 · {TODAY.year}년 {TODAY.month}월 {TODAY.day}일 기준</footer></body></html>"""
    out = os.path.join(ROOT, path, "index.html") if path else None
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(body)
    PAGES.append(path)

CATS = [("food", "식품", ["식품"]), ("living", "생활용품", ["화장품/미용/제지", "공구/생활/자동차"]), ("kitchen", "주방·홈", ["홈/키친"]),
        ("health", "건강·영양제", ["건강/영양제"]), ("fashion", "의류·잡화", ["의류/가방/잡화"]), ("digital", "가전·디지털", ["디지털/TV/컴퓨터", "대형/생활가전"])]
ending = [x for x in ok if x["_e"] and (x["_e"] - TODAY).days <= 5]
NAV = [("this-week/", "이번 주 할인 TOP"), ("ending/", "마감 임박")] + [(f"c/{s}/", n) for s, n, _ in CATS]

page("this-week/", f"이번 주 코스트코 할인 TOP 50 ({PERIOD}) | 골라골라", f"{WEEK} 코스트코 매장 할인 {len(items)}개 중 인기 상위 50개. 할인가·행사기간·상품코드 정리.",
     f"이번 주 코스트코 할인 TOP 50", f"{WEEK} · {PERIOD} · 할인 {len(items)}개 중 자주 사는 식품·생활용품 위주 인기순", ok[:50])
page("ending/", f"코스트코 마감 임박 할인 {len(ending)}개 ({TODAY.month}월 {TODAY.day}일 기준) | 골라골라", f"5일 안에 끝나는 코스트코 매장 할인 {len(ending)}개. 마감일·할인가·상품코드 정리.",
     "곧 끝나는 코스트코 할인", f"5일 안에 행사가 끝나는 상품 {len(ending)}개 · 인기순", ending[:60])
for slug, name, cs in CATS:
    L = [x for x in ok if x["c"] in cs]
    if not L: continue
    page(f"c/{slug}/", f"이번 주 코스트코 {name} 할인 TOP {min(30,len(L))} ({PERIOD}) | 골라골라", f"코스트코 {name} 할인 {len(L)}개 중 인기 상위. 할인가·행사기간·상품코드 정리.",
         f"이번 주 코스트코 {name} 할인", f"{WEEK} · {name} 할인 {len(L)}개 중 인기순", L[:30])

# 홈: TOP20 미리 그리기(검색엔진용, 화면이 열리면 스크립트가 다시 그림)
idx = os.path.join(ROOT, "index.html"); s = open(idx, encoding="utf-8").read()
pre = "".join(f'<div class="row"><div class="no">{i+1}</div><div><b>{esc(x["n"])}</b><small>{esc(x["c"])} · {x["pc"]}% 할인 · {md(x["_e"])}까지</small></div><div class="pr"><b>{won(x["p"])}</b></div></div>' for i, x in enumerate(ok[:20]))
s = re.sub(r'<div class="rank" id="rankList">.*?</div>\s*</div>\s*</section>', f'<div class="rank" id="rankList">{pre}</div>\n  </div>\n</section>', s, count=1, flags=re.S)
s = re.sub(r'<p class="seo-links"[^>]*>.*?</p>\n?', "", s, flags=re.S)
links = " · ".join(f'<a href="/{p}">{esc(t)}</a>' for p, t in NAV)
s = s.replace('<footer class="band" id="about">', f'<p class="seo-links" style="text-align:center;font-size:14px;padding:0 16px 20px">{links}</p>\n<footer class="band" id="about">', 1)
open(idx, "w", encoding="utf-8").write(s)

urls = [f"{SITE}/"] + [f"{SITE}/{p}" for p in PAGES]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
    f"<url><loc>{u}</loc><lastmod>{TODAY.isoformat()}</lastmod><changefreq>weekly</changefreq></url>" for u in urls) + "</urlset>\n"
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
print(len(urls), "pages:", urls)
