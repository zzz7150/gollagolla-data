"""카톡 할인 시트(CSV) -> deals.json. 사용: python3 build.py sheet.csv 2026-11-24"""
import csv, json, re, sys, unicodedata
from datetime import date

src, today = sys.argv[1], date.fromisoformat(sys.argv[2])

# 코스트코 코리아 사이트 대분류 기준
CAT = {12:"식품",13:"식품",14:"식품",16:"식품",17:"식품",18:"식품",19:"식품",61:"식품",62:"식품",63:"식품",64:"식품",65:"식품",
 20:"화장품/미용/제지",23:"공구/생활/자동차",24:"디지털/TV/컴퓨터",25:"공구/생활/자동차",26:"스포츠/헬스/캠핑",27:"파티오/정원/창고",
 28:"홈/키친",31:"의류/가방/잡화",35:"의류/가방/잡화",39:"의류/가방/잡화",32:"홈/키친",33:"대형/생활가전",34:"가구/침구/인테리어",
 38:"가구/침구/인테리어",44:"가구/침구/인테리어",93:"건강/영양제"}
# 상품명으로 세부 조정 (부서 번호만으론 섞이는 것들)
RECAT = [(r"사료|애견|애묘|반려|츄르|고양이|(?<!크리스마스)강아지", "유아동/완구/반려동물용품"),
         (r"레고|완구|장난감|퍼즐", "유아동/완구/반려동물용품"),
         (r"화장지|키친타월|티슈|물티슈|미용티슈", "화장품/미용/제지"),
         (r"캡슐|원두|커피믹스|티백", "식품"),
         (r"세제|섬유유연|다우니|페브리즈|락스|주방세제", "공구/생활/자동차"),
         (r"비타민|오메가|유산균|홍삼|루테인|영양제", "건강/영양제")]
WINTER = re.compile("패딩|다운|핫팩|넥워머|스웨터|플리스|기모|가디건|목도리|장갑|히터|가습|곰탕|사골|고구마|감귤|단감|홍삼|유자|스프|수프|어묵|떡국|만두|부츠|조끼|퀼팅|이불|울양말|내복|발열")
XMAS = re.compile("크리스마스|산타|눈사람|어드벤트|케익|선물세트")
# 영상 픽: (상품명 일부, 훅, 첫 화면 대표 여부)
PICKS = [
 ("삼성 UHD 75","블프 TV 대전 — 삼성 75형 56만원 할인, 지금 사도 될까?",True),
 ("눈오는마을장식","코스트코 크리스마스 장식 하울, 최대 41% 할인",True),
 ("키즈퀼팅패딩","아이 겨울 패딩 40% 할인, 12월 1일까지",True),
 ("2.7M LED","2.7m LED 트리 20만원 할인 — 거실에 놓으면 이 정도",False),
 ("남성 다운자켓","남자 다운 3만원 할인, 브랜드 패딩이랑 비교해봄",False),
 ("씰리매디슨 펌 CK","씰리 매트리스 최대 32만원 할인, 사이즈별 정리",False),
 ("1865","송년회 와인 3만원 이하로 해결하기",False),
 ("하겐다즈샌드위치","하겐다즈 33% 할인, 쟁여도 되는 가격",False),
 ("휴대용비데","휴대용 비데 3만원 할인, 써보고 솔직 후기",False),
]

def num(s): return int(re.sub(r"[^\d]", "", s or "") or 0)
def day(s):
    y, m, d = (int(v) for v in re.split(r"[/.-]", s.strip()))
    return date(y, m, d)

