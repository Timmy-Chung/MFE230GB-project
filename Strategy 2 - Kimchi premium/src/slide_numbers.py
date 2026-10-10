"""Every number quoted on the slides, recomputed from the output tables (reported window only).

Usage: python -I src/slide_numbers.py      -> prints a fact sheet, writes output/tables/slide_numbers.json
Run after run_backtest.py, run_analysis.py and make_figures.py.
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
A = json.load(open(os.path.join(T, "analysis.json")))
FN = json.load(open(os.path.join(T, "figure_numbers.json")))
rob = pd.read_csv(os.path.join(T, "robustness.csv")).set_index("test")
costs = pd.read_csv(os.path.join(T, "costs.csv")).set_index("test")
wk = pd.read_csv(os.path.join(T, "weekly_main.csv"), parse_dates=["week"], index_col="week")
jp = pd.read_csv(os.path.join(T, "weekly_japan.csv"), parse_dates=["week"], index_col="week")
macro = pd.read_parquet(os.path.join(C.PROC, "macro.parquet"))
up = pd.read_parquet(os.path.join(C.PROC, "upbit_close.parquet"))
wc = pd.read_parquet(os.path.join(C.PROC, "world_close.parquet"))
S = {}

# ------------------------------------------------------------------ H1: segmentation (daily, simple premium)
k = np.expm1(macro[["kappa_kr", "kappa_jp"]].loc[C.REPORT_DAILY_START:C.REPORT_DAILY_END]).dropna()
h1 = {r["market"].split()[0]: r for r in A["h1"]}
S["h1"] = {
    "days": int(len(k)),
    "korea_mean": float(k["kappa_kr"].mean()), "japan_mean": float(k["kappa_jp"].mean()),
    "korea_share_above_2pct": float((k["kappa_kr"] > 0.02).mean()), "japan_share_above_2pct": float((k["kappa_jp"] > 0.02).mean()),
    "korea_share_above_5pct": float((k["kappa_kr"] > 0.05).mean()),
    "korea_share_below_0": float((k["kappa_kr"] < 0).mean()),
    "korea_max": float(k["kappa_kr"].max()), "korea_max_date": str(k["kappa_kr"].idxmax().date()),
    "korea_min": float(k["kappa_kr"].min()), "korea_min_date": str(k["kappa_kr"].idxmin().date()),
    "japan_max": float(k["kappa_jp"].max()),
    "korea_half_life_days": h1["Korea"]["half_life_days"], "japan_half_life_days": h1["Japan"]["half_life_days"],
}


def board(day):
    """One coin, two prices on a given day: Upbit BTC in won vs Binance BTC in USDT."""
    d = pd.Timestamp(day)
    krw, usd, fx = float(up.loc[d, "BTC"]), float(wc.loc[d, "BTC"]), float(macro.loc[d, "krw_per_usd"])
    return {"date": day, "upbit_krw": krw, "binance_usdt": usd, "implied_krw_per_usd": krw / usd, "market_krw_per_usd": fx,
            "premium_simple": krw / usd / fx - 1, "kappa_table": float(np.expm1(macro.loc[d, "kappa_kr"]))}


S["board_peak"] = board(S["h1"]["korea_max_date"])
S["board_last"] = board(C.REPORT_DAILY_END)

# ------------------------------------------------------------------ the rule and one live week
m = rob.loc["Main rule (Korea)"]
lw = A["live_week"]
rows = pd.DataFrame(lw["rows"])
W = pd.Timestamp(lw["week"])
S["universe"] = {"avg_coins": float(m["avg_coins"]), "weeks": int(m["weeks"]), "first_week": str(m["first_week"]),
                 "coins_traded": A["concentration"]["n_coins_traded"]}
S["live_week"] = {"week": lw["week"], "n_coins": lw["n_coins"], "k": lw["k"], "kappa_bar": lw["kappa_bar"], "krw_per_usd": lw["krw_per_usd"],
                  "book_gross": float(wk.loc[W, "gross"]), "book_net": float(wk.loc[W, "net"]),
                  "long_leg": float(wk.loc[W, "long_ret"]), "short_leg": float(wk.loc[W, "short_ret"])}
ex = pd.concat([rows[rows.side == "long"].nsmallest(4, "signal"), rows[rows.side == "short"].nlargest(4, "signal").iloc[::-1]])
ex = ex.assign(position_pnl=np.where(ex.side == "long", ex.ret_long, -ex.ret_long), fund_ann=ex.fund7 * 52)  # trailing 7-day funding, x52
S["live_rows"] = ex[["coin", "side", "signal", "premium", "fund7", "fund_ann", "ret_price", "funding", "ret_long", "position_pnl"]].to_dict("records")

# ------------------------------------------------------------------ signal tests (H2, H4)
fm = {r["var"]: r for r in A["fm"]["signal"]}
fmf = {r["var"]: r for r in A["fm"]["full"]}
q = pd.DataFrame(A["quintiles"]).set_index("quintile")
S["fm"] = {"coef_pct": fm["sig_pct"]["coef"], "t": fm["sig_pct"]["t_nw"], "weeks": fm["sig_pct"]["weeks"],
           "coef_controls": fmf["sig_pct"]["coef"], "t_controls": fmf["sig_pct"]["t_nw"],
           "horizons": A["fm_horizons"]}
S["quintiles"] = q[["signal_bp", "ret_rel_ann", "ret_long_ann", "funding_paid_ann", "dpi_bp", "t_dpi", "dlocal_rel_pct", "t_dlocal",
                    "dworld_rel_pct", "t_dworld", "t_rel"]].to_dict("index")
S["signal_dispersion"] = {"share_abs_below_25bp": A["share_abs_signal_below_25bp"], "iqr_bp": A["signal_iqr_bp"]}

# ------------------------------------------------------------------ results
n = perf(wk["net"])
wealth = (1 + wk["net"]).cumprod()
dd = wealth / wealth.cummax() - 1
trough = dd.idxmin()
peak = wealth.loc[:trough].idxmax()
S["results"] = {
    "weeks": int(len(wk)), "first_week": str(wk.index.min().date()), "last_week": str(wk.index.max().date()),
    "price_ann": float(m["price_ann"]), "funding_ann": float(m["funding_ann"]), "cost_ann": float(m["cost_ann"]),
    "gross_ann": float(m["gross_return"]), "net_ann": float(m["net_return"]), "vol": float(m["vol"]),
    "sharpe_gross": float(m["sharpe_gross"]), "sharpe_net": float(m["sharpe_net"]), "t_net": float(m["t_net"]),
    "max_dd": float(m["max_dd"]), "dd_peak_week_end": str((peak + pd.Timedelta(days=7)).date()),
    "dd_trough_week_end": str((trough + pd.Timedelta(days=7)).date()),
    "turnover_wk": float(m["turnover_wk"]), "final_wealth_net": float(m["final_wealth"]), "cagr_net": float(n["cagr"]),
    "hit_rate": float(n["hit_rate"]), "skew": float(n["skew"]), "best_week": float(n["best_week"]), "worst_week": float(n["worst_week"]),
    "wealth_paths": FN["wealth_final"], "breakeven_bp": FN["breakeven_bp"],
    "costs_grid": costs[["net_return", "sharpe_net"]].to_dict("index"),
    "funding_by_leg": A["funding_by_leg"], "side_pnl_ann": A["side_pnl_ann"],
    "share_of_price_kept": float(m["net_return"] / m["price_ann"]),
}

# ------------------------------------------------------------------ risk
S["risk"] = {"by_year": A["pnl_by_year"], "worst_weeks": A["worst_weeks"][:5], "worst_coin": A["worst_coin"], "tails": A["tails"],
             "exposures": A["exposures"], "episodes": A["episodes"], "regime": FN["regime"], "liquidity": A["liquidity"],
             "concentration": A["concentration"]}

# ------------------------------------------------------------------ the one robustness test: Japan placebo
j = rob.loc["Japan placebo (bitbank)"]
S["placebo"] = {"weeks": int(j["weeks"]), "first_week": str(j["first_week"]), "avg_coins": float(j["avg_coins"]),
                "net_ann": float(j["net_return"]), "gross_ann": float(j["gross_return"]), "sharpe_net": float(j["sharpe_net"]),
                "sharpe_gross": float(j["sharpe_gross"]), "vol": float(j["vol"]), "max_dd": float(j["max_dd"]),
                "turnover_wk": float(j["turnover_wk"]), "funding_ann": float(j["funding_ann"]), "price_ann": float(j["price_ann"]),
                "same_weeks": FN["placebo_same_weeks"]}

# ------------------------------------------------------------------ H3 (backup)
S["h3"] = {"regression": A["h3"], "overlay": {kk: A["overlay"][kk] for kk in ("froth_weeks", "weeks", "btc_ret_in_froth_weeks_ann",
                                                                               "btc_ret_other_weeks_ann", "t_diff")},
           "btc_sharpe": A["overlay"]["btc"]["sharpe"], "brake_sharpe": A["overlay"]["overlay"]["sharpe"],
           "froth_quintiles": FN["froth_quintiles"]}

# ------------------------------------------------------------------ the pre-registered full sample (backup disclosure)
fs = os.path.join(T, "full_sample_2020_2026", "robustness.csv")
if os.path.exists(fs):
    f = pd.read_csv(fs).set_index("test").loc["Main rule (Korea)"]
    S["full_sample"] = {"weeks": int(f["weeks"]), "first_week": str(f["first_week"]), "net_ann": float(f["net_return"]),
                        "sharpe_net": float(f["sharpe_net"]), "sharpe_gross": float(f["sharpe_gross"]), "max_dd": float(f["max_dd"])}

json.dump(S, open(os.path.join(T, "slide_numbers.json"), "w"), indent=1, default=str)


def pc(x, d=1):
    return f"{x * 100:+.{d}f}%".replace("-", "−")


print("H1  Korea mean", pc(S["h1"]["korea_mean"], 2), "Japan mean", pc(S["h1"]["japan_mean"], 2),
      "| >2%:", f'{S["h1"]["korea_share_above_2pct"]:.0%} vs {S["h1"]["japan_share_above_2pct"]:.1%}',
      "| half-life", f'{S["h1"]["korea_half_life_days"]:.1f} vs {S["h1"]["japan_half_life_days"]:.1f} days',
      "| max", pc(S["h1"]["korea_max"]), S["h1"]["korea_max_date"])
for b in ("board_peak", "board_last"):
    x = S[b]
    print(b, x["date"], f'Upbit ₩{x["upbit_krw"]:,.0f}  Binance ${x["binance_usdt"]:,.2f}  implied ₩{x["implied_krw_per_usd"]:,.0f}/$  '
          f'market ₩{x["market_krw_per_usd"]:,.2f}/$  premium {pc(x["premium_simple"])} (table {pc(x["kappa_table"])})')
print("universe", S["universe"])
print("live week", {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in S["live_week"].items()})
print(pd.DataFrame(S["live_rows"]).round(4).to_string())
print("FM", {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in S["fm"].items() if kk != "horizons"})
print(pd.DataFrame(S["fm"]["horizons"]).round(3).to_string())
print(pd.DataFrame(S["quintiles"]).T.round(3).to_string())
print("results", {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in S["results"].items() if not isinstance(v, dict)})
print(pd.DataFrame(S["results"]["costs_grid"]).T.round(3).to_string())
print("placebo", {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in S["placebo"].items() if kk != "same_weeks"})
print("placebo same weeks", S["placebo"]["same_weeks"])
print("H3", S["h3"])
print("full sample", S.get("full_sample"))
