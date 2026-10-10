"""Slide figures (PNG on the slides' dark card colour, "exchange terminal" theme).

Usage: python -I src/make_figures.py [fonts_dir]
Reported window: the last five years (October 2021 to September 2026). With a fonts directory
holding JetBrains Mono TTFs the charts use it, as on the slides; otherwise the default font.
Colours were checked with a colour-blind-safety validator against the slide background (#0a0e17); figures
are drawn on the slides' card colour (#101725).
"""
import json
import logging
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402
from strategy import perf  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # the Bold TTF registers as weight 558
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    for f in os.listdir(sys.argv[1]):
        if f.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(sys.argv[1], f))
    if any("JetBrains" in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = "JetBrains Mono"

INK, INK2, MUTED, GRID, AXIS = "#e6ebf3", "#b4c0d3", "#8391a7", "#1f2a3d", "#334155"
CARD = "#101725"                  # the slides' chart-card colour, so a figure sits flush in its card
KR, WORLD, VIO, SLATE, WHITE = "#df7410", "#1d9bd6", "#8b5cf6", "#5b6b85", "#e6ebf3"
plt.rcParams.update({
    "font.size": 17, "text.color": INK, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 1.0, "axes.axisbelow": True, "xtick.major.size": 0, "ytick.major.size": 0, "xtick.minor.size": 0, "ytick.minor.size": 0,
    "figure.facecolor": CARD, "axes.facecolor": CARD, "savefig.facecolor": CARD, "figure.dpi": 100, "legend.frameon": False, "axes.unicode_minus": True,
})
T, F = C.TABLES, C.FIGS
D = pd.Timedelta(days=1)


def sg(v, d=0, plus=True):
    t = f"{abs(v):.{d}f}%"
    if round(abs(v), d) == 0:
        return f"{0:.{d}f}%"
    return ("−" if v < 0 else ("+" if plus else "")) + t


pct = mt.FuncFormatter(lambda v, _: sg(v, 0, plus=False))


def fig(wpx, hpx):
    return plt.subplots(figsize=(wpx / 100, hpx / 100))


def save(f, name):
    f.savefig(os.path.join(F, name), dpi=200, bbox_inches="tight", pad_inches=0.12)
    plt.close(f)


A = json.load(open(os.path.join(T, "analysis.json")))
macro = pd.read_parquet(os.path.join(C.PROC, "macro.parquet"))
extra = {}

# ---------------------------------------------------------------- 1. Korea vs Japan premium, daily
k = np.expm1(macro[["kappa_kr", "kappa_jp"]].loc[C.REPORT_DAILY_START:C.REPORT_DAILY_END]) * 100
f, ax = fig(1500, 600)
ax.axhline(0, color=AXIS, lw=1.2)
ax.plot(k.index, k["kappa_jp"], color=WORLD, lw=1.6)
ax.plot(k.index, k["kappa_kr"], color=KR, lw=1.6)
d = k["kappa_kr"].idxmax()
v = k.loc[d, "kappa_kr"]
ax.annotate(f"{sg(v, 1)} · {d.day} {d.strftime('%b %Y')}", (d, v), xytext=(d + pd.Timedelta(days=140), v + 0.6), color=INK, fontsize=17,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
ax.text(k.index[-1] + pd.Timedelta(days=12), k["kappa_kr"].iloc[-30:].mean() + 2.2, "KOREA", color=KR, fontsize=17, fontweight="bold")
ax.text(k.index[-1] + pd.Timedelta(days=12), -2.6, "JAPAN", color=WORLD, fontsize=17, fontweight="bold")
ax.yaxis.set_major_formatter(pct)
ax.set_ylim(-4.5, 13.5)
ax.set_xlim(k.index[0], k.index[-1] + pd.Timedelta(days=130))
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2022, 2027)], [str(y) for y in range(2022, 2027)])
ax.set_ylabel("Premium over world price, daily")
save(f, "kappa_kr_jp.png")

# ---------------------------------------------------------------- 2. quintile returns
q = pd.DataFrame(A["quintiles"])
vals = q["ret_rel_ann"].values * 100
f, ax = fig(900, 560)
bars = ax.bar(range(5), vals, color=[KR, SLATE, SLATE, SLATE, KR], width=0.62)
ax.axhline(0, color=AXIS, lw=1.2)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + (1.3 if v >= 0 else -1.3), sg(v, 0), ha="center", va="bottom" if v >= 0 else "top",
            fontsize=18, fontweight="bold", color=INK)
