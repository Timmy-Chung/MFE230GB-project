"""Collect every number the interactive page shows into one JSON file.

Reported window: the last five years, October 2021 to September 2026 (DESIGN.md deviations log, entry 5).
Usage: python -I src/export_page_data.py  ->  output/page/page_data.json
Run after run_backtest.py (both modes), run_analysis.py, make_figures.py and slide_numbers.py.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402
from strategy import perf  # noqa: E402

T = C.TABLES
FULL = os.path.join(T, "full_sample_2020_2026")
A = json.load(open(os.path.join(T, "analysis.json")))
FN = json.load(open(os.path.join(T, "figure_numbers.json")))
S = json.load(open(os.path.join(T, "slide_numbers.json")))
macro = pd.read_parquet(os.path.join(C.PROC, "macro.parquet"))
DAY0 = pd.Timestamp("1970-01-01")
D0, D1 = C.REPORT_DAILY_START, C.REPORT_DAILY_END


def days(idx):
    return [int((pd.Timestamp(d) - DAY0).days) for d in idx]


def r(x, n=6):
    if x is None:
        return None
    try:
        if np.isnan(x):
            return None
    except TypeError:
        pass
    return round(float(x), n)


def col(s, n=6):
    return [r(v, n) for v in s]


out = {"meta": {"generated": "2026-10-07", "window_daily": f"{D0} to {D1}",
                "window_weeks": f"{C.REPORT_START} to {C.LAST_FORMATION}"}}

# ---------------------------------------------------------------- premium series (7-day average), the window only
# shown as simple premia, exp(log premium) - 1; the analysis itself uses logs
k = np.expm1(macro[["kappa_kr", "kappa_jp"]]).rolling(7, min_periods=5).mean().loc[D0:D1]
out["kappa"] = {"days": days(k.index), "kr": col(k["kappa_kr"], 5), "jp": col(k["kappa_jp"], 5)}

# H1 statistics on the daily simple premium (same series as the slides)
kd = np.expm1(macro[["kappa_kr", "kappa_jp"]].loc[D0:D1]).dropna()
hl = {row["market"].split()[0]: row["half_life_days"] for row in A["h1"]}
out["h1_simple"] = []
for lab, c, key in [("Korea (Upbit, won)", "kappa_kr", "Korea"), ("Japan (bitbank, yen)", "kappa_jp", "Japan")]:
    x = kd[c]
    out["h1_simple"].append({"market": lab, "mean": r(x.mean()), "sd": r(x.std()), "p95": r(x.quantile(.95)),
                             "max": r(x.max()), "max_date": str(x.idxmax().date()), "min": r(x.min()), "min_date": str(x.idxmin().date()),
                             "share_above_2pct": r((x > 0.02).mean()), "share_below_0": r((x < 0).mean()),
                             "half_life_days": r(hl[key], 2)})

# shadow exchange rate: the won per dollar that bitcoin implies on three days
out["shadow"] = []
for key, label in [("board_peak", "Peak, 19 Mar 2024"), ("board_last", "Latest, 30 Sep 2026")]:
    b = S[key]
    out["shadow"].append({"date": b["date"], "label": label, "upbit_krw": r(b["upbit_krw"], 0), "binance_usd": r(b["binance_usdt"], 2),
                          "implied": r(b["implied_krw_per_usd"], 2), "official": r(b["market_krw_per_usd"], 2), "premium": r(b["premium_simple"], 5)})
up = pd.read_parquet(os.path.join(C.PROC, "upbit_close.parquet"))
world = pd.read_parquet(os.path.join(C.PROC, "world_close.parquet"))
dmin = pd.Timestamp(out["h1_simple"][0]["min_date"])
u, w, fx = float(up.loc[dmin, "BTC"]), float(world.loc[dmin, "BTC"]), float(macro.loc[dmin, "krw_per_usd"])
out["shadow"].insert(1, {"date": str(dmin.date()), "label": f"Discount, {dmin.day} {dmin.strftime('%b %Y')}", "upbit_krw": r(u, 0),
                         "binance_usd": r(w, 2), "implied": r(u / w, 2), "official": r(fx, 2), "premium": r(u / w / fx - 1, 5)})
us = macro["usdt_premium_kr"].rolling(7, min_periods=5).mean().loc[A["usdt_premium_start"]:D1]
out["usdt_premium"] = {"days": days(us.index), "v": col(np.expm1(us), 5)}

# ---------------------------------------------------------------- weekly returns: Korea and the Japan placebo
out["weekly"] = {}
for key, label, f in [("kr", "Korea (Upbit)", "weekly_main.csv"), ("jp", "Japan placebo (bitbank)", "weekly_japan.csv")]:
    wk = pd.read_csv(os.path.join(T, f), parse_dates=["week"], index_col="week")
    out["weekly"][key] = {"label": label, "days": days(wk.index), "gross": col(wk["gross"]), "turnover": col(wk["turnover"], 4),
                          "price": col(wk["price"]), "funding": col(wk["funding"])}

# ---------------------------------------------------------------- headline tables
keep = ["test", "weeks", "first_week", "avg_coins", "gross_return", "net_return", "vol", "sharpe_gross", "sharpe_net", "t_net",
        "max_dd", "final_wealth", "turnover_wk", "funding_ann", "price_ann", "cost_ann"]
rb = pd.read_csv(os.path.join(T, "robustness.csv"))
out["robustness"] = [{k2: (r(v) if not isinstance(v, str) else v) for k2, v in row.items() if k2 in keep} for row in rb.to_dict("records")]
# Korea over exactly the Japan placebo's weeks, for a like-for-like comparison
wkr = pd.read_csv(os.path.join(T, "weekly_main.csv"), parse_dates=["week"], index_col="week")
wjp = pd.read_csv(os.path.join(T, "weekly_japan.csv"), parse_dates=["week"], index_col="week")
same = wkr.loc[wkr.index.isin(wjp.index)]
g, n = perf(same["gross"]), perf(same["net"])
PK = pd.read_parquet(os.path.join(C.PROC, "panel_kr_report.parquet"))
out["robustness"].insert(1, {"test": "Korea, the placebo's weeks", "weeks": int(n["weeks"]), "first_week": str(same.index.min().date()),
                             "avg_coins": r(PK[PK["week"].isin(same.index)].groupby("week").size().mean(), 1),
                             "gross_return": r(g["ann_return"]), "net_return": r(n["ann_return"]), "vol": r(n["ann_vol"]),
                             "sharpe_gross": r(g["sharpe"]), "sharpe_net": r(n["sharpe"]), "t_net": r(n["t_nw"]), "max_dd": r(n["max_dd"]),
                             "final_wealth": r(n["final_wealth"]), "turnover_wk": r(same["turnover"].mean()),
                             "funding_ann": r(same["funding"].mean() * 52), "price_ann": r(same["price"].mean() * 52),
                             "cost_ann": r(same["cost"].mean() * 52)})
cs = pd.read_csv(os.path.join(T, "costs.csv"))
out["costs"] = [{"bp": float(t.replace(" bp", "")), "net_return": r(nr), "sharpe_net": r(sn)}
                for t, nr, sn in zip(cs["test"], cs["net_return"], cs["sharpe_net"])]
out["breakeven_bp"] = r(FN["breakeven_bp"], 2)

for key in ["h1", "quintiles", "fm", "fm_horizons", "buckets", "h3", "exposures", "episodes", "liquidity", "concentration",
            "side_pnl_ann", "worst_weeks", "pnl_by_year", "tails", "worst_coin", "funding_by_leg", "live_week",
            "signal_iqr_bp", "share_abs_signal_below_25bp", "usdt_premium_mean", "usdt_premium_start"]:
    out[key] = A[key]
out["overlay"] = {"stats": {k2: {kk: r(vv) for kk, vv in v.items()} for k2, v in A["overlay"].items() if isinstance(v, dict)},
                  "froth_weeks": A["overlay"]["froth_weeks"], "weeks": A["overlay"]["weeks"]}
out["froth_quintiles"] = FN["froth_quintiles"]
out["regime"] = [{"regime": x["kappa_bar"], "mean": r(x["mean"]), "size": int(x["size"])} for x in FN["regime"]]

chk = pd.read_csv(os.path.join(T, "coin_checks_kr.csv"))
P = pd.read_parquet(os.path.join(C.PROC, "panel_kr_report.parquet"))
out["universe"] = {"coins_checked": int(len(chk)), "coins_pass": int(chk["pass"].sum()),
                   "coins_traded": int(A["concentration"]["n_coins_traded"]), "avg_coins": r(P.groupby("week").size().mean(), 1),
                   "first_trade_week": str(wkr.index.min().date()), "last_week": str(wkr.index.max().date())}

# ---------------------------------------------------------------- the pre-registered full sample, for the disclosure only
fr = pd.read_csv(os.path.join(FULL, "robustness.csv")).set_index("test").loc["Main rule (Korea)"]
fw = pd.read_csv(os.path.join(FULL, "weekly_main.csv"), parse_dates=["week"], index_col="week")
worst = fw["net"].idxmin()
out["full_sample"] = {"weeks": int(fr["weeks"]), "first_week": str(fr["first_week"]), "net_return": r(fr["net_return"]),
                      "sharpe_net": r(fr["sharpe_net"]), "sharpe_gross": r(fr["sharpe_gross"]), "max_dd": r(fr["max_dd"]),
                      "worst_week": str(worst.date()), "worst_week_net": r(fw.loc[worst, "net"]),
                      "sharpe_net_ex_worst": r(perf(fw["net"].drop(worst))["sharpe"])}


def clean(o):
    if isinstance(o, dict):
        return {str(k2): clean(v) for k2, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if (o != o or o in (float("inf"), float("-inf"))) else round(float(o), 6)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


json.dump(clean(out), open(os.path.join(C.PAGE, "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("page_data.json", os.path.getsize(os.path.join(C.PAGE, "page_data.json")) // 1024, "KB")
print(json.dumps(out["shadow"], indent=0))
print(out["robustness"][1])
print(out["universe"], out["full_sample"])
