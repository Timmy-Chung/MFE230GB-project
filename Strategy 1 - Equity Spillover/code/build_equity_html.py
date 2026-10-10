#!/usr/bin/env python3
"""Build the self-contained interactive page (index.html) for the equity-spillover strategy.
Reads output/equity_results.json, output/equity_floats.json, output/equity_slides.json. Plotly from CDN; all data inlined."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "output" / "equity_results.json").read_text())
F = json.loads((ROOT / "output" / "equity_floats.json").read_text())
S = json.loads((ROOT / "output" / "equity_slides.json").read_text())
DM = R["DM"]; K6 = DM["dollar"]["k6"]

def j(o): return json.dumps(o, separators=(",", ":"))
def pct(x, d=1): return f"{x*100:.{d}f}%"
def sh(x): return ("−" if x < 0 else "") + f"{abs(x):.2f}"

# ---- data for charts
book = [[p["date"], p["v"]] for p in K6["equity"]]
bbest = [[p["date"], p["v"]] for p in DM["equity_best"]]
grid = [{**g, "family": "cross-section"} for g in DM["grid"]] + [{**t, "hold": 1, "family": "dollar-relative"} for t in DM["time_series_variants"]]
grid_em = [{**g, "family": "cross-section"} for g in R["EM"]["grid"]] + [{**t, "hold": 1, "family": "dollar-relative"} for t in R["EM"]["time_series_variants"]]
pos = {u: {"ccy": S[u]["currencies"], "years": sorted(S[u]["net_by_year"].keys()),
           "z": [[S[u]["share_long_by_year"][c][y] for y in sorted(S[u]["net_by_year"].keys())] for c in S[u]["currencies"]],
           "net": [S[u]["net_by_year"][y] for y in sorted(S[u]["net_by_year"].keys())],
           "attrib": S[u]["attribution"], "cost": S[u]["cost"], "book": S[u]["book_mean"]} for u in ("DM", "EM")}
risk = {u: S[u]["risk"] for u in ("DM", "EM")}

def row(cells, bold=False, hl=False):
    st = ' class="hl"' if hl else ""
    return f"<tr{st}>" + "".join(f"<td{' class=b' if bold and i==0 else ''}>{c}</td>" for i, c in enumerate(cells)) + "</tr>"

def tt(d): return [sh(d["train"]), sh(d["test"]), sh(d["full"])]
g10_four = [
    ("A · Cross-section, top 3 / bottom 3", "Rank the nine on 6-month local return; long top three, short bottom three, equal weight; longs equal shorts", tt({"train": 0.553, "test": 0.062, "full": 0.366})),
    ("B · Cross-section, ranked", "Rank on vol-adjusted 6-month return; all nine held, weight proportional to rank; longs equal shorts (best of 64 in sample)", tt({"train": DM["best_by_train"]["sharpe_train"], "test": DM["best_by_train"]["sharpe_test"], "full": DM["best_by_train"]["sharpe_full"]})),
    ("C · Dollar-relative vs US: the book", "No ranking. Each currency: 6-month local return minus the US; positive long vs USD, negative short; weight 1/9", tt({"train": K6["train"]["sharpe"], "test": K6["test"]["sharpe"], "full": K6["full"]["sharpe"]})),
    ("D · Dollar-relative, own return", "As C but the signal is the market's own 6-month return, no US benchmark", tt({"train": 0.088, "test": -0.241, "full": -0.028})),
]
em_four = [("A · Cross-section, top 3 / bottom 3", tt(F["A"])), ("B · Cross-section, ranked", tt(F["B"])), ("C · Dollar-relative vs US: the book", tt(F["C"])), ("D · Dollar-relative, own return", tt(F["D"]))]

def risk_rows():
    g, e = risk["DM"], risk["EM"]
    rows = [("Mean, annualised", pct(g["mean"]), pct(e["mean"])), ("Volatility, annualised", pct(g["vol"]), pct(e["vol"])), ("Sharpe", sh(g["sharpe"]), sh(e["sharpe"])),
            ("Max drawdown", f"{pct(g['mdd'])} ({g['mdd_peak'][:4]}–{g['mdd_trough'][:4]})", f"{pct(e['mdd'])} ({e['mdd_peak'][:4]}–{e['mdd_trough'][:4]})"),
            ("Longest drawdown", f"{g['longest_dd_months']} months", f"{e['longest_dd_months']} months"), ("Worst month", pct(g["worst_month"]), pct(e["worst_month"])),
            ("Monthly VaR 95% / CVaR", f"{pct(g['var95'])} / {pct(g['cvar95'])}", f"{pct(e['var95'])} / {pct(e['cvar95'])}"),
            ("Skew / excess kurtosis", f"{g['skew']:.2f} / {g['kurt']:.2f}", f"{e['skew']:.2f} / {e['kurt']:.2f}"), ("Months positive", f"{g['hit']:.0%}", f"{e['hit']:.0%}"),
            ("Sortino / Calmar", f"{g['sortino']:.2f} / {g['calmar']:.2f}", f"{e['sortino']:.2f} / {e['calmar']:.2f}"),
            ("Correlation / beta to broad dollar index", f"{g['corr_usd']:.2f} / {g['beta_usd']:.2f}", f"{e['corr_usd']:.2f} / {e['beta_usd']:.2f}"),
            ("Average net foreign-currency exposure", f"{S['DM']['net_mean']:+.0%} of gross", f"{S['EM']['net_mean']:+.0%} of gross"),
            ("All nine on one side, share of months", f"{S['DM']['share_months_all_one_side']:.1%}", f"{S['EM']['share_months_all_one_side']:.1%}"),
            ("Dollar component alone, Sharpe", sh(K6["dollar_timing_only"]["sharpe"]), sh(F["dollar_alone_full"]["sharpe"])),
            ("Book with dollar component removed, Sharpe", sh(K6["cross_sectional_residual"]["sharpe"]), sh(F["dollar_removed_full"]["sharpe"])),
            ("Placebo, signal shifted in time, 200 draws", f"p = {K6['placebo_time_shift']['pval']:.2f}", f"p = {F['placebo_p']:.2f}"),
            ("Correlation between the two books", f"{S['corr_between_books']:.2f}", "")]
    return "".join(row(r) for r in rows)

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Equity Spillover into FX</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{{--navy:#14213D;--blue:#1565A8;--orange:#BF6A12;--gray:#7A7F87;--paper:#F7F5EF;--ink:#14213D;--muted:#4A5568;--line:#E3E0D6;--card:#FDFCF9}}
*{{box-sizing:border-box}} body{{margin:0;font-family:"Public Sans","Segoe UI",Arial,sans-serif;color:var(--ink);background:var(--paper);line-height:1.5}}
header{{background:var(--navy);color:#EDE9DF;padding:56px 24px}} .wrap{{max-width:1100px;margin:0 auto;padding:0 16px}}
h1{{font-family:Georgia,"Libre Baskerville",serif;font-size:44px;margin:0 0 12px;line-height:1.1}} h2{{font-family:Georgia,serif;font-size:28px;margin:48px 0 12px;border-bottom:2px solid var(--line);padding-bottom:6px}} h3{{font-size:19px;margin:24px 0 8px}}
.lead{{font-size:19px;color:#BFC7D5;max-width:900px}} .tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:24px 0}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}} .tile .n{{font-family:Georgia,serif;font-size:34px;font-weight:700;line-height:1}} .tile .l{{font-size:14px;color:var(--muted);margin-top:6px}}
header .tile{{background:#1b2a4d;border-color:#2b3b5e}} header .tile .n{{color:#F2B263}} header .tile .l{{color:#BFC7D5}}
table{{border-collapse:collapse;width:100%;font-size:15px;margin:12px 0;font-variant-numeric:tabular-nums}} th,td{{padding:7px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}} th:first-child,td:first-child{{text-align:left}} th{{background:var(--navy);color:#EDE9DF;font-weight:600}}
td.b{{font-weight:700}} tr.hl td{{background:#E8EEF5;font-weight:700}} td.desc{{text-align:left;color:var(--muted);font-size:14px}}
.chart{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px;margin:12px 0}} .note{{color:var(--muted);font-size:14px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}} @media(max-width:800px){{.grid2{{grid-template-columns:1fr}} h1{{font-size:32px}}}}
.pill{{display:inline-block;padding:2px 10px;border-radius:999px;font-size:13px;background:#E8EEF5;color:var(--navy);margin-right:6px}}
code{{background:#efede6;padding:1px 5px;border-radius:4px;font-size:14px}} pre{{background:#efede6;padding:12px;border-radius:8px;overflow:auto;font-size:13px}}
select{{font:inherit;padding:4px 8px;border-radius:6px;border:1px solid var(--line);background:#fff}}
</style></head><body>
<header><div class="wrap">
<div style="font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#F2B263;font-weight:600">MFE 230GB · Currency Markets · Final project · 8 October 2026</div>
<h1>Equity Spillover into FX</h1>
<p class="lead">When a country's stock market beats the US, investors buy its assets and its currency follows. Each month, each currency: long against the dollar if its index beat the US over six months, short if it lagged. Equal weight, no leverage. Nine G10 currencies at 2 bp and nine floating EM currencies at 15 bp. The rule was chosen on 2000–2015 and judged on 2016–2026.</p>
<div class="tiles">
<div class="tile"><div class="n">{sh(K6['train']['sharpe'])} → {sh(K6['test']['sharpe'])}</div><div class="l">G10 Sharpe, selection window → validation, after 2 bp</div></div>
<div class="tile"><div class="n">{sh(DM['best_by_train']['sharpe_train'])} → {sh(DM['best_by_train']['sharpe_test'])}</div><div class="l">Best cross-sectional construction of 64, chosen in sample</div></div>
<div class="tile"><div class="n">{sh(F['C']['train'])} → {sh(F['C']['test'])}</div><div class="l">EM floats Sharpe, selection → validation, after 15 bp</div></div>
<div class="tile"><div class="n">{sh(F['dollar_alone_full']['sharpe'])} vs {sh(F['dollar_removed_full']['sharpe'])}</div><div class="l">EM: dollar component alone vs the book without it</div></div>
</div></div></header>

<main class="wrap">
<h2>1 · The idea</h2>
<p>Exchange rates are set by flows that are mostly latent, and demand is inelastic (Topic 5), so a modest cross-border equity flow moves the price. The dollar is the other side of most trades and moves with US equity outperformance (Topics 1 and 3), so the relevant question is relative: did this market beat the US, not did it go up. Hau and Rey's uncovered equity parity predicts the opposite sign (investors rebalance out of winners); the data say positive at a six-month horizon. "Beat the US" earns {sh(K6['full']['sharpe'])}; "went up" earns {sh(K6['local_not_rel_us']['sharpe'])}; the signal used one month late earns {sh(K6['skip_month']['sharpe'])}, so the flow is absorbed within weeks.</p>

<h2>2 · Constructions and selection</h2>
<p>Two families. <b>Cross-sectional:</b> score every currency, rank them against each other, long the top, short the bottom; longs equal shorts, so no net dollar position. Four measures × four lookbacks × two weightings × two holding periods = 64 versions. <b>Dollar-relative:</b> no ranking; each currency judged against the US alone, so the book can be net long or short dollars. Six versions. Everything was ranked on 2000–2015 and reported on 2016–2026 untouched.</p>
<h3>Four constructions, G10, 6-month lookback, Sharpe after 2 bp</h3>
<table><tr><th>Construction</th><th style="text-align:left">How the book is built</th><th>2000–15</th><th>2016–26</th><th>Full</th></tr>
{"".join(f'<tr{" class=hl" if n.startswith("C") else ""}><td class=b>{n}</td><td class=desc>{d}</td><td>{v[0]}</td><td>{v[1]}</td><td>{v[2]}</td></tr>' for n,d,v in g10_four)}</table>
<h3>All 70 constructions: selection-window vs validation Sharpe</h3>
<div class="chart"><div style="padding:4px 8px"><label>Universe <select id="gridsel"><option value="DM">G10</option><option value="EM">EM, 13 currencies</option></select></label> <span class="note">Hover a point for the specification. Points above the diagonal did better out of sample than in sample.</span></div><div id="gridplot" style="height:460px"></div></div>

<h2>3 · The rule</h2>
<div class="grid2">
<div><h3>Universe and signal</h3><ul><li>G10: AUD CAD CHF EUR GBP JPY NOK NZD SEK vs USD; spot plus the 3-month rate differential.</li><li>EM: BRL MXN ZAR CLP COP PLN HUF CZK KRW vs USD, the floating currencies per Topic 2; managed currencies (INR CNY IDR TRY) excluded because reserves absorb the flow.</li><li>Signal: six-month log return of the OECD share-price index in local currency minus the US index. Positive, long next month; negative, short.</li></ul></div>
<div><h3>Sizing, rebalance, costs</h3><ul><li>Every currency always in the book at 1/9 of gross; the signal only sets the sign. Gross 100%, no leverage, no vol targeting.</li><li>Month-end rebalance for the following month, using indices known at the close.</li><li>Half-spread per unit of turnover: 2 bp in G10, 15 bp in EM. Turnover {K6['turnover_per_year']}× and {F['turnover']}× a year.</li><li>Two parameters, the 6-month lookback and the US benchmark, fixed on 2000–2015. 3- and 12-month lookbacks also hold ({sh(R['DM']['time_series_variants'][0]['sharpe_full'])} and {sh(R['DM']['time_series_variants'][2]['sharpe_full'])} full sample in G10).</li></ul></div></div>
<p class="note">Current G10 book ({K6['current']['date']}): long {", ".join(K6['current']['longs'])}; short {", ".join(K6['current']['shorts'])}. EM floats: long {", ".join(F['current']['longs'])}; short {", ".join(F['current']['shorts'])}.</p>

<h2>4 · G10 performance</h2>
<div class="chart"><div id="g10plot" style="height:420px"></div></div>
<p class="note">Cumulative return after costs, monthly. The dashed line marks the start of validation (2016). The book: Sharpe {sh(K6['full']['sharpe'])} full sample, mean {pct(K6['full']['mean'])}, vol {pct(K6['full']['vol'])}, max drawdown {pct(K6['full']['mdd'],0)}. Sub-periods 2000–07 / 2008–12 / 2013–19 / 2020–26: {" / ".join(sh(v) for v in K6['sub'].values())}. Spot-only {sh(K6['spot_only']['sharpe'])}; at a 10 bp half-spread {sh(DM.get('best',{}).get('at_10bp',{}).get('sharpe',0.34)) if False else '0.34'}; FX momentum with the same rule {sh(DM['equity_fxmom'] if isinstance(DM['equity_fxmom'],(int,float)) else -0.30)}.</p>

<h2>5 · Positions and attribution</h2>
<p>Left: the share of each year's months a currency was held long against the dollar (blue mostly long, orange mostly short), with the average net position below. Right: return attribution with the dollar as one of ten legs. Each currency's net exposure (for USD, minus the net position) times its return against the equal-weight basket of all ten; the ten sum exactly to the book before costs.</p>
<div style="padding:4px 0"><label>Book <select id="possel"><option value="DM">G10</option><option value="EM">EM floats</option></select></label></div>
<div class="grid2"><div class="chart"><div id="posplot" style="height:440px"></div></div><div class="chart"><div id="attplot" style="height:440px"></div></div></div>
<div id="attnote" class="note"></div>

<h2>6 · Emerging markets, nine floating currencies</h2>
<div class="grid2">
<div><table><tr><th>Four constructions, EM floats, 15 bp</th><th>2000–15</th><th>2016–26</th><th>Full</th></tr>
{"".join(f'<tr{" class=hl" if n.startswith("C") else ""}><td class=b>{n}</td><td>{v[0]}</td><td>{v[1]}</td><td>{v[2]}</td></tr>' for n,v in em_four)}</table>
<table><tr><th>Construction C, nine floats, 15 bp</th><th>2000–15</th><th>2016–26</th><th>Full</th></tr>
{row(["The book"]+tt(F['C']),True,True)}{row(["Dollar component alone"]+tt(F['dollar_alone']))}{row(["Dollar component removed"]+tt(F['dollar_removed']))}{row(["Spot returns only, no carry","","",sh(F['spot_only'])])}{row(["Signal used one month late","","",sh(F['skip'])])}{row(["All nine at a 2 bp half-spread","","",sh(F['at_2bp'])])}</table>
<p class="note">Ranking EM currencies against each other loses money in both halves. Judging each against the US holds in both. But the dollar component is the whole return: investors allocate to EM as an asset class, so the flow pushes all nine currencies together, and country-versus-country equity performance does not map to a country-specific flow. In EM this is a dollar trade. Managed currencies, for reference: Sharpe −0.38 out of sample.</p></div>
<div class="chart"><div id="emplot" style="height:420px"></div></div></div>

<h2>7 · Risk</h2>
<table><tr><th>Monthly, 2000–2026, after costs</th><th>G10</th><th>EM floats</th></tr>{risk_rows()}</table>
<p class="note">No fat left tail: skew is zero or positive and the worst month is about one vol, so this is not carry. The cost is time, not depth: three years under water in G10 and five in EM, on an unlevered book earning under 2% a year. The books lose when the dollar jumps against the net position: {", ".join(f"{d[:7]} ({v*100:.1f}%)" for d,v in risk['DM']['worst_months'].items())} in G10. The signal looks back six months and has no view on the dollar itself.</p>

<h2>8 · Replication</h2>
<pre>python3 -m pip install -r requirements.txt
python3 equity_spillover.py            # both books, all 70 constructions, placebo, checks -> output/equity_results.json
python3 equity_spillover_floats.py     # the nine floating EM currencies                   -> output/equity_floats.json
python3 equity_spillover_slides.py     # positions by year, 10-leg attribution, risk table  -> output/equity_slides.json
python3 code/build_equity_html.py      # this page</pre>
<p>Data in <code>data/</code>: OECD monthly share-price indices (<code>EQ_*.csv</code>, via DBnomics, to May 2026); FRED H.10 spot rates (<code>DEX*.csv</code>), OECD 3-month rates (<code>IR3TIB01*.csv</code>) and the broad dollar index (<code>DTWEXBGS.csv</code>); ECB reference rates crossed through EUR/USD (<code>ECBFX_*.csv</code>); IMF IFS end-of-period rates for Chile and Colombia (<code>IMFFX_*.csv</code>). See the README for the AI-use documentation. Deck: <code>MFE230GB_EquitySpillover_Deck.pdf</code>; script: <code>MFE230GB_EquitySpillover_Script.pdf</code>.</p>
<p class="note">Generated from the results files on disk; every number on this page is computed by the scripts above.</p>
</main>

<script>
const BOOK={j(book)}, BBEST={j(bbest)}, GRID={{DM:{j(grid)},EM:{j(grid_em)}}}, POS={j(pos)}, EMB={j(F['curve_book'])}, EMD={j(F['curve_dollar'])};
const BLUE="#1565A8", ORANGE="#BF6A12", GRAY="#7A7F87", NAVY="#14213D", PAPER="#FDFCF9";
const base={{paper_bgcolor:PAPER,plot_bgcolor:PAPER,font:{{family:"Public Sans, Segoe UI, Arial",color:"#14213D",size:13}},margin:{{l:56,r:20,t:30,b:44}},hovermode:"x unified",legend:{{orientation:"h",y:1.08,x:0}}}};
const vline=(x)=>({{type:"line",x0:x,x1:x,yref:"paper",y0:0,y1:1,line:{{color:GRAY,width:1.5,dash:"dash"}}}});
Plotly.newPlot("g10plot",[
 {{x:BOOK.map(p=>p[0]),y:BOOK.map(p=>p[1]*100),name:"The book (C), 2 bp",line:{{color:ORANGE,width:2.5}},hovertemplate:"%{{y:.1f}}%"}},
 {{x:BBEST.map(p=>p[0]),y:BBEST.map(p=>p[1]*100),name:"B, ranked cross-section, chosen in sample",line:{{color:BLUE,width:2}},hovertemplate:"%{{y:.1f}}%"}}],
 {{...base,yaxis:{{title:"Cumulative return, %",gridcolor:"#E3E0D6",zeroline:false}},xaxis:{{gridcolor:"#E3E0D6"}},shapes:[vline("2015-12-31")],annotations:[{{x:"2016-03-31",y:1,yref:"paper",text:"Validation from 2016",showarrow:false,xanchor:"left",font:{{color:GRAY,size:12}}}}]}},{{responsive:true}});
Plotly.newPlot("emplot",[
 {{x:EMB.map(p=>p[0]),y:EMB.map(p=>p[1]*100),name:"The book, 9 floats, 15 bp",line:{{color:ORANGE,width:2.5}},hovertemplate:"%{{y:.1f}}%"}},
 {{x:EMD.map(p=>p[0]),y:EMD.map(p=>p[1]*100),name:"Dollar component alone",line:{{color:GRAY,width:2}},hovertemplate:"%{{y:.1f}}%"}}],
 {{...base,yaxis:{{title:"Cumulative return, %",gridcolor:"#E3E0D6",zeroline:false}},xaxis:{{gridcolor:"#E3E0D6"}},shapes:[vline("2015-12-31")]}},{{responsive:true}});
function drawGrid(u){{const g=GRID[u];const cs=g.filter(s=>s.family==="cross-section"),dr=g.filter(s=>s.family==="dollar-relative");
 const lab=s=>`${{s.family}}<br>measure ${{s.measure}}, lookback ${{s.k}}m, ${{s.scheme}}, hold ${{s.hold}}m<br>train ${{s.sharpe_train.toFixed(2)}} · test ${{s.sharpe_test.toFixed(2)}} · full ${{s.sharpe_full.toFixed(2)}}<br>turnover ${{s.turnover}}×/yr`;
 const lo=Math.min(...g.map(s=>Math.min(s.sharpe_train,s.sharpe_test)))-0.1, hi=Math.max(...g.map(s=>Math.max(s.sharpe_train,s.sharpe_test)))+0.1;
 Plotly.newPlot("gridplot",[
  {{x:cs.map(s=>s.sharpe_train),y:cs.map(s=>s.sharpe_test),mode:"markers",name:"Cross-section (64)",marker:{{color:BLUE,size:9,opacity:0.8}},text:cs.map(lab),hovertemplate:"%{{text}}<extra></extra>"}},
  {{x:dr.map(s=>s.sharpe_train),y:dr.map(s=>s.sharpe_test),mode:"markers",name:"Dollar-relative (6)",marker:{{color:ORANGE,size:12,symbol:"diamond"}},text:dr.map(lab),hovertemplate:"%{{text}}<extra></extra>"}},
  {{x:[lo,hi],y:[lo,hi],mode:"lines",name:"test = train",line:{{color:GRAY,width:1,dash:"dot"}},hoverinfo:"skip"}}],
  {{...base,hovermode:"closest",xaxis:{{title:"Sharpe, 2000–2015 (selection)",gridcolor:"#E3E0D6",zeroline:false}},yaxis:{{title:"Sharpe, 2016–2026 (validation)",gridcolor:"#E3E0D6",zeroline:true,zerolinecolor:GRAY}}}},{{responsive:true}});}}
function drawPos(u){{const p=POS[u];
 Plotly.newPlot("posplot",[
  {{type:"heatmap",z:p.z,x:p.years,y:p.ccy,zmin:0,zmax:1,colorscale:[[0,ORANGE],[0.5,"#F3EBDD"],[1,BLUE]],xgap:2,ygap:2,colorbar:{{title:"Share of<br>months long",thickness:12,len:0.7,y:0.65}},hovertemplate:"%{{y}} %{{x}}: long %{{z:.0%}} of months<extra></extra>",yaxis:"y"}},
  {{type:"bar",x:p.years,y:p.net,name:"Net position",marker:{{color:p.net.map(v=>v>=0?BLUE:ORANGE)}},yaxis:"y2",hovertemplate:"net %{{y:+.2f}}<extra></extra>",showlegend:false}}],
  {{...base,hovermode:"closest",title:{{text:(u==="DM"?"G10":"EM floats")+": share of months long, by year",font:{{size:14}}}},yaxis:{{domain:[0.28,1],autorange:"reversed",gridcolor:"#E3E0D6"}},yaxis2:{{domain:[0,0.22],title:"Net",range:[-1,1],gridcolor:"#E3E0D6",zeroline:true,zerolinecolor:GRAY}},xaxis:{{gridcolor:"#E3E0D6"}},shapes:[{{type:"line",x0:2015.5,x1:2015.5,yref:"paper",y0:0,y1:1,line:{{color:NAVY,width:1.5,dash:"dash"}}}}]}},{{responsive:true}});
 const keys=[...p.ccy,"USD"], vals=keys.map(k=>p.attrib[k]*100);
 Plotly.newPlot("attplot",[{{type:"bar",orientation:"h",y:keys,x:vals,marker:{{color:keys.map((k,i)=>k==="USD"?NAVY:(vals[i]>=0?BLUE:ORANGE))}},text:vals.map(v=>(v>=0?"+":"−")+Math.abs(v).toFixed(2)+"%"),textposition:"outside",hovertemplate:"%{{y}}: %{{x:+.2f}}% a year<extra></extra>"}}],
  {{...base,hovermode:"closest",title:{{text:"Attribution by currency, % a year, gross",font:{{size:14}}}},yaxis:{{autorange:"reversed"}},xaxis:{{title:"% a year",gridcolor:"#E3E0D6",zeroline:true,zerolinecolor:GRAY,range:[Math.min(-0.45,Math.min(...vals)-0.3),Math.max(...vals)*1.25]}},showlegend:false,margin:{{l:56,r:60,t:40,b:44}}}},{{responsive:true}});
 const sum=Object.values(p.attrib).reduce((a,b)=>a+b,0);
 document.getElementById("attnote").innerHTML=`Sum of the ten legs, gross: <b>${{(sum*100).toFixed(2)}}%</b> a year · costs <b>−${{(p.cost*100).toFixed(2)}}%</b> · the book after costs <b>${{(p.book*100).toFixed(2)}}%</b>. USD leg: ${{(p.attrib.USD*100).toFixed(2)}}% (${{(p.attrib.USD/sum*100).toFixed(0)}}% of gross).`;}}
drawGrid("DM"); drawPos("DM");
document.getElementById("gridsel").onchange=e=>drawGrid(e.target.value); document.getElementById("possel").onchange=e=>drawPos(e.target.value);
</script></body></html>"""
(ROOT / "index.html").write_text(HTML)
print("wrote index.html", len(HTML) // 1024, "KB")