ax.set_xticks(range(5), ["Q1\nlong leg", "Q2", "Q3", "Q4", "Q5\nshort leg"], color=INK2)
ax.yaxis.set_major_formatter(pct)
ax.set_ylim(vals.min() - 9, vals.max() + 9)
ax.set_ylabel("Return vs universe, per year")
save(f, "quintiles.png")

# ---------------------------------------------------------------- 3. channel: which price moves
qq = q.set_index(q.columns[0])
kv = [qq.iloc[4]["dlocal_rel_pct"], qq.iloc[0]["dlocal_rel_pct"]]
wv = [qq.iloc[4]["dworld_rel_pct"], qq.iloc[0]["dworld_rel_pct"]]
f, ax = fig(900, 520)
x = np.arange(2)
b1 = ax.bar(x - 0.17, kv, 0.32, color=KR, label="Korean price (Upbit)")
b2 = ax.bar(x + 0.17, wv, 0.32, color=WORLD, label="World price (Binance)")
ax.axhline(0, color=AXIS, lw=1.2)
for bs, vs in [(b1, kv), (b2, wv)]:
    for b, v in zip(bs, vs):
        ax.text(b.get_x() + b.get_width() / 2, v - 0.04 if v < 0 else v + 0.04, sg(v, 2), ha="center",
                va="top" if v < 0 else "bottom", fontsize=17, color=INK, fontweight="bold")
ax.set_xticks(x, ["Top quintile\n(short leg)", "Bottom quintile\n(long leg)"], color=INK2)
ax.yaxis.set_major_locator(mt.MultipleLocator(0.2))
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: sg(v, 1, plus=False)))
ax.set_ylim(min(kv + wv) - 0.3, 0.45)
ax.legend(loc="lower right", fontsize=16, labelcolor=INK2)
ax.set_ylabel("Next-week price change vs universe")
save(f, "channel.png")

# ---------------------------------------------------------------- 4. wealth, Korea
wk = pd.read_csv(os.path.join(T, "weekly_main.csv"), parse_dates=["week"], index_col="week")
end = wk.index + pd.Timedelta(days=7)
paths = [((1 + wk["price"]).cumprod(), WORLD, "Price only"), ((1 + wk["gross"]).cumprod(), VIO, "After funding"),
         ((1 + wk["net"]).cumprod(), KR, "Net of 10 bp")]
f, ax = fig(1250, 600)
ax.axhline(1, color=AXIS, lw=1.2)
for s, c, nm in paths:
    ax.plot(end, s, color=c, lw=2.6 if c == KR else 2)
    ax.text(end[-1] + pd.Timedelta(days=25), s.iloc[-1], f"${s.iloc[-1]:.2f} {nm}", color=c, va="center", fontsize=16, fontweight="bold")
ax.set_yscale("log")
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v:g}"))
ax.yaxis.set_minor_formatter(mt.NullFormatter())
ax.set_yticks([1, 1.5, 2, 3, 4, 6])
ax.set_ylim(0.9, 7.2)
ax.set_xlim(end[0] - pd.Timedelta(days=20), end[-1] + pd.Timedelta(days=560))
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2022, 2027)], [str(y) for y in range(2022, 2027)])
ax.set_ylabel("Growth of $1 (log scale)")
save(f, "wealth.png")
extra["wealth_final"] = {nm: float(s.iloc[-1]) for s, _, nm in paths}

# ---------------------------------------------------------------- 5. where the money goes
rb = pd.read_csv(os.path.join(T, "robustness.csv")).set_index("test")
m = rb.loc["Main rule (Korea)"]
items = [("Price", m["price_ann"], WORLD), ("Funding", m["funding_ann"], VIO), ("Costs", -m["cost_ann"], SLATE), ("Net", m["net_return"], KR)]
f, ax = fig(820, 560)
run_ = 0
for i, (nm, v, c) in enumerate(items):
    if nm == "Net":
        ax.bar(i, v * 100, color=c, width=0.6)
        top, bot = v * 100, 0
    else:
        ax.bar(i, v * 100, bottom=run_ * 100, color=c, width=0.6)
        top, bot = (run_ + v) * 100, run_ * 100
        ax.plot([i + 0.3, i + 0.7], [(run_ + v) * 100] * 2, color=MUTED, lw=1)
        run_ += v
    ax.text(i, max(top, bot) + 1.2, sg(v * 100, 1), ha="center", va="bottom", fontsize=19, fontweight="bold", color=INK)