rows = list(csv.reader(open(src, encoding="utf-8-sig")))
h = next(i for i, r in enumerate(rows) if "상품" in r and "적용가" in r)
H = rows[h]; ix = {k: H.index(k) for k in H if k}
out = []
for r in rows[h+1:]:
    if len(r) < len(H) or not r[ix["상품"]].strip(): continue
    try: end = day(r[ix["끝"]]); start = day(r[ix["시작"]])
    except Exception: continue
    if end < today: continue
    name = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", r[ix["상품"]])).strip().lstrip("#* ").strip()
    dept = num(r[ix["DEPT"]]); o, p = num(r[ix["정상가"]]), num(r[ix["적용가"]])
    t = []
    if WINTER.search(name) or dept == 34: t.append("겨울")
    if dept in (16, 28) or XMAS.search(name): t.append("연말")
    if dept in (24, 33, 44) and o - p >= 50000: t.append("블프")
    lim = r[ix["제한수량"]].strip()
    stock = num(r[ix["재고"]]) if "재고" in ix else 0
    out.append({"_stock":stock,"_dept":dept,"id":r[ix["Item"]].strip() if "Item" in ix else "","n":name,"c":next((c for rx,c in RECAT if re.search(rx,name)), CAT.get(dept,"기타")),"o":o,"p":p,"s":start.isoformat(),"e":end.isoformat(),
                "t":t,"lim":"" if lim in ("","N") else ("구매제한" if lim=="Y" else f"{lim}개 한정")})

# 추천: 카테고리별 할인율 상위 2개(20% 이상)
by = {}
for x in out: by.setdefault(x["c"], []).append(x)
for L in by.values():
    for x in sorted(L, key=lambda x: -(x["o"]-x["p"])/max(x["o"],1))[:2]:
        if (x["o"]-x["p"])/max(x["o"],1) >= .2: x["t"].append("추천")
for key, hook, hero in PICKS:
    m = [x for x in out if key in x["n"]]
    if not m: print("픽 못 찾음:", key); continue
    m[0]["hook"] = hook; m[0]["hero"] = hero
    if "추천" not in m[0]["t"]: m[0]["t"].append("추천")

