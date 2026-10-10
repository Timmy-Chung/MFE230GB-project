"""Backtest of the pre-registered rule (DESIGN.md sections 6-8).

Usage:
  python -I src/run_backtest.py        reported results for the last five years (Oct 2021 - Sep 2026):
                                       main rule, cost grid and the Japan placebo -> output/tables
  python -I src/run_backtest.py full   the pre-registered full sample (2020 - 2026) with every variant
                                       and robustness test -> output/tables/full_sample_2020_2026
Also writes data/processed/panel_{kr,jp}_{report,full}.parquet
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402
from strategy import Market, weekly_panel, build_weights, backtest, perf  # noqa: E402

MODE = sys.argv[1] if len(sys.argv) > 1 else "report"
if MODE == "full":
    T, START = os.path.join(C.TABLES, "full_sample_2020_2026"), C.FIRST_FORMATION
else:
    MODE, T, START = "report", C.TABLES, C.REPORT_START
os.makedirs(T, exist_ok=True)
mk = Market("KR")


def run(panel, label, cost=C.COST_BP, mkt=None, **kw):
    W = build_weights(panel, mk=mkt or mk, **kw)
    res, contrib = backtest(panel, W, cost)
    g, n = perf(res["gross"]), perf(res["net"])
    row = {"test": label, "weeks": n["weeks"], "first_week": res.index.min().date(), "avg_coins": panel.groupby("week").size().loc[res.index].mean(),
           "gross_return": g["ann_return"], "net_return": n["ann_return"], "vol": n["ann_vol"],
           "sharpe_gross": g["sharpe"], "sharpe_net": n["sharpe"], "t_net": n["t_nw"], "max_dd": n["max_dd"],
           "final_wealth": n["final_wealth"], "turnover_wk": res["turnover"].mean(),
           "funding_ann": res["funding"].mean() * 52, "price_ann": res["price"].mean() * 52, "cost_ann": res["cost"].mean() * 52}
    return row, res, contrib


# ------------------------------------------------------------------ main rule
panel = weekly_panel(mk, start=START)
panel.to_parquet(os.path.join(C.PROC, f"panel_kr_{MODE}.parquet"))
main, res, contrib = run(panel, "Main rule (Korea)")
res.to_csv(os.path.join(T, "weekly_main.csv"))
contrib.to_csv(os.path.join(T, "contrib_main.csv"), index=False)

# effect of transaction costs
costs = [run(panel, f"{c} bp", cost=c)[0] for c in (0, 5, 10, 20, 30, 40)]
pd.DataFrame(costs).to_csv(os.path.join(T, "costs.csv"), index=False)

# Japan placebo: the same rule on bitbank's yen market, where capital moves freely
mj = Market("JP")
pj = weekly_panel(mj, start=START)
pj.to_parquet(os.path.join(C.PROC, f"panel_jp_{MODE}.parquet"))
rj, resj, _ = run(pj, "Japan placebo (bitbank)", mkt=mj)
resj.to_csv(os.path.join(T, "weekly_japan.csv"))
pd.DataFrame([main, rj]).to_csv(os.path.join(T, "robustness.csv"), index=False)
print(pd.DataFrame([main, rj] + costs)[["test", "weeks", "first_week", "avg_coins", "gross_return", "net_return", "vol",
                                        "sharpe_gross", "sharpe_net", "t_net", "max_dd", "final_wealth", "turnover_wk",
                                        "funding_ann", "price_ann", "cost_ann"]].round(3).to_string())

if MODE == "full":
    # ---------------------------------------------------------------- pre-specified variants
    rows = [main]
    for label, kw in [("Beta-neutral legs", {"beta_neutral": True}), ("Rank weights", {"scheme": "rank"}),
                      ("Terciles", {"q": 1 / 3})]:
        r, rs, _ = run(panel, label, **kw)
        rows.append(r)
        rs.to_csv(os.path.join(T, f"weekly_{label.split()[0].lower()}.csv"))
    pd.DataFrame(rows).to_csv(os.path.join(T, "perf_variants.csv"), index=False)

    # ---------------------------------------------------------------- full robustness grid
    rob = [dict(main, test="Main (10 bp)")]
    for lo, hi, lab in [("2020-01-01", "2022-12-31", "2020–2022"), ("2023-01-01", "2026-12-31", "2023–2026")]:
        sub = panel[(panel.week >= lo) & (panel.week <= hi)]
        rob.append(run(sub, f"Sub-period {lab}")[0])
    for c in [0, 5, 20, 30, 40]:
        rob.append(run(panel, f"Costs {c} bp", cost=c)[0])
    for lab, kw in [("One-day execution lag", dict(lag=1)), ("No liquidity filter", dict(liq="none")),
                    ("Strict liquidity filter", dict(liq="strict")), ("No blocked-channel filter", dict(blocked=None)),
                    ("Blocked-channel filter 5%", dict(blocked=0.05)), ("Signal: change in premium", dict(signal="change")),
                    ("Signal: premium vs BTC", dict(base="btc"))]:
        rob.append(run(weekly_panel(mk, start=START, **kw), lab)[0])
    rob.append(rj)
    rob.append(run(pj, "Japan placebo, 10 coins minimum", mkt=mj, min_coins=10)[0])
    pd.DataFrame(rob).to_csv(os.path.join(T, "robustness_grid.csv"), index=False)

    # ---------------------------------------------------------------- exploratory, NOT pre-registered
    # Specified after seeing the main result (DESIGN.md deviations log, entry 3) and run once.
    def short_band_weights(panel, thr=0.0025, slots=10):
        W = {}
        for M, g in panel.groupby("week"):
            if len(g) < C.MIN_COINS:
                continue
            s = g.set_index("coin")["signal"]
            sh = s[s > thr].index
            if len(sh) == 0:
                continue
            ws = pd.Series(-1.0 / max(len(sh), slots), index=sh)
            rest = s.index.difference(sh)
            W[M] = pd.concat([pd.Series(-ws.sum() / len(rest), index=rest), ws])
        return W

    resx, _ = backtest(panel, short_band_weights(panel), C.COST_BP)
    resx = resx.reindex([w for w in sorted(set(panel.week)) if w >= resx.index.min()]).fillna(0.0)
    gx, nx = perf(resx["gross"]), perf(resx["net"])
    pd.DataFrame([{"test": "Exploratory: short coins above a 25 bp band, hedged with the universe",
                   "weeks": nx["weeks"], "gross_return": gx["ann_return"], "net_return": nx["ann_return"], "vol": nx["ann_vol"],
                   "sharpe_gross": gx["sharpe"], "sharpe_net": nx["sharpe"], "max_dd": nx["max_dd"],
                   "turnover_wk": resx["turnover"].mean(), "funding_ann": resx["funding"].mean() * 52,
                   "price_ann": resx["price"].mean() * 52, "cost_ann": resx["cost"].mean() * 52}]).to_csv(
        os.path.join(T, "exploratory.csv"), index=False)

    # ---------------------------------------------------------------- randomization (gross, quintiles)
    rng = np.random.default_rng(20261007)
    groups = [panel[panel.week == w] for w in sorted(set(res.index))]
    draws = []
    for _ in range(1000):
        rr = []
        for g in groups:
            k = int(np.floor(len(g) * C.QUANTILE))
            perm = rng.permutation(len(g))
            x = g["ret_long"].values
            rr.append(x[perm[:k]].mean() - x[perm[-k:]].mean())
        rr = np.array(rr)
        draws.append(rr.mean() / rr.std() * np.sqrt(52))
    pd.Series(draws, name="sharpe_gross").to_csv(os.path.join(T, "randomization.csv"), index=False)
    print("full-sample grid written to", T)