ax.axhline(0, color=AXIS, lw=1.2)
ax.set_xticks(range(4), [x[0] for x in items], color=INK2)
ax.yaxis.set_major_formatter(pct)
ax.set_ylim(0, 50)
ax.set_ylabel("Per year, Oct 2021 – Sep 2026")
save(f, "waterfall.png")

# ---------------------------------------------------------------- 6. by year: where each year's P&L came from
yr = pd.DataFrame(A["pnl_by_year"]).set_index("year")
f, ax = fig(1150, 600)
xs = np.arange(len(yr))
bw = 0.56
pos, neg = np.zeros(len(yr)), np.zeros(len(yr))
for col, c, nm in [("price", WORLD, "Price"), ("funding", VIO, "Funding"), ("cost", SLATE, "Costs")]:
    v = yr[col].values * 100
    ax.bar(xs, v, bw, bottom=np.where(v >= 0, pos, neg), color=c, label=nm)
    pos, neg = pos + np.where(v >= 0, v, 0), neg + np.where(v < 0, v, 0)
net = yr["net"].values * 100
ax.hlines(net, xs - bw / 2 - 0.07, xs + bw / 2 + 0.07, color=KR, lw=5, label="Net", zorder=4)
for x_, v_ in zip(xs, net):
    ax.text(x_, 80, "Net " + sg(v_, 0), ha="center", va="center", fontsize=17, fontweight="bold", color=KR)
ax.axhline(0, color=AXIS, lw=1.2)
ax.set_xticks(xs, [f"{y}{'*' if n < 50 else ''}" for y, n in zip(yr.index, yr["weeks"])], color=INK2)
ax.yaxis.set_major_formatter(pct)
ax.set_yticks([-40, -20, 0, 20, 40, 60])
ax.set_ylim(-48, 90)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, fontsize=16, labelcolor=INK2)
ax.set_ylabel("Sum of weekly returns")
save(f, "by_year.png")

# ---------------------------------------------------------------- 7. Japan placebo vs Korea, same weeks
jp = pd.read_csv(os.path.join(T, "weekly_japan.csv"), parse_dates=["week"], index_col="week")
kr_same = wk.loc[wk.index.isin(jp.index), "net"]
ends = jp.index + pd.Timedelta(days=7)
f, ax = fig(1100, 560)
ax.axhline(1, color=AXIS, lw=1.2)
for s, c, nm in [((1 + kr_same).cumprod(), KR, "Korea"), ((1 + jp["net"]).cumprod(), WORLD, "Japan")]:
    s = s.reindex(jp.index)
    ax.plot(ends, s, color=c, lw=2.6)
    ax.text(ends[-1] + pd.Timedelta(days=18), s.iloc[-1], f"${s.iloc[-1]:.2f} {nm}", color=c, va="center", fontsize=17, fontweight="bold")
ax.set_xlim(ends[0] - pd.Timedelta(days=15), ends[-1] + pd.Timedelta(days=260))
ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2024, 2027)], [str(y) for y in range(2024, 2027)])
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v:.2f}"))
ax.set_ylabel("Growth of $1, net of 10 bp")
save(f, "placebo.png")
pk, pj = perf(kr_same), perf(jp["net"])
extra["placebo_same_weeks"] = {"weeks": int(len(jp)), "first_week": str(jp.index.min().date()),
                               "korea": {"sharpe": pk["sharpe"], "ann_return": pk["ann_return"], "final": pk["final_wealth"]},
                               "japan": {"sharpe": pj["sharpe"], "ann_return": pj["ann_return"], "final": pj["final_wealth"]}}

# ---------------------------------------------------------------- 8. cost sensitivity
cs = pd.read_csv(os.path.join(T, "costs.csv"))
cs["bp"] = cs["test"].str.replace(" bp", "").astype(float)
be = float(np.interp(0, cs["sharpe_net"].values[::-1], cs["bp"].values[::-1]))
f, ax = fig(860, 500)
ax.axhline(0, color=AXIS, lw=1.2)
ax.axvline(be, color=MUTED, lw=1.2, ls=(0, (4, 4)))
ax.plot(cs["bp"], cs["sharpe_net"], color=KR, lw=2.6, marker="o", markersize=9, markeredgecolor=CARD, markeredgewidth=1.5)
for _, r in cs.iterrows():
    if r["bp"] == 0:
        ax.text(r["bp"] + 1.2, r["sharpe_net"] + 0.06, f"{r['sharpe_net']:+.2f}".replace("-", "−"),
                ha="left", va="bottom", fontsize=16, fontweight="bold", color=INK)
    if r["bp"] == 10:
        ax.text(r["bp"] - 0.6, r["sharpe_net"] - 0.12, f"{r['sharpe_net']:+.2f}".replace("-", "−") + " at 10 bp",
                ha="right", va="top", fontsize=16, fontweight="bold", color=INK)
