/* 골라골라 가격 비교 계산·표시 (사이트와 관리자 페이지가 같이 씀)
   데이터: compare.json = {settings:{staleHours}, items:{ "<상품코드>": 항목 }}
   항목 = {store:{qty,per,kind,branch,note}, hook, memo, updatedAt,
          offers:{coupang:판매처, naver:판매처}}
   판매처 = {price, ship(숫자|null: null=미확인, 0=무료), qty, per, kind('ea'|'g'|'ml'), checkedAt(ISO),
            url, aff(true=제휴), match('same'|'qty'|'unknown'), cond, condPrice, multiOk, multiShip}
   원칙: 계산·비교는 반올림 전 값, 화면에만 원 단위 반올림. 제휴 여부·수수료·비교 결과는 순위에 안 씀. */
(function (G) {
  "use strict";
  const SELLER = { store: "코스트코 매장", coupang: "쿠팡", naver: "네이버" };
  const KIND = { ea: { label: "개당", base: 1, unit: "개" }, g: { label: "100g당", base: 100, unit: "g" }, ml: { label: "100mL당", base: 100, unit: "mL" } };
  const isNum = v => typeof v === "number" && isFinite(v);
  const n = v => (v === "" || v === null || v === undefined) ? null : (isFinite(+v) ? +v : null);
  const won = v => Math.round(v).toLocaleString("ko-KR") + "원";
  const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  const keyOf = d => d && d.id ? String(d.id) : "n:" + (d && d.n || "");

  // 판매 구성 → 기준 수량(개 / g / mL). 1개당 용량이 없으면 g·mL는 계산 불가
  function amount(qty, per, kind) {
    qty = n(qty); per = n(per);
    if (!qty || qty <= 0) return null;
    if (kind === "g" || kind === "ml") return per && per > 0 ? qty * per : null;
    return qty; // ea
  }
  function packLabel(qty, per, kind) {
    qty = n(qty); per = n(per);
    if (!qty) return "구성 미확인";
    if ((kind === "g" || kind === "ml") && per) {
      const u = kind === "g" ? (per >= 1000 ? (per / 1000) + "kg" : per + "g") : (per >= 1000 ? (per / 1000) + "L" : per + "mL");
      return qty > 1 ? `${u} × ${qty}개` : u;
    }
    return `${qty}개`;
  }
  function unitPrice(total, amt, kind) {
    if (!isNum(total) || !amt) return null;
    return total / amt * (KIND[kind] || KIND.ea).base;
  }

  /* d: 할인 상품(deals.json 한 줄), e: 비교 항목, opt: {now:Date, today:Date(한국 날짜 0시), daysLeft:Number|null, staleHours} */
  function compute(d, e, opt) {
    opt = opt || {};
    const now = opt.now || new Date(), staleH = n(opt.staleHours) || 72;
    const st = (e && e.store) || {};
    const kind = st.kind || "ea";
    const daysLeft = opt.daysLeft;                 // 0 = 오늘 마감(오늘까지 행사 중), 음수 = 종료, null = 기간 미확인
    const ended = isNum(daysLeft) && daysLeft < 0;
    const storeAmt = amount(st.qty, st.per, kind);
    const store = {
      key: "store", name: SELLER.store, price: d.p, total: d.p, shipKnown: true, ship: 0, kind, amt: storeAmt,
      pack: packLabel(st.qty, st.per, kind), unit: unitPrice(d.p, storeAmt, kind), ended, periodUnknown: daysLeft === null,
      branch: st.branch || "", note: st.note || "", valid: !ended
    };
    const sellers = [];
    const offers = (e && e.offers) || {};
    for (const k of ["coupang", "naver"]) {
      const o = offers[k];
      if (!o || n(o.price) === null) continue;
      const price = n(o.price), ship = n(o.ship), shipKnown = ship !== null;
      const okind = o.kind || kind, amt = amount(o.qty, o.per, okind);
      const t = o.checkedAt ? new Date(o.checkedAt) : null;
      const ageH = t && !isNaN(t) ? (now - t) / 36e5 : null;
      const stale = ageH === null || ageH > staleH;
      const total = shipKnown ? price + ship : null;
      const s = {
        key: k, name: SELLER[k], price, ship, shipKnown, total, kind: okind, amt, pack: packLabel(o.qty, o.per, okind),
        unit: unitPrice(shipKnown ? total : null, amt, okind), unitNoShip: unitPrice(price, amt, okind),
        match: o.match || "unknown", stale, ageH, checkedAt: t && !isNaN(t) ? t : null, url: o.url || "", aff: !!o.aff,
        cond: o.cond || "", condPrice: n(o.condPrice), multiOk: !!o.multiOk, multiShip: n(o.multiShip), qty: n(o.qty)
      };
      s.valid = shipKnown && !stale && s.match !== "unknown";
      s.why = !shipKnown ? "배송비 미확인" : stale ? (ageH === null ? "확인 시각 없음" : "가격 재확인 필요") : s.match === "unknown" ? "비교 조건 미확인" : "";
      sellers.push(s);
    }
    const res = { key: keyOf(d), has: sellers.length > 0, store, sellers, verdict: null, notes: [], hook: (e && e.hook) || "", memo: (e && e.memo) || "" };
    if (!res.has) return res;

    // 1) 동일 제품·동일 구성: 배송비 포함 총액 비교
    const same = [store, ...sellers.filter(s => s.valid && s.match === "same")].filter(s => s.valid && isNum(s.total));
    if (same.length >= 2) {
      const sorted = [...same].sort((a, b) => a.total - b.total);
      const best = sorted[0], second = sorted[1];
      if (best.total === second.total && same.length === 2) {
        res.verdict = `${second.name}${josa(second.name, "과", "와")} ${best.name} 가격이 같아요`;
      } else if (same.length === 2) {
        const other = second;
        res.verdict = `${other.name}보다 ${best.name}${josa(best.name, "이", "가")} ${won(other.total - best.total)} 저렴해요`;
      } else {
        const ties = sorted.filter(s => s.total === best.total);
        if (ties.length > 1) res.verdict = `비교한 판매처 중 ${ties.map(s => s.name).join("·")} 가격이 가장 낮아요`;
        else {
          const ref = best.key === "store" ? sorted.slice(1).map(s => `${s.name}보다 ${won(s.total - best.total)}`).join(", ")
            : (store.valid ? `코스트코 매장보다 ${won(store.total - best.total)}` : `${second.name}보다 ${won(second.total - best.total)}`);
          res.verdict = `비교한 판매처 중 ${best.name}${josa(best.name, "이", "가")} 가장 저렴해요 · ${ref} 저렴`;
        }
      }
      res.verdictKind = best.key === "store" ? "store" : "online";
    }

    // 2) 동일 제품·수량만 다름: 실제 묶음 총액 + 단가
    const qtys = sellers.filter(s => s.valid && s.match === "qty");
    const packSaid = new Set();
    for (const s of qtys) {
      const comparable = store.valid && store.unit !== null && s.unit !== null && s.kind === store.kind;
      if (comparable) {
        const lab = (KIND[store.kind] || KIND.ea).label;
        let line;
        if (store.unit < s.unit) { line = `${lab} 가격은 코스트코 매장이 낮고, ${s.name}에서는 ${s.pack} 묶음으로 살 수 있어요`; packSaid.add(s.key); }
        else if (store.unit > s.unit) line = `${lab} 가격은 ${s.name}${josa(s.name, "이", "가")} 낮아요 (${lab} ${won(s.unit)} vs 매장 ${won(store.unit)})`;
        else line = `${lab} 가격은 코스트코 매장과 ${s.name}${josa(s.name, "이", "가")} 같아요`;
        // 같은 수량으로 맞춰 비교: 여러 묶음 구매 가능·합산 배송비 확인 + 수량이 딱 나눠질 때만
        if (s.multiOk && s.multiShip !== null && s.amt && storeAmt) {
          const k = storeAmt / s.amt;
          if (Number.isInteger(k) && k >= 1) {
            const tot = s.price * k + s.multiShip, diff = store.total - tot;
            const nameTail = diff > 0 ? `${s.name}${josa(s.name, "이", "가")} ${won(diff)} 저렴` : diff < 0 ? `코스트코 매장이 ${won(-diff)} 저렴` : `가격이 같아요`;
            res.notes.push(`같은 수량(${store.pack})으로 맞추면 ${s.name}에서 ${k}묶음 ${won(tot)}(배송비 포함) · ${nameTail}`);
          } else res.notes.push(`${s.name} 묶음 수량이 매장 구성과 딱 나눠지지 않아 같은 수량 차액은 계산하지 않았어요`);
        }
        if (!res.verdict) { res.verdict = line; res.verdictKind = store.unit <= s.unit ? "store" : "online"; } else res.notes.push(line);
      } else if (store.valid) {
        res.notes.push(`${s.name}${josa(s.name, "은", "는")} ${s.pack} 묶음 ${won(s.total)}(배송비 포함)이에요 · 단위가 확인되지 않아 단가 비교는 보류했어요`);
      }
    }

    // 3) 온라인 이점 (소량 구매·무료배송) 안내
    for (const s of sellers) {
      if (!packSaid.has(s.key) && s.qty && n(st.qty) && s.kind === kind && s.amt && storeAmt && s.amt < storeAmt) res.notes.push(`${s.name}에서는 ${s.pack}로 적게 살 수 있어요`);
      if (s.ship === 0 && s.valid) res.notes.push(`${s.name}${josa(s.name, "은", "는")} 무료배송이에요`);
    }
    if (store.ended) res.notes.unshift("코스트코 매장 할인이 끝나 매장 가격 비교 문구는 숨겼어요");
    if (!res.verdict) {
      const w = sellers.map(s => s.why);
      res.hold = store.ended ? "매장 할인이 끝나 가격 비교를 멈췄어요"
        : w.includes("가격 재확인 필요") || w.includes("확인 시각 없음") ? "온라인 가격을 다시 확인한 뒤 비교할게요"
        : w.includes("배송비 미확인") ? "배송비 확인 전이라 가격 비교는 보류했어요"
        : w.includes("비교 조건 미확인") ? "같은 상품·구성인지 확인 전이라 비교는 보류했어요"
        : "가격 비교 조건을 확인 중이에요";
    }
    res.notes = [...new Set(res.notes)];
    return res;
  }

  function josa(word, a, b) {
    const c = word.charCodeAt(word.length - 1);
    if (c < 0xac00 || c > 0xd7a3) return b;
    return (c - 0xac00) % 28 ? a : b;
  }
  function ago(t, now) {
    if (!t) return "확인 시각 없음";
    const h = Math.floor((now - t) / 36e5);
    if (h < 1) return "방금 확인";
    if (h < 24) return `${h}시간 전 확인`;
    return `${Math.floor(h / 24)}일 전 확인`;
  }
  function fmtTime(t) {
    if (!t) return "";
    const k = new Date(t.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
    return `${k.getMonth() + 1}.${k.getDate()} ${String(k.getHours()).padStart(2, "0")}:${String(k.getMinutes()).padStart(2, "0")}`;
  }

  /* 카드 안 비교 블록 HTML. extra: {period:"11.23~11.29", now:Date} */
  function html(r, extra) {
    extra = extra || {}; const now = extra.now || new Date();
    if (!r || !r.has) return "";
    const row = s => {
      const isStore = s.key === "store";
      const pay = isStore ? won(s.total)
        : s.shipKnown ? `${won(s.total)}<small>${s.ship === 0 ? "무료배송" : `배송비 ${won(s.ship)} 포함`}</small>`
          : `${won(s.price)}<small>배송비 미확인</small>`;
      const unit = s.unit !== null ? `${(KIND[s.kind] || KIND.ea).label} ${won(s.unit)}` : (!isStore && !s.shipKnown && s.unitNoShip !== null ? `${(KIND[s.kind] || KIND.ea).label} ${won(s.unitNoShip)}+배송비` : "");
      const badges = [];
      if (isStore && s.ended) badges.push('<span class="gb warn">매장 할인 종료</span>');
      if (isStore && s.periodUnknown) badges.push('<span class="gb">기간 미확인</span>');
      if (!isStore && s.stale) badges.push(`<span class="gb warn">${s.ageH === null ? "확인 시각 없음" : "가격 재확인 필요"}</span>`);
      if (!isStore && s.match === "qty") badges.push('<span class="gb">수량 다름</span>');
      if (!isStore && s.match === "unknown") badges.push('<span class="gb">비교 조건 미확인</span>');
      const meta = isStore ? [extra.period && `${extra.period} 행사`, s.branch || "적용 지점: 지점마다 다를 수 있음"].filter(Boolean).join(" · ")
        : (s.checkedAt ? `${ago(s.checkedAt, now)} (${fmtTime(s.checkedAt)})` : "");
      const cond = !isStore && (s.cond || s.condPrice !== null) ? `<div class="gcond">조건부 가격: ${s.condPrice !== null ? won(s.condPrice) + " · " : ""}${esc(s.cond)} <em>(비교에는 안 넣었어요)</em></div>` : "";
      return `<div class="gr ${isStore ? "st" : ""}"><div class="gn"><b>${esc(s.name)}</b><span>${esc(s.pack)}</span></div>
        <div class="gp"><b>${pay}</b>${unit ? `<span>${unit}</span>` : ""}</div>
        <div class="gm">${badges.join("")}<span>${esc(meta)}</span></div>${cond}</div>`;
    };
    const btn = s => s.url ? `<a class="gbtn ${s.key}" href="${esc(s.url)}" target="_blank" rel="noopener${s.aff ? " sponsored" : ""}">${esc(s.name)}에서 가격 보기</a>` : "";
    const btns = r.sellers.map(btn).filter(Boolean).join("");
    const aff = r.sellers.some(s => s.url && s.aff);
    return `<div class="gcmp">
      ${r.verdict ? `<p class="gv ${r.verdictKind || ""}">${esc(r.verdict)}</p>` : `<p class="gv none">${esc(r.hold || "가격 비교 조건을 확인 중이에요")}</p>`}
      ${r.notes.length ? `<ul class="gnotes">${r.notes.map(t => `<li>${esc(t)}</li>`).join("")}</ul>` : ""}
      <div class="grs">${row(r.store)}${r.sellers.map(row).join("")}</div>
      ${r.memo ? `<p class="gmemo">참고: ${esc(r.memo)}</p>` : ""}
      ${btns ? `<div class="gbtns">${btns}</div>` : ""}
      ${aff ? `<p class="gaff">제휴 링크가 포함돼 있어요. 이 링크로 구매하면 골라골라가 일정액의 수수료를 받을 수 있어요.</p>` : ""}
    </div>`;
  }

  const CSS = `.gcmp{margin-top:10px;border-top:1px dashed var(--line,#ddd);padding-top:10px}
.gv{margin:0 0 6px;font-weight:900;font-size:16px;line-height:1.4}.gv.online{color:var(--blue,#1747a6)}.gv.store{color:var(--red,#d4211a)}.gv.none{color:var(--mute,#666);font-weight:700;font-size:14px}
.gnotes{margin:0 0 8px;padding-left:18px;font-size:14px;color:var(--mute,#555)}
.grs{display:grid;gap:6px}.gr{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 10px;padding:8px 10px;border-radius:8px;background:var(--bg,#f6f6f6)}
.gr.st{outline:2px solid var(--line,#e3dbd0)}.gn b{display:block;font-size:15px}.gn span{font-size:13px;color:var(--mute,#666)}
.gp{text-align:right;white-space:nowrap}.gp b{display:block;font-size:17px;font-weight:900}.gp b small{display:block;font-size:12px;font-weight:500;color:var(--mute,#666)}.gp>span{font-size:13px;color:var(--mute,#666)}
.gm{grid-column:1/-1;font-size:12px;color:var(--mute,#666);display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.gb{font-size:12px;font-weight:700;padding:1px 6px;border-radius:4px;background:var(--line,#e3dbd0);color:var(--ink,#111)}.gb.warn{background:#d4211a;color:#fff}
.gcond{grid-column:1/-1;font-size:12px;color:var(--ink,#111)}.gcond em{font-style:normal;color:var(--mute,#666)}
.gmemo{font-size:13px;color:var(--mute,#666);margin:6px 0 0}
.gbtns{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.gbtn{font-weight:700;font-size:14px;text-decoration:none;min-height:40px;display:inline-flex;align-items:center;padding:0 12px;border-radius:8px;color:#fff}
.gbtn.coupang{background:#16110f}.gbtn.naver{background:#03a94d}
.gaff{font-size:12px;color:var(--mute,#666);margin:6px 0 0}`;

  G.GC = { compute, html, CSS, keyOf, amount, unitPrice, packLabel, won, KIND, SELLER };
})(typeof window !== "undefined" ? window : globalThis);
