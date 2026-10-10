#!/usr/bin/env python3
"""Build the self-contained project HTML page from output/results.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = json.loads((ROOT / "output" / "results.json").read_text())
OUT = ROOT / "index.html"


def dumps(obj) -> str:
    return json.dumps(obj, separators=(",", ":"))


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>MFE 230GB — Policy Path and Terms of Trade</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {
    --navy: #0B1F3A;
    --gold: #C4A35A;
    --teal: #1D6A6A;
    --risk: #B23A48;
    --ice: #EEF3F8;
    --muted: #5C6B7A;
    --ink: #1A1A1A;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: "Calibri", "Segoe UI", sans-serif;
    color: var(--ink);
    background: #fff;
    line-height: 1.45;
  }
  header {
    background: var(--navy);
    color: #fff;
    padding: 2.4rem 8vw 2rem;
  }
  header .kicker {
    display: inline-block;
    background: var(--gold);
    color: var(--navy);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 0.28rem 0.7rem;
    border-radius: 4px;
  }
  h1 { font-family: Cambria, Georgia, serif; font-size: 2.4rem; font-weight: 600; margin: 0.8rem 0 0.5rem; }
  header p { color: #D5DEE8; max-width: 46rem; }
  nav {
    position: sticky; top: 0; z-index: 5;
    background: var(--navy);
    padding: 0.6rem 8vw;
    display: flex; gap: 1.2rem; flex-wrap: wrap;
    border-top: 1px solid #163152;
  }
  nav a { color: var(--gold); text-decoration: none; font-size: 0.9rem; }
  nav a:hover { color: #fff; }
  main { padding: 0 8vw 4rem; max-width: 1200px; }
  section { padding-top: 2.4rem; }
  h2 { font-family: Cambria, Georgia, serif; color: var(--navy); font-size: 1.7rem; margin-bottom: 0.4rem; }
  h3 { color: var(--navy); font-size: 1.15rem; margin: 1.2rem 0 0.4rem; }
  .lede { color: var(--muted); font-style: italic; margin-top: 0; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
  @media (max-width: 900px) {
    .grid2, .grid3, .grid4 { grid-template-columns: 1fr; }
    header, nav, main { padding-left: 1.2rem; padding-right: 1.2rem; }
  }
  .card { background: var(--ice); border-radius: 10px; padding: 1.1rem 1.2rem; }
  .card.dark { background: var(--navy); color: #fff; }
  .card.dark .lbl { color: #D5DEE8; }
  .stat { font-size: 2rem; font-weight: 700; color: var(--navy); }
  .card.dark .stat { color: #fff; }
  .lbl { font-size: 0.88rem; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
  th { background: var(--navy); color: #fff; text-align: left; padding: 0.55rem 0.7rem; }
  td { padding: 0.5rem 0.7rem; border-bottom: 1px solid #e2e8f0; }
  tr:nth-child(even) td { background: var(--ice); }
  .neg { color: var(--risk); }
  .pos { color: var(--teal); }
  .chart { width: 100%; height: 380px; margin: 0.6rem 0 1.2rem; }
  .chart.tall { height: 440px; }
  footer { background: var(--navy); color: #D5DEE8; padding: 1.4rem 8vw; font-size: 0.9rem; }
  code { font-size: 0.88em; background: var(--ice); padding: 0.05rem 0.3rem; border-radius: 3px; }
  ul.tight li { margin: 0.25rem 0; }
</style>
</head>
<body>
<header>
  <div class="kicker">MFE 230GB · 8 OCTOBER 2026</div>
  <h1>Policy Path and Terms of Trade</h1>
  <p>Two identified trading strategies for Currency Markets. The first trades G10 FX and duration around policy-path information. The second trades emerging-market NDFs around oil terms-of-trade shocks. Prediction markets are the alternative data; the economic logic is Topics 3–5, not a Sharpe hunt.</p>
</header>
<nav>
  <a href="#idea">Idea</a>
  <a href="#s1">Policy Path</a>
  <a href="#s2">Terms of Trade</a>
  <a href="#pm">Prediction markets</a>
  <a href="#risk">Risk</a>
  <a href="#data">Replication</a>
</nav>
<main>
<section id="idea">
  <h2>One theme, two books</h2>
  <p class="lede">At horizons under a year, exchange rates are mostly demand and information flow, not scheduled macro. We trade that claim in two universes that fail in different weeks.</p>
  <div class="grid3">
    <div class="card"><div class="stat">&le; 5%</div><div class="lbl">of monthly FX variance explained by measured macro (Topic 4)</div></div>
    <div class="card"><div class="stat">64%</div><div class="lbl">of daily DM/USD explained by interdealer order flow (Evans–Lyons)</div></div>
    <div class="card"><div class="stat">82%</div><div class="lbl">of FX variation attributed to latent demand (Koijen–Yogo 2026)</div></div>
  </div>
  <div class="grid2" style="margin-top:1rem">
    <div class="card">
      <h3>Strategy 1 · OECD · Policy Path</h3>
      <p>G10 FX forwards, vol-targeted, with a VIX crash filter and a policy-path overlay from 2-year yields and Polymarket P(cut). Carry is harvested only when global risk is quiet — raw developed HML has not paid since 2010.</p>
      <p><b>Universe</b> EUR, JPY, GBP, AUD, CAD, CHF, SEK, NOK, NZD vs USD<br>
      <b>Horizon</b> weekly · 2 bp half-spread · 10% vol target on the combined book</p>
    </div>
    <div class="card">
      <h3>Strategy 2 · EM · Terms of Trade</h3>
      <p>Dollar-controlled oil betas, estimated 2010–19 and frozen. Long the two highest-beta EM names, short the two lowest, timed on last week’s Brent sign. The mechanism is Topic 3; the trading friction is Topic 1 (NDF spreads).</p>
      <p><b>Live names</b> long BRL, THB · short ZAR, INR<br>
      <b>Horizon</b> weekly (mechanism) and monthly (live NDF) · 15 bp round-trip</p>
    </div>
  </div>
</section>

<section id="s1">
  <h2>Policy Path</h2>
  <p class="lede">Unconditional G10 carry is the wrong trade. Conditioning on global risk, and overlaying policy-path shocks, is the course-consistent one.</p>
  <div class="grid4" id="s1-stats"></div>
  <div id="s1-equity" class="chart tall"></div>
  <h3>Developed HML carry, net of bid–ask (Lustig–Roussanov–Verdelhan)</h3>
  <p>Same series as Problem Set 1. Full-sample Sharpe 0.24; since 2010, ~0. Low-VIX months 0.54; high-VIX months −0.03. Skipping the top VIX quintile raises Sharpe from 0.21 to 0.45. October 2008: −13.8% in one month.</p>
  <div id="s1-lustig" class="chart"></div>
  <h3>Our G10 book after 2 bp costs</h3>
  <p>Cross-sectional carry-to-vol, long 3 / short 3, plus a VIX filter (flat when VIX is above its expanding 80th percentile) plus a 2-year overlay: when the US 2-year rallies more than 15 bp, add long EUR+JPY and a duration sleeve. Combined Sharpe <b>0.62</b> (2000–2026; VIX-filtered carry alone 0.66), <b>0.84</b> out of sample 2020–26, max drawdown −19%. The book is in the market 83% of weeks with gross turnover of about 4.5× a year, so costs are roughly 9 bp a year. Corrected run of 7 Oct 2026: the monthly OECD rate is now carried across the weeks of the month (an earlier draft was flat three weeks in four and reported 0.35 / 0.57).</p>
</section>

<section id="s2">
  <h2>Terms of Trade</h2>
  <p class="lede">A 10% ToT improvement appreciates the real exchange rate (Topic 3). A static exporter–importer book does not pay. Timing the oil shock does — until you pay NDF costs every week.</p>
  <div class="grid4" id="s2-stats"></div>
  <div id="s2-betas" class="chart"></div>
  <div id="s2-equity" class="chart tall"></div>
  <h3>What the costs say</h3>
  <p>Gross, oil-timed long BRL+THB / short ZAR+INR has Sharpe <b>0.28</b> versus <b>0.04</b> always-on (2010–2026). That is the mechanism test: the premium is for bearing the shock, not for sitting in BRL. The breakeven half-spread is about 4 bp (gross 4 bp a week against 0.98 units of turnover a week); charging the 15 bp NDF spread wipes the edge (net Sharpe −0.74). Monthly holding does not restore it. A placebo that shuffles the Brent signs beats 0.28 about 13% of the time, and the timed pair's residual dollar beta is 0.04. EM ToT is identifiable and not cheaply tradable at NDF spreads — which is what Topic 1’s 10–16 bp EM spread chart predicted.</p>
</section>

<section id="pm">
  <h2>Prediction markets</h2>
  <p class="lede">Polymarket Fed-decision contracts, December 2024 – January 2026. P(cut) is the sum of the 25 bp and 50+ bp decrease markets, averaged across live meetings.</p>
  <div id="pm-chart" class="chart"></div>
  <div class="grid2">
    <div class="card">
      <h3>Lead/lag vs the 2-year</h3>
      <p>Weekly ΔP(cut) correlates <b>0.42</b> with last week’s 2-year rally and 0.27 contemporaneously. In this sample the prediction market <em>lags</em> the 2s. That is the brief’s own falsifier: if the ΔP has already printed in 2-year yields, we are late. We therefore use 2-year changes as the long-sample policy-path shifter and treat Polymarket as the 2025–26 overlay and as a disagreement/confirmation series, not as a free look-ahead.</p>
    </div>
    <div class="card">
      <h3>Short-sample overlay</h3>
      <p>Adding a EUR/JPY overlay when weekly ΔP(cut) exceeds +5 pp, on top of the VIX-filtered G10 book, produces Sharpe 1.18 from January 2025 to October 2026 (n = 92 weeks, 79 active); the overlay on its own is 0.67 on 57 weeks with 31 trigger weeks. That number is too small a sample to be a headline. It is reported as a live-period illustration, with the lead/lag result above attached.</p>
    </div>
  </div>
  <div id="pm-leadlag" class="chart"></div>
</section>

<section id="risk">
  <h2>When each book loses money</h2>
  <div class="grid2">
    <div class="card">
      <h3>Policy Path</h3>
      <ul class="tight">
        <li><b>Carry crash.</b> Developed HML: Oct 2008 −13.8%, Mar 1995 −10.4%, Oct 1998 −8.5%. The VIX filter is supposed to cut these; if it does not, the strategy is rejected.</li>
        <li><b>Fiscal dominance.</b> Yields up, currency down (UK 2022, Japan 2025–26). The duration overlay is then the wrong side.</li>
        <li><b>Announcement catch-up.</b> If PM ΔP only predicts inside the FOMC window, we are trading the statement, not order flow.</li>
      </ul>
    </div>
    <div class="card">
      <h3>Terms of Trade</h3>
      <ul class="tight">
        <li><b>Oil crash.</b> 13 Mar 2020 Brent −35%, BRL −2.6%, ZAR −4.3%. 20 Mar: oil −23%, BRL −4.9%, ZAR −7.0%.</li>
        <li><b>Country risk.</b> A Brazil or South Africa week can dominate oil. Single-name cap 35%.</li>
        <li><b>NDF liquidity.</b> 15 bp round-trip is enough to erase weekly timing. That is a result, not a footnote.</li>
        <li><b>Dollar wave.</b> Betas are estimated with dDollar on the right-hand side; residual dollar beta is the specification check.</li>
      </ul>
    </div>
  </div>
  <h3>Worst oil weeks, 2010–2026</h3>
  <div id="crash-table"></div>
</section>

<section id="data">
  <h2>Replication</h2>
  <p>From the <code>project</code> folder:</p>
  <pre style="background:var(--ice);padding:1rem;border-radius:8px;overflow:auto">python3 code/run_strategies.py
python3 code/build_html.py</pre>
  <p><b>Prices.</b> FRED H.10 FX, Brent, VIX, OECD 3-month rates, DGS2/DGS10. Lustig currency portfolios (developed, net of spreads). <b>Prediction markets.</b> Polymarket Data API v2 price histories for Fed-decision contracts (cut 25, cut 50+, hold, hike) and Iran-strike contracts. Raw JSON is in <code>data/</code>.</p>
  <p><b>AI.</b> Cursor (Grok 4.6) drafted the slide deck, the backtest code, and this page. Prompts and generated code that materially contributed are listed in <code>README.md</code>. No result was taken from the model without being recomputed from the files in <code>data/</code>.</p>
  <p class="lbl">Generated __DATE__ · MFE 230GB Currency Markets · Haas School of Business</p>
</section>
</main>
<footer>MFE 230GB Final Project · Policy Path · Terms of Trade · Prediction markets as demand shifters, not as a second Taylor rule.</footer>
<script>
const R = __RESULTS__;
const NAVY = "#0B1F3A", GOLD = "#C4A35A", TEAL = "#1D6A6A", RISK = "#B23A48", MUTED = "#5C6B7A";
const layout = {
  paper_bgcolor: "#fff", plot_bgcolor: "#fff",
  font: { family: "Calibri, Segoe UI, sans-serif", color: NAVY, size: 13 },
  margin: { t: 36, r: 24, b: 48, l: 52 },
  legend: { orientation: "h", y: 1.12 },
  xaxis: { gridcolor: "#EEF3F8" },
  yaxis: { gridcolor: "#EEF3F8", tickformat: ".0%" },
  hovermode: "x unified"
};
function xy(arr, key) {
  return { x: arr.map(d => d.date), y: arr.map(d => d[key]) };
}
function card(el, items) {
  el.innerHTML = items.map(([v, l]) =>
    `<div class="card"><div class="stat">${v}</div><div class="lbl">${l}</div></div>`
  ).join("");
}
function fmt(x) { return (x>=0?"+":"") + (x*100).toFixed(1) + "%"; }
function sh(s) { return s.toFixed(2); }

const s1 = R.strategy1, s2 = R.strategy2, L = R.lustig;
card(document.getElementById("s1-stats"), [
  [sh(s1.combined.sharpe), "Sharpe, combined book, 2000–2026, after 2 bp"],
  [sh(s1.oos.sharpe), "Sharpe, 2020–2026 out of sample"],
  [fmt(s1.combined.mdd), "Max drawdown"],
  [(s1.combined.pct_active*100).toFixed(0)+"%", "Weeks with a non-zero position"],
]);
card(document.getElementById("s2-stats"), [
  [sh(s2.timed.sharpe), "Sharpe, oil-timed, gross"],
  [sh(s2.always.sharpe), "Sharpe, always-on exporter LS (rejected)"],
  [sh(s2.shock_net.sharpe), "Sharpe after 15 bp weekly NDF costs"],
  [s2.longs.join("+")+" / "+s2.shorts.join("+"), "Long / short from 2010–19 oil betas"],
]);

Plotly.newPlot("s1-equity", [
  { ...xy(s1.equity_raw, "v"), name: "Carry-to-vol, 2 bp", type: "scatter", mode: "lines", line: { color: MUTED, width: 1.5 } },
  { ...xy(s1.equity_filt, "v"), name: "VIX-filtered", type: "scatter", mode: "lines", line: { color: TEAL, width: 2 } },
  { ...xy(s1.equity_combined, "v"), name: "VIX + 2y overlay", type: "scatter", mode: "lines", line: { color: GOLD, width: 2.4 } },
], Object.assign({}, layout, { title: "Strategy 1 cumulative excess return", yaxis: { gridcolor: "#EEF3F8", tickformat: ".0%" } }), {responsive:true, displayModeBar:false});

Plotly.newPlot("s1-lustig", [{
  x: L.equity.map(d => d.date), y: L.equity.map(d => d.cum),
  type: "scatter", mode: "lines", name: "Developed HML net",
  line: { color: NAVY, width: 2 }
}], Object.assign({}, layout, { title: "Lustig developed HML, net of spreads", showlegend: false }), {responsive:true, displayModeBar:false});

const betaNames = Object.keys(s2.betas);
Plotly.newPlot("s2-betas", [{
  y: betaNames, x: betaNames.map(k => s2.betas[k].oil),
  type: "bar", orientation: "h",
  marker: { color: betaNames.map(k => s2.betas[k].oil >= 0 ? TEAL : RISK) }
}], Object.assign({}, layout, {
  title: "Oil beta, weekly, 2010–2019 (dollar-controlled)",
  yaxis: { gridcolor: "#EEF3F8", automargin: true },
  xaxis: { gridcolor: "#EEF3F8", tickformat: ".3f", title: "b on dBrent" }
}), {responsive:true, displayModeBar:false});

Plotly.newPlot("s2-equity", [
  { ...xy(s2.equity_always, "v"), name: "Always-on LS", type: "scatter", mode: "lines", line: { color: MUTED, width: 1.5 } },
  { ...xy(s2.equity_timed, "v"), name: "Oil-timed, gross", type: "scatter", mode: "lines", line: { color: GOLD, width: 2.4 } },
  { ...xy(s2.equity_shock_net, "v"), name: "After 15 bp weekly NDF", type: "scatter", mode: "lines", line: { color: RISK, width: 2 } },
], Object.assign({}, layout, { title: "Strategy 2 cumulative excess return" }), {responsive:true, displayModeBar:false});

if (R.pm.pcut && R.pm.pcut.length) {
  Plotly.newPlot("pm-chart", [{
    x: R.pm.pcut.map(d => d.date), y: R.pm.pcut.map(d => d.v),
    type: "scatter", mode: "lines", name: "P(cut)",
    line: { color: GOLD, width: 2 }
  }], Object.assign({}, layout, {
    title: "Polymarket implied P(Fed cut), averaged across live meetings",
    yaxis: { gridcolor: "#EEF3F8", tickformat: ".0%", range: [0, 1] }
  }), {responsive:true, displayModeBar:false});
}

Plotly.newPlot("pm-leadlag", [
  { x: s1.leadlag_pcut_dgs2.map(d => d.lag), y: s1.leadlag_pcut_dgs2.map(d => d.corr),
    name: "ΔP(cut) vs −Δ 2y", type: "bar", marker: { color: GOLD } },
  { x: s1.leadlag_dgs2_usd.map(d => d.lag), y: s1.leadlag_dgs2_usd.map(d => d.corr),
    name: "Δ 2y vs −Δ dollar (long sample)", type: "bar", marker: { color: TEAL } },
], Object.assign({}, layout, {
  title: "Lead/lag correlations (k>0 means the first series leads)",
  barmode: "group",
  xaxis: { title: "lag k, weeks", dtick: 1, gridcolor: "#EEF3F8" },
  yaxis: { title: "corr", tickformat: ".2f", gridcolor: "#EEF3F8", zeroline: true }
}), {responsive:true, displayModeBar:false});

document.getElementById("crash-table").innerHTML =
  "<table><thead><tr><th>Week</th><th>Brent</th><th>BRL</th><th>ZAR</th></tr></thead><tbody>" +
  s2.crashes.map(r => `<tr><td>${r.date}</td><td class="neg">${(r.oil*100).toFixed(1)}%</td>
    <td class="${r.BRL<0?'neg':'pos'}">${r.BRL==null?'':(r.BRL*100).toFixed(1)+'%'}</td>
    <td class="${r.ZAR<0?'neg':'pos'}">${r.ZAR==null?'':(r.ZAR*100).toFixed(1)+'%'}</td></tr>`).join("") +
  "</tbody></table>";
</script>
</body>
</html>
"""

text = HTML.replace("__RESULTS__", dumps(RESULTS)).replace("__DATE__", RESULTS.get("generated", ""))
OUT.write_text(text)
print("wrote", OUT, "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    pass