ax.text(be + 1.2, 0.62, f"break-even\n≈ {be:.0f} bp", ha="left", va="bottom", fontsize=16, color=INK2)
ax.set_xlabel("Cost per unit traded (bp)", color=INK2)
ax.set_ylabel("Net Sharpe ratio")
ax.set_ylim(-1.2, 1.35)
ax.set_xticks([0, 5, 10, 20, 30, 40])
save(f, "costs.png")
extra["breakeven_bp"] = be

# ---------------------------------------------------------------- 9. froth (H3), backup
ov = pd.read_csv(os.path.join(T, "overlay_weekly.csv"), parse_dates=["week"], index_col="week")
btc = pd.read_parquet(os.path.join(C.PROC, "world_close.parquet"))["BTC"]
btc = btc.reindex(pd.date_range(btc.index.min(), btc.index.max() + pd.Timedelta(days=60)))
fw = pd.Series({M: btc.loc[M + 27 * D] / btc.loc[M - D] - 1 for M in ov.index}).dropna()
kb = ov["kappa_bar"].reindex(fw.index)
grp = pd.qcut(kb.rank(method="first"), 5, labels=False)
gm, gk = fw.groupby(grp).mean() * 100, kb.groupby(grp).mean() * 100
f, ax = fig(860, 540)
bars = ax.bar(range(5), gm.values, color=SLATE, width=0.6)
ax.axhline(0, color=AXIS, lw=1.2)
for b, v in zip(bars, gm.values):
    ax.text(b.get_x() + b.get_width() / 2, v + (0.35 if v >= 0 else -0.35), sg(v, 1), ha="center", va="bottom" if v >= 0 else "top",
            fontsize=18, fontweight="bold", color=INK)
ax.set_xticks(range(5), [sg(x, 1, plus=False) for x in gk.values], color=INK2)
ax.set_xlabel("Korea's BTC premium at formation (quintile mean)", color=INK2)
ax.set_ylabel("BTC return, next 4 weeks")
ax.yaxis.set_major_formatter(pct)
ax.set_ylim(min(gm.min() - 2, -1), gm.max() + 2.5)
save(f, "froth.png")
extra["froth_quintiles"] = {"kappa_pct": gk.round(2).tolist(), "btc_4w_pct": gm.round(2).tolist()}

# ---------------------------------------------------------------- 10. regime, backup
kb2 = ov["kappa_bar"].reindex(wk.index)
reg = pd.cut(kb2, [-1, 0, 0.02, 0.05, 1], labels=["Discount", "0–2%", "2–5%", "Above 5%"])
rg = wk.groupby(reg, observed=True)["net"].agg(["mean", "size"])
f, ax = fig(860, 540)
vv = rg["mean"].values * 100
bars = ax.bar(range(len(rg)), vv, color=[KR if x == vv.max() else SLATE for x in vv], width=0.6)
ax.axhline(0, color=AXIS, lw=1.2)
for b, val in zip(bars, vv):
    up = val >= 0 or abs(val) < 0.1          # a sliver below zero is labelled above the axis
    ax.text(b.get_x() + b.get_width() / 2, max(val, 0) + 0.05 if up else val - 0.05, sg(val, 2), ha="center",
            va="bottom" if up else "top", fontsize=18, fontweight="bold", color=INK)
ax.set_xticks(range(len(rg)), [f"{r}\n{n} weeks" for r, n in zip(rg.index, rg["size"])], color=INK2)
ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda x, _: sg(x, 1, plus=False)))
ax.set_ylabel("Average net return a week")
ax.set_xlabel("Korea's BTC premium at formation", color=INK2)
save(f, "regime.png")
extra["regime"] = rg.reset_index().rename(columns={"net": "regime"}).to_dict("records")

json.dump(extra, open(os.path.join(T, "figure_numbers.json"), "w"), default=str, indent=1)
print("figures saved to", F)
print(json.dumps(extra, default=str, indent=1))