# 인기점수(100): 작년 같은 시기 인기 30 + 올해 지금 관심 25 + 판매 검증 15 + 할인 매력 20 + 시즌 10
import math, os
J = lambda f: json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
G = J("google.json")                         # 상품 키워드별 구글 검색지수(최근 30일, 프링글스=100)
SIG = J("signals.json").get("rows", [])      # 코스트코 리뷰 수·공식 베스트
TERMS = J("gt/terms.json").get("map", {})
def termscore(lst):                          # 구글 '코스트코' 관련 검색어 → {검색어: 0~100}
    out = {}
    for row in lst.get("top", []):
        k, v = row.split("|"); k = k.replace("코스트코", "").strip(); out[k] = max(out.get(k, 0), int(v))
    for row in lst.get("rising", []):
        k, v = row.split("|"); k = k.replace("코스트코", "").strip()
        out[k] = max(out.get(k, 0), round(.6*(100 if not v.strip("+%,").replace(",", "").isdigit() else min(100, int(v.strip("+%").replace(",", "")) // 5))))   # 급상승은 변동이 커서 60%만 반영
    return out
LY, TY = termscore(J("gt/ly_costco.json")), termscore(J("gt/ty_costco.json"))
def hit(x, rule):
    if "cat" in rule and x["c"] != rule["cat"]: return False
    if "tag" in rule and rule["tag"] not in x["t"]: return False
    if "re" in rule and not re.search(rule["re"], x["n"]): return False
    if "not" in rule and re.search(rule["not"], x["n"]): return False
    return True
def listhit(x, sc):
    best, why = 0, None
    for term, v in sc.items():
        r = TERMS.get(term)
        if r and hit(x, r) and v > best: best, why = v, term
    return best, why
# 생활 소비 가산점(0~10): 자주·많이 사는 소모품일수록 높게
LIFE = {"식품":10, "화장품/미용/제지":10, "공구/생활/자동차":8, "홈/키친":6, "건강/영양제":6, "유아동/완구/반려동물용품":6,
        "의류/가방/잡화":4, "스포츠/헬스/캠핑":3, "가구/침구/인테리어":2, "파티오/정원/창고":1, "디지털/TV/컴퓨터":0, "대형/생활가전":0}
def pr(vals):
    srt = sorted(vals); n = len(srt) - 1 or 1
    return lambda v: sum(1 for x in srt if x < v) / n
pp = pr([min(1-x["p"]/max(x["o"],1), .5) for x in out]); pa = pr([x["o"]-x["p"] for x in out])
gmax = math.log1p(max(G.values() or [1])); rmax = math.log1p(max([s.get("r",0) for s in SIG] or [1]))
for x in out:
    pct = 1 - x["p"]/max(x["o"],1)
    ly, lyw = listhit(x, LY); ty, tyw = listhit(x, TY)
    sig = next((s for s in SIG if re.search(s["match"], x["n"]) and (not s.get("dept_hint") or x["c"].startswith(s["dept_hint"]))), None)
    gk = 100*math.log1p(G[sig["g"]])/gmax if sig and sig.get("g") in G else 0
    # 사용자 피드백: 상품별 검색·판매 신호가 더 정확, 비싼 가전은 사는 사람이 적으니 낮게
    s_ty = 30*max(.6*ty, gk)/100                      # 지금 관심(상품 검색지수 우선)
    s_ly = 10*ly/100                                  # 작년 이맘때 인기(보너스)
    s_sell = (15*math.log1p(sig.get("r",0))/rmax + (5 if sig.get("best") else 0)) if sig else 0
    s_deal = 9*pp(min(pct,.5)) + 6*pa(x["o"]-x["p"])
    s_season = 10 if set(x["t"]) & {"겨울","연말","블프"} else 0
    s_mass = 15*min(1, max(0, (math.log(500000)-math.log(max(x["p"],1)))/(math.log(500000)-math.log(10000))))   # 대중성: 1만원 이하 만점, 50만원 이상 0
    # 사용자 요청(11/25): 자주 사는 식품·생활용품에 가산점 — 기존 점수 90% + 생활소비 10점
    s_life = LIFE.get(x["c"], 3)
    sc = .9*(s_ty + s_ly + s_sell + s_deal + s_season + s_mass) + s_life
    if sig: x["_grp"] = sig["match"]
    elif lyw or tyw: x["_grp"] = "t:" + (tyw or lyw)
    x["sig"] = {"ly": lyw, "ty": tyw, "g": G.get(sig.get("g")) if sig else None, "r": sig.get("r",0) if sig else 0, "best": bool(sig and sig.get("best")),
                "pt": [round(s_ty), round(s_ly), round(s_sell), round(s_deal), s_season, round(s_mass), s_life]}
    if pct > .6: x["chk"] = 1; sc *= .5
    x["sc"] = round(sc)
out.sort(key=lambda x: -x["sc"])
seen = set()
for x in out:   # 같은 상품군 중복은 순위에서 한 칸 양보
    g = x.pop("_grp", None)
    if g and g in seen: x["sc"] = round(x["sc"]*.7)
    if g: seen.add(g)
out.sort(key=lambda x: -x["sc"])
crank = {}
for i, x in enumerate(out, 1):
    x["rk"] = i; crank[x["c"]] = crank.get(x["c"], 0) + 1; x["crk"] = crank[x["c"]]
for x in out: x.pop("_stock"); x.pop("_dept")
print("TOP20:"); [print(x["rk"], x["sc"], x["c"], x["n"], x["p"]) for x in out[:20]]

meta = {"week": f"{today.month}월 {(today.day-1)//7+1}주차", "from": min(x["s"] for x in out), "today": today.isoformat(), "count": len(out)}
json.dump({"meta": meta, "items": out}, open("deals.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "개 →", "deals.json", meta)
print("기타 카테고리:", sorted({x["n"] for x in out if x["c"]=="기타"})[:10])
