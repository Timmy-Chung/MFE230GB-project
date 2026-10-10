/* Kimchi Premium page: builds every figure and table from DATA. */
(function () {
  const D = DATA, F = CC.fmt, DAY = 86400000;
  const $ = (s) => document.querySelector(s);
  function el(tag, cls, parent, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  const setK = (k, v) => document.querySelectorAll(`[data-k="${k}"]`).forEach((n) => (n.textContent = v));
  const neg = (s) => s.replace(/^-/, "−");
  const pct = (v, d = 1) => (v == null || isNaN(v) ? "–" : neg((v * 100).toFixed(d)) + "%");
  const spct = (v, d = 1) => (v == null || isNaN(v) ? "–" : Math.abs(v * 100) < 0.5 * Math.pow(10, -d) ? (0).toFixed(d) + "%" : F.spct(v, d));
  const num = (v, d = 2) => F.num(v, d);
  const snum = (v, d = 2) => F.snum(v, d);
  const bp = (v, d = 0) => (v == null || isNaN(v) ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v * 1e4).toFixed(d) + " bp");
  const krw = (v) => "₩" + Math.round(v).toLocaleString("en-US");
  const usd = (v) => "$" + v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  const dstr = (d) => new Date(d * DAY).toLocaleString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const mstr = (iso) => { const d = new Date(iso + "T00:00:00Z"); return MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const rob = Object.fromEntries(D.robustness.map((r) => [r.test, r]));
  const main = rob["Main rule (Korea)"], krSame = rob["Korea, the placebo's weeks"], jpn = rob["Japan placebo (bitbank)"];
  const qs = D.quintiles;

  // ------------------------------------------------------------------ narrative numbers
  const h1 = D.h1_simple;
  setK("h1.krMean", pct(h1[0].mean, 1));
  setK("h1.jpMean", pct(h1[1].mean, 1));
  setK("h1.kr2", pct(h1[0].share_above_2pct, 0));
  setK("h1.krDisc", pct(h1[0].share_below_0, 0));
  const fmSig = D.fm.signal.find((r) => r.var === "sig_pct");
  setK("fm.coef", spct(fmSig.coef, 1));
  setK("fm.t", snum(fmSig.t_nw, 1));
  setK("main.net", spct(main.net_return, 1));
  setK("main.sharpeNet", num(main.sharpe_net, 2));
  setK("main.t", num(main.t_net, 1));
  setK("main.price", spct(main.price_ann, 0));
  setK("main.funding", spct(main.funding_ann, 0));
  setK("main.cost", spct(-main.cost_ann, 0));
  setK("main.eaten", pct(1 - main.net_return / main.price_ann, 0));
  setK("main.weeks", String(main.weeks));
  setK("cost.be", D.breakeven_bp.toFixed(0) + " bp");
  const y26 = D.pnl_by_year[D.pnl_by_year.length - 1];
  setK("y26.fund", pct(Math.abs(y26.funding), 0));
  setK("y26.price", pct(y26.price, 0));
  setK("usdt.mean", pct(D.usdt_premium_mean, 1));
  setK("u.avg", String(Math.round(main.avg_coins)));
  setK("u.traded", String(D.universe.coins_traded));
  setK("u.sample", `${mstr(D.universe.first_trade_week)} to ${mstr("2026-09-27")}`);
  setK("live.date", dstr(Math.round(Date.parse(D.live_week.week + "T00:00:00Z") / DAY)));
  setK("live.n", String(D.live_week.n_coins));
  setK("live.k", String(D.live_week.k));
  setK("sig.share", pct(D.share_abs_signal_below_25bp, 0));
  setK("sig.iqr", `${bp(D.signal_iqr_bp[0] / 1e4, 0)} to ${bp(D.signal_iqr_bp[1] / 1e4, 0)}`);
  const q5 = qs[4], q1 = qs[0];
  setK("ch.dpi", `${Math.abs(q5.dpi_bp).toFixed(0)} of its ${q5.signal_bp.toFixed(0)} bp`);
  setK("ch.tdpi", snum(q5.t_dpi, 1));
  setK("h3.coef", spct(D.h3.coef_4w / 100, 2));
  setK("h3.t", snum(D.h3.t_4w, 1));
  setK("ov.btc", num(D.overlay.stats.btc.sharpe, 2));
  setK("ov.ovl", num(D.overlay.stats.overlay.sharpe, 2));
  setK("ov.weeks", String(D.overlay.froth_weeks));
  const rg = Object.fromEntries(D.regime.map((r) => [r.regime, r]));
  setK("rg.disc", spct(rg["Discount"].mean, 2));
  setK("rg.hot", spct(rg["Above 5%"].mean, 2));
  setK("rg.hotn", String(rg["Above 5%"].size));
  const W = D.worst_coin;
  setK("worst.date", dstr(Math.round(Date.parse(W.week + "T00:00:00Z") / DAY)));
  setK("worst.week", pct(D.tails.worst_week_net, 1));
  setK("worst.coin", W.coin);
  setK("worst.ret", spct(W.ret_price, 0));
  setK("worst.w", "1/" + Math.round(1 / Math.abs(W.weight)));
  setK("worst.sig", bp(W.signal, 0));
  setK("worst.f", spct(W.fund7_ann, 0));
  setK("worst.n", String(W.n_per_leg));
  setK("tails.exworst", num(D.tails.sharpe_net_ex_worst_week, 2));
  setK("jp.coins", String(Math.round(jpn.avg_coins)));
  setK("jp.weeks", String(jpn.weeks));
  setK("jp.net", pct(Math.abs(jpn.net_return), 0));
  setK("jp.sharpe", snum(jpn.sharpe_net, 2));
  setK("jp.gross", spct(jpn.gross_return, 0) + " a year");
  setK("krs.net", spct(krSame.net_return, 1));
  setK("krs.sharpe", num(krSame.sharpe_net, 2));
  const FS = D.full_sample;
  setK("fs.net", pct(Math.abs(FS.net_return), 1));
  setK("fs.sharpe", snum(FS.sharpe_net, 2));
  setK("fs.worst", dstr(Math.round(Date.parse(FS.worst_week + "T00:00:00Z") / DAY)));
  setK("fs.worstNet", pct(Math.abs(FS.worst_week_net), 0));
  setK("fs.exworst", snum(FS.sharpe_net_ex_worst, 2));
  setK("meta.generated", D.meta.generated);

  // ------------------------------------------------------------------ hero board
  (function () {
    const seg = $("#board-dates"), grid = $("#board");
    function draw(i) {
      const s = D.shadow[i];
      grid.replaceChildren();
      const cell = (lab, val, sub, hot) => {
        const c = el("div", "board-cell" + (hot ? " hot" : ""), grid);
        el("span", "lab", c, lab); el("span", "val", c, val); if (sub) el("span", "sub", c, sub);
      };
      cell("Bitcoin on Upbit, Seoul", krw(s.upbit_krw), "won price");
      cell("Bitcoin on Binance", usd(s.binance_usd), "USDT price");
      cell("Implied won rate", krw(s.implied) + "/$", "Upbit ÷ Binance");
      cell("Market won rate", krw(s.official) + "/$", "Fed noon New York rate");
      cell("Kimchi premium", spct(s.premium, 1), "implied ÷ market − 1", true);
      [...seg.children].forEach((b, k) => b.setAttribute("aria-pressed", String(k === i)));
    }
    D.shadow.forEach((s, i) => { const b = el("button", null, seg, s.label); b.type = "button"; b.addEventListener("click", () => draw(i)); });
    draw(0);
  })();

  // ------------------------------------------------------------------ H1 chart + table
  CC.lineChart($("#kappa-chart"), {
    x: D.kappa.days.map((d) => d * DAY),
    series: [
      { name: "Korea (Upbit, won)", short: "Korea", values: D.kappa.kr, colorVar: "--s-kr" },
      { name: "Japan (bitbank, yen)", short: "Japan", values: D.kappa.jp, colorVar: "--s-jp" },
    ],
    height: 320, baseline: 0, yFmt: (v) => pct(v, 0), tipFmt: (v) => pct(v, 1), endFmt: (v) => pct(v, 1),
    aria: "Line chart of the bitcoin premium in Korea and Japan, October 2021 to September 2026",
  });
  CC.table($("#h1-table"), [
    { key: "market", label: "Market", num: false },
    { key: "mean", label: "Average", fmt: (v) => pct(v, 2) }, { key: "sd", label: "Std. dev.", fmt: (v) => pct(v, 1) },
    { key: "share_above_2pct", label: "Days above 2%", fmt: (v) => pct(v, 0) },
    { key: "share_below_0", label: "Days at a discount", fmt: (v) => pct(v, 0) },
    { key: "max", label: "Peak", fmt: (v, r) => `${pct(v, 1)} (${mstr(r.max_date)})` },
    { key: "half_life_days", label: "Half-life, days", fmt: (v) => num(v, 1) },
  ], h1);

  // ------------------------------------------------------------------ live week
  (function () {
    const rows = D.live_week.rows;
    const pick = rows.slice(0, 5).concat(rows.slice(-5));
    CC.table($("#live-table"), [
      { key: "coin", label: "Coin", num: false },
      { key: "side", label: "Position", num: false, fmt: (v) => (v === "long" ? "Long" : "Short") },
      { key: "signal", label: "π, 7-day", fmt: (v) => bp(v, 0) },
      { key: "premium", label: "Premium vs market rate", fmt: (v) => spct(Math.expm1(v), 1) },
      { key: "fund7", label: "Funding, ann.", fmt: (v) => spct(v * 52, 0) },
      { key: "ret_long", label: "Next week, P&L", fmt: (v, r) => spct(r.side === "long" ? v : -v, 1) },
    ], pick.map((r) => Object.assign({}, r, { _cls: r.side === "short" ? "hi" : "" })), { compact: true });
  })();

  // ------------------------------------------------------------------ mechanism
  const qlab = ["Q1\nlowest π", "Q2", "Q3", "Q4", "Q5\nhighest π"];
  CC.barChart($("#quint-chart"), {
    categories: qlab,
    series: [{ name: "Next-week return vs universe, per year", values: qs.map((q) => q.ret_rel_ann),
      colorVars: ["--s-kr", "--s-jp", "--s-jp", "--s-jp", "--s-kr"],
      extra: qs.map((q) => ({ name: "t-statistic", value: snum(q.t_rel, 1) })) }],
    height: 270, yFmt: (v) => pct(v, 0), valueLabels: true, labelFmt: (v) => spct(v, 0),
    aria: "Bar chart of next-week relative returns by premium quintile",
  });
  CC.barChart($("#channel-chart"), {
    categories: ["Top quintile\n(short leg)", "Bottom quintile\n(long leg)"],
    series: [
      { name: "Korean price (Upbit)", values: [q5.dlocal_rel_pct / 100, q1.dlocal_rel_pct / 100], colorVar: "--s-kr",
        extra: [{ name: "t-statistic", value: snum(q5.t_dlocal, 1) }, { name: "t-statistic", value: snum(q1.t_dlocal, 1) }] },
      { name: "World price (Binance)", values: [q5.dworld_rel_pct / 100, q1.dworld_rel_pct / 100], colorVar: "--s-jp",
        extra: [{ name: "t-statistic", value: snum(q5.t_dworld, 1) }, { name: "t-statistic", value: snum(q1.t_dworld, 1) }] },
    ],
    height: 270, yFmt: (v) => pct(v, 1), valueLabels: true, labelFmt: (v) => spct(v, 2), ymin: -0.0105,
    aria: "Bar chart of next-week Korean and world price changes for the two traded legs",
  });
  (function () {
    const spec = [["signal", "π only"], ["signal+past1", "+ past-week return"], ["full", "+ past 4 weeks, volume, funding"]];
    const rows = spec.map(([k, lab]) => {
      const t = Object.fromEntries(D.fm[k].map((r) => [r.var, r]));
      return { spec: lab, coef: t.sig_pct.coef, t: t.sig_pct.t_nw, weeks: t.sig_pct.weeks };
    });
    CC.table($("#fm-table"), [
      { key: "spec", label: "Controls", num: false },
      { key: "coef", label: "Return per point of π", fmt: (v) => spct(v, 2) },
      { key: "t", label: "t (NW)", fmt: (v) => snum(v, 2) }, { key: "weeks", label: "Weeks", fmt: (v) => String(v) },
    ], rows, { compact: true });
    CC.table($("#fmh-table"), [
      { key: "horizon_weeks", label: "Horizon", num: false, fmt: (v) => `${v} week${v > 1 ? "s" : ""}` },
      { key: "coef", label: "Cumulative return per point of π", fmt: (v) => spct(v, 2) },
      { key: "t_nw", label: "t (NW)", fmt: (v) => snum(v, 2) },
    ], D.fm_horizons, { compact: true });
  })();
  CC.barChart($("#froth-chart"), {
    categories: D.froth_quintiles.kappa_pct.map((v) => `${neg(v.toFixed(1))}%`),
    series: [{ name: "BTC return over the next 4 weeks", values: D.froth_quintiles.btc_4w_pct.map((v) => v / 100),
      colorVars: D.froth_quintiles.btc_4w_pct.map((v) => (v >= 0 ? "--div-pos" : "--div-neg")) }],
    height: 250, yFmt: (v) => pct(v, 0), valueLabels: true, labelFmt: (v) => spct(v, 1),
    aria: "Bar chart of bitcoin's next-4-week return by quintile of the Korean premium",
  });

  // ------------------------------------------------------------------ results workbench: Korea, before costs, Japan placebo
  (function () {
    const jpStart = D.weekly.jp.days[0];
    const periods = [["Oct 2021 – Sep 2026", 0], [`${mstr(D.weekly.jp.days.length ? new Date(jpStart * DAY).toISOString().slice(0, 10) : "2023-03-20")} – Sep 2026, with Japan`, jpStart]];
    let cost = 10, per = 0, showGross = true;
    const ctr = $("#wb-controls");
    const tg = el("div", "controls", ctr);
    const lg = el("label", "toggle", tg);
    const cg = el("input", null, lg); cg.type = "checkbox"; cg.checked = true; cg.id = "wb-gross";
    const sg = el("span", "sw", lg); sg.style.background = CC.cssVar("--s-ref");
    el("span", null, lg, "Korea before costs");
    cg.addEventListener("change", () => { showGross = cg.checked; draw(); });
    const sl = el("label", "slider", ctr);
    el("span", null, sl, "Cost per unit traded");
    const rng = el("input", null, sl); rng.type = "range"; rng.min = 0; rng.max = 40; rng.step = 1; rng.value = cost; rng.id = "wb-cost";
    const out = el("output", null, sl, cost + " bp");
    rng.addEventListener("input", () => { cost = +rng.value; out.textContent = cost + " bp"; draw(); });
    const seg = el("div", "seg", ctr); seg.setAttribute("role", "group"); seg.setAttribute("aria-label", "Period");
    periods.forEach((p, i) => {
      const b = el("button", null, seg, p[0]); b.type = "button"; b.setAttribute("aria-pressed", String(i === per));
      b.addEventListener("click", () => { per = i; [...seg.children].forEach((x, k) => x.setAttribute("aria-pressed", String(k === i))); draw(); });
    });
    const chartHost = $("#wb-chart"), tableHost = $("#wb-table");
    let chart = null;
    function series(key, c) {
      const w = D.weekly[key], lo = periods[per][1];
      const idx = w.days.map((d, i) => i).filter((i) => w.days[i] >= lo);
      const r = idx.map((i) => w.gross[i] - (c / 1e4) * w.turnover[i]);
      return { days: idx.map((i) => w.days[i] + 7), r, idx, w };
    }
    function stats(s, c) {
      const r = s.r, n = r.length;
      const m = r.reduce((a, b) => a + b, 0) / n;
      const sd = Math.sqrt(r.reduce((a, b) => a + (b - m) * (b - m), 0) / (n - 1));
      let acc = 1, peak = 1, mdd = 0;
      for (const x of r) { acc *= 1 + x; peak = Math.max(peak, acc); mdd = Math.min(mdd, acc / peak - 1); }
      const sum = (arr) => s.idx.reduce((a, i) => a + arr[i], 0) / n * 52;
      return { ret: m * 52, vol: sd * Math.sqrt(52), sharpe: (m * 52) / (sd * Math.sqrt(52)), mdd, fin: acc,
        turn: s.idx.reduce((a, i) => a + s.w.turnover[i], 0) / n, price: sum(s.w.price), fund: sum(s.w.funding),
        cost: -(c / 1e4) * s.idx.reduce((a, i) => a + s.w.turnover[i], 0) / n * 52, weeks: n };
    }
    function wealth(r) { let a = 1; return r.map((x) => (a *= 1 + x)); }
    function draw() {
      const kr = series("kr", cost);
      const x = kr.days.map((d) => d * DAY);
      const sers = [], rows = [];
      if (showGross) {
        const g = series("kr", 0);
        sers.push({ name: "Korea before costs", short: "Before costs", values: wealth(g.r), colorVar: "--s-ref", width: 1.6 });
        rows.push(Object.assign({ name: "Korea before costs", _color: "--s-ref" }, stats(g, 0)));
      }
      sers.push({ name: `Korea (Upbit), net of ${cost} bp`, short: "Korea", values: wealth(kr.r), colorVar: "--s-kr" });
      rows.push(Object.assign({ name: `Korea (Upbit), ${cost} bp`, _color: "--s-kr", _cls: "hi" }, stats(kr, cost)));
      if (per === 1) {
        const jp = series("jp", cost);
        const byDay = new Map(jp.days.map((d, i) => [d, i]));
        const wl = wealth(jp.r);
        sers.push({ name: `Japan placebo (bitbank), net of ${cost} bp`, short: "Japan", values: kr.days.map((d) => (byDay.has(d) ? wl[byDay.get(d)] : null)), colorVar: "--s-jp" });
        rows.push(Object.assign({ name: `Japan placebo, ${cost} bp`, _color: "--s-jp" }, stats(jp, cost)));
      }
      const opts = { x, series: sers, height: 320, baseline: 1, yFmt: (v) => "$" + v.toFixed(2), tipFmt: (v) => (v == null ? "–" : "$" + v.toFixed(2)),
        endFmt: (v) => "$" + v.toFixed(2), aria: "Growth of one dollar for Korea, before costs, and the Japan placebo" };
      if (!chart) chart = CC.lineChart(chartHost, opts); else chart.update(opts);
      CC.table(tableHost, [
        { key: "name", label: "Series", num: false, swatch: true },
        { key: "ret", label: "Return, ann.", fmt: (v) => spct(v, 1) }, { key: "vol", label: "Volatility", fmt: (v) => pct(v, 0) },
        { key: "sharpe", label: "Sharpe", fmt: (v) => snum(v, 2) }, { key: "mdd", label: "Max drawdown", fmt: (v) => pct(v, 0) },
        { key: "fin", label: "$1 becomes", fmt: (v) => "$" + v.toFixed(2) }, { key: "turn", label: "Turnover/wk", fmt: (v) => v.toFixed(2) + "×" },
        { key: "price", label: "Price, ann.", fmt: (v) => spct(v, 1) }, { key: "fund", label: "Funding, ann.", fmt: (v) => spct(v, 1) },
        { key: "cost", label: "Costs, ann.", fmt: (v) => spct(v, 1) },
      ], rows, { compact: true });
    }
    draw();
  })();

  // ------------------------------------------------------------------ by year, funding by quintile
  (function () {
    const y = D.pnl_by_year;
    CC.barChart($("#year-chart"), {
      categories: y.map((r) => String(r.year) + (r.weeks < 50 ? "*" : "")),
      series: [
        { name: "Price", values: y.map((r) => r.price), colorVar: "--s-jp", extra: y.map((r) => ({ name: "Net for the year", value: spct(r.net, 0) })) },
        { name: "Funding", values: y.map((r) => r.funding), colorVar: "--s-kr", extra: y.map((r) => ({ name: "Net for the year", value: spct(r.net, 0) })) },
        { name: "Trading costs", values: y.map((r) => r.cost), colorVar: "--s-btc", extra: y.map((r) => ({ name: "Net for the year", value: spct(r.net, 0) })) },
      ],
      height: 280, yFmt: (v) => pct(v, 0), aria: "Bar chart of price, funding and cost contributions by year",
    });
    CC.barChart($("#bucket-chart"), {
      categories: qlab,
      series: [{ name: "Past-week funding, annualised (longs pay when positive)", values: qs.map((q) => q.fund7_ann),
        colorVars: qs.map((q) => (q.fund7_ann >= 0 ? "--div-pos" : "--div-neg")) }],
      height: 270, yFmt: (v) => pct(v, 0), valueLabels: true, labelFmt: (v) => spct(v, 1),
      aria: "Bar chart of perpetual funding rates by premium quintile",
    });
  })();

  // ------------------------------------------------------------------ risk
  (function () {
    const R = D.regime;
    CC.barChart($("#regime-chart"), {
      categories: R.map((r) => `${r.regime}\n${r.size} weeks`),
      series: [{ name: "Average weekly net return", values: R.map((r) => r.mean), colorVar: "--s-kr" }],
      height: 260, yFmt: (v) => pct(v, 1), valueLabels: true, labelFmt: (v) => spct(v, 2),
      aria: "Bar chart of weekly returns by Korean premium regime",
    });
    CC.table($("#worst-table"), [
      { key: "week", label: "Week of", num: false }, { key: "net", label: "Book, net", fmt: (v) => spct(v, 1) },
      { key: "btc", label: "Bitcoin", fmt: (v) => spct(v, 1) },
      { key: "drivers", label: "Largest losses (share of capital)", num: false, fmt: (v) => v.replace(/pp\)/g, " pts)").replace(/-/g, "−") },
    ], D.worst_weeks, { compact: true });
    CC.table($("#episode-table"), [
      { key: "episode", label: "Episode", num: false }, { key: "strategy", label: "Book", fmt: (v) => spct(v, 1) },
      { key: "long_leg", label: "Long leg", fmt: (v) => spct(v, 1) }, { key: "short_leg", label: "Short leg", fmt: (v) => spct(v, 1) },
      { key: "btc", label: "Bitcoin", fmt: (v) => spct(v, 1) },
    ], D.episodes, { compact: true });
    const names = { const: "Constant (weekly)", BTC_up: "BTC, up weeks", BTC_down: "BTC, down weeks", MKT_EW: "ALT: alts minus BTC",
      MOM: "MOM: crypto momentum", dVIX: "ΔVIX (10 points)", dKRW: "ΔKRW per USD", dKAPPA: "Δ aggregate premium" };
    CC.table($("#expo-table"), [
      { key: "factor", label: "Factor", num: false, fmt: (v) => names[v] || v },
      { key: "coef", label: "Beta", fmt: (v, r) => (r.factor === "const" ? spct(v, 2) : snum(v, 2)) }, { key: "t", label: "t (NW)", fmt: (v) => snum(v, 1) },
    ], D.exposures.table.map((r) => Object.assign({}, r, { _cls: Math.abs(r.t) > 2 ? "hi" : "" })), { compact: true });
    const L = D.liquidity, lk = Object.keys(L);
    CC.barChart($("#liq-chart"), {
      categories: lk.map((k) => k.replace(" third", "\nthird")),
      series: [{ name: "Gross P&L per year", values: lk.map((k) => L[k]), colorVars: lk.map((k) => (L[k] >= 0 ? "--div-pos" : "--div-neg")) }],
      height: 230, yFmt: (v) => pct(v, 0), valueLabels: true, labelFmt: (v) => spct(v, 1), aria: "Bar chart of P&L by liquidity tercile",
    });
    const C2 = D.concentration;
    const crow = Object.entries(C2.worst5).map(([c, v]) => ({ coin: c, pnl: v, kind: "Worst" }))
      .concat(Object.entries(C2.best5).reverse().map(([c, v]) => ({ coin: c, pnl: v, kind: "Best" })));
    CC.table($("#conc-table"), [
      { key: "kind", label: "", num: false }, { key: "coin", label: "Coin", num: false },
      { key: "pnl", label: "Total P&L, sum of weekly", fmt: (v) => spct(v, 1) },
    ], crow, { compact: true });
  })();

  // ------------------------------------------------------------------ the one robustness test: Japan placebo
  (function () {
    const jw = D.weekly.jp, kw = D.weekly.kr;
    const kByDay = new Map(kw.days.map((d, i) => [d, i]));
    const net = (w, i) => w.gross[i] - 0.001 * w.turnover[i];
    let a = 1, b = 1;
    const jv = [], kv = [];
    jw.days.forEach((d, i) => { a *= 1 + net(jw, i); jv.push(a); const k = kByDay.get(d); b *= 1 + (k == null ? 0 : net(kw, k)); kv.push(b); });
    CC.lineChart($("#placebo-chart"), {
      x: jw.days.map((d) => (d + 7) * DAY),
      series: [
        { name: "Korea (Upbit)", short: "Korea", values: kv, colorVar: "--s-kr" },
        { name: "Japan placebo (bitbank)", short: "Japan", values: jv, colorVar: "--s-jp" },
      ],
      height: 280, baseline: 1, yFmt: (v) => "$" + v.toFixed(2), tipFmt: (v) => "$" + v.toFixed(2), endFmt: (v) => "$" + v.toFixed(2),
      aria: "Growth of one dollar for the same rule in Korea and in Japan over the same weeks, net of 10 bp",
    });
    CC.table($("#rob-table"), [
      { key: "test", label: "Market and weeks", num: false }, { key: "weeks", label: "Weeks", fmt: (v) => String(v) },
      { key: "avg_coins", label: "Coins/wk", fmt: (v) => (v == null ? "–" : num(v, 0)) },
      { key: "gross_return", label: "Gross, ann.", fmt: (v) => spct(v, 1) }, { key: "net_return", label: "Net, ann.", fmt: (v) => spct(v, 1) },
      { key: "sharpe_gross", label: "Sharpe gross", fmt: (v) => snum(v, 2) }, { key: "sharpe_net", label: "Sharpe net", fmt: (v) => snum(v, 2) },
      { key: "t_net", label: "t, net", fmt: (v) => snum(v, 1) },
      { key: "max_dd", label: "Max DD", fmt: (v) => pct(v, 0) }, { key: "funding_ann", label: "Funding, ann.", fmt: (v) => spct(v, 1) },
    ], [Object.assign({}, main, { test: "Korea, all five years", _cls: "hi" }), Object.assign({}, krSame, { test: "Korea, the placebo's weeks" }),
      Object.assign({}, jpn, { test: "Japan placebo (bitbank)" })], { compact: true });
  })();

  // ------------------------------------------------------------------ verdicts
  (function () {
    const host = $("#verdicts");
    const items = [
      ["yes", "Supported", "H1 · Segmentation", `Korea averages ${pct(h1[0].mean, 1)} with a ${num(h1[0].half_life_days, 0)}-day half-life; Japan ${pct(h1[1].mean, 1)}, gone within a day.`],
      ["yes", "Supported", "H2 · Reversal", `Regressions: ${spct(fmSig.coef, 1)} a week per point of π (t = ${snum(fmSig.t_nw, 1)}). As a trade: ${spct(main.net_return, 1)} a year net, Sharpe ${num(main.sharpe_net, 2)}, t = ${num(main.t_net, 1)}.`],
      ["no", "Not here", "H3 · Froth", `Slope ${spct(D.h3.coef_4w / 100, 2)} per point (t = ${snum(D.h3.t_4w, 1)}); the pre-set brake lowers bitcoin's Sharpe from ${num(D.overlay.stats.btc.sharpe, 2)} to ${num(D.overlay.stats.overlay.sharpe, 2)}.`],
      ["yes", "Supported", "H4 · Channel", `The top quintile's premium shrinks ${Math.abs(q5.dpi_bp).toFixed(0)} bp in a week: Korean price ${spct(q5.dlocal_rel_pct / 100, 2)}, world price ${spct(q5.dworld_rel_pct / 100, 2)}.`],
      ["yes", "Passed", "Japan placebo", `The same rule where capital is free: ${spct(jpn.net_return, 0)} a year, Sharpe ${snum(jpn.sharpe_net, 2)}, against ${num(krSame.sharpe_net, 2)} for Korea over the same weeks.`],
      ["part", "Thin", "The trade", `Price ${spct(main.price_ann, 0)}, funding ${spct(main.funding_ann, 0)}, costs ${spct(-main.cost_ann, 0)} a year; breaks even at ${D.breakeven_bp.toFixed(0)} bp per unit traded.`],
    ];
    items.forEach(([cls, pill, t, d]) => {
      const v = el("div", "verdict", host);
      el("span", "pill " + cls, v, pill); el("p", "t", v, t); el("p", "d", v, d);
    });
  })();
})();
