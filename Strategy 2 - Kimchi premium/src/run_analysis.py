"""Mechanism tests (H1-H4), the froth overlay and risk analysis (DESIGN.md sections 2, 7, 9).

Usage: python -I src/run_analysis.py   (after run_backtest.py)
Writes output/tables/*.csv and output/tables/analysis.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402
from strategy import Market, fama_macbeth, nw_tstat, perf, formation_dates  # noqa: E402

T = C.TABLES
D = pd.Timedelta(days=1)
out = {}

mk = Market("KR")
macro = mk.macro
P = pd.read_parquet(os.path.join(C.PROC, "panel_kr_report.parquet"))   # last five years
P["sig_pct"] = P["signal"] * 100
P["logvol"] = np.log(P["perp_vol"])
res = pd.read_csv(os.path.join(T, "weekly_main.csv"), parse_dates=["week"], index_col="week")
contrib = pd.read_csv(os.path.join(T, "contrib_main.csv"), parse_dates=["week"])


def ols_nw(y, X, lags):
    """OLS with Newey-West standard errors. X without constant."""
    df = pd.concat([y, X], axis=1).dropna()
    yv = df.iloc[:, 0].values
    Xv = np.column_stack([np.ones(len(df)), df.iloc[:, 1:].values])
    b = np.linalg.lstsq(Xv, yv, rcond=None)[0]
    e = yv - Xv @ b
    n, k = Xv.shape
    XtX_inv = np.linalg.inv(Xv.T @ Xv)
    S = (Xv * e[:, None]).T @ (Xv * e[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = (Xv[L:] * e[L:, None]).T @ (Xv[:-L] * e[:-L, None])
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.diag(V))
    r2 = 1 - (e @ e) / ((yv - yv.mean()) @ (yv - yv.mean()))
    names = ["const"] + list(df.columns[1:])
    return pd.DataFrame({"coef": b, "se": se, "t": b / se}, index=names), r2, n


# ===================================================================== H1 segmentation
kr, jp = macro["kappa_kr"], macro["kappa_jp"]
btc_w = mk.world["BTC"]


def half_life(s):
    s = s.dropna()
    x, y = s.shift(1).dropna(), s.iloc[1:]
    rho = np.polyfit(x.values, y.loc[x.index].values, 1)[0]
    return np.log(0.5) / np.log(rho) if 0 < rho < 1 else np.nan


h1 = []
for lab, s in [("Korea (Upbit, KRW)", kr), ("Japan (bitbank, JPY)", jp)]:
    for lo, hi in [(C.REPORT_DAILY_START, C.REPORT_DAILY_END)]:
        x = s.loc[lo:hi].dropna()
        wk = x.resample("W-SUN").mean()
        ret4 = np.log(btc_w).resample("W-SUN").last().diff(4)
        h1.append({"market": lab, "sample": f"{lo[:7]} to {hi[:7]}", "mean": x.mean(), "sd": x.std(), "p95": x.quantile(.95), "max": x.max(),
                   "min": x.min(), "share_above_2pct": (x > 0.02).mean(), "half_life_days": half_life(x),
                   "corr_with_btc_4w_return": wk.corr(ret4.reindex(wk.index))})
h1 = pd.DataFrame(h1)
h1.to_csv(os.path.join(T, "h1_segmentation.csv"), index=False)
pi_kr, pi_jp = pd.read_parquet(os.path.join(C.PROC, "pi_kr.parquet")), pd.read_parquet(os.path.join(C.PROC, "pi_jp.parquet"))
out["h1"] = h1.to_dict("records")
out["usdt_premium_mean"] = float(macro["usdt_premium_kr"].dropna().mean())
out["usdt_premium_start"] = str(macro["usdt_premium_kr"].dropna().index.min().date())

# ===================================================================== H2 Fama-MacBeth and quintiles
fm = {}
for name, xs in [("signal", ("sig_pct",)), ("signal+past1", ("sig_pct", "past1")),
                 ("full", ("sig_pct", "past1", "past4", "logvol", "fund7"))]:
    r, B = fama_macbeth(P, "ret_long", xs)
    fm[name] = r
    r.to_csv(os.path.join(T, f"fm_{name.replace('+', '_')}.csv"))
# horizon: does the effect persist beyond one week?
hz = []
for h in [1, 2, 3, 4]:
    rows = []
    for M, g in P.groupby("week"):
        days = pd.date_range(M, M + (7 * h - 1) * D)
        if days[-1] > mk.perp_ret.index.max():
            continue
        r = mk.perp_ret.loc[days, g["coin"]].where(mk.perp_close.loc[days, g["coin"]].notna(), 0).fillna(0)
        f = mk.funding.loc[days, g["coin"]].fillna(0).sum()
        rows.append(pd.DataFrame({"week": M, "coin": g["coin"].values, "sig_pct": g["sig_pct"].values,
                                  "past1": g["past1"].values, "y": ((1 + r).prod() - 1 - f).values}))
    PH = pd.concat(rows)
    r, _ = fama_macbeth(PH, "y", ("sig_pct", "past1"), lags=max(4, 2 * h))
    hz.append({"horizon_weeks": h, "coef": r.loc["sig_pct", "coef"], "t_nw": r.loc["sig_pct", "t_nw"]})
hz = pd.DataFrame(hz)
hz.to_csv(os.path.join(T, "fm_horizons.csv"), index=False)

def sort_groups(g):
    """Same legs as the backtest: Q1 = the k lowest premia (long), Q5 = the k highest (short),
    k = floor(0.2 N); the middle coins are split into three equal groups by rank."""
    o = g.sort_values("signal", kind="mergesort")
    n = len(o)
    k = int(np.floor(n * C.QUANTILE))
    lab = np.empty(n, dtype=int)
    lab[:k], lab[n - k:] = 0, 4
    mid = n - 2 * k
    lab[k:n - k] = 1 + (np.arange(mid) * 3 // max(mid, 1))
    return pd.Series(lab, index=o.index).reindex(g.index).rename("q")


qrows = []
for M, g in P.groupby("week"):
    if len(g) < C.MIN_COINS:
        continue
    q = sort_groups(g)
    g = g.assign(dpi=g["pi_end"] - g["pi_last"],
                 dlocal_rel=g["dlocal"] - g["dlocal"].mean(), dworld_rel=g["dworld"] - g["dworld"].mean(),
                 ret_rel=g["ret_long"] - g["ret_long"].mean())
    agg = g.groupby(q).agg(ret_long=("ret_long", "mean"), ret_price=("ret_price", "mean"), funding=("funding", "mean"),
                           fund7=("fund7", "mean"), past1=("past1", "mean"), signal=("signal", "mean"),
                           dpi=("dpi", "mean"), dlocal_rel=("dlocal_rel", "mean"), dworld_rel=("dworld_rel", "mean"),
                           ret_rel=("ret_rel", "mean"), median_ret=("ret_long", "median"))
    qrows.append(agg.assign(week=M))
Q = pd.concat(qrows).reset_index()
qt = Q.groupby("q").agg(signal_bp=("signal", lambda x: x.mean() * 1e4), ret_long_ann=("ret_long", lambda x: x.mean() * 52),
                        ret_rel_ann=("ret_rel", lambda x: x.mean() * 52), price_ann=("ret_price", lambda x: x.mean() * 52),
                        funding_paid_ann=("funding", lambda x: x.mean() * 52), fund7_ann=("fund7", lambda x: x.mean() * 52),
                        past1_pct=("past1", lambda x: x.mean() * 100),
                        dpi_bp=("dpi", lambda x: x.mean() * 1e4), dlocal_rel_pct=("dlocal_rel", lambda x: x.mean() * 100),
                        dworld_rel_pct=("dworld_rel", lambda x: x.mean() * 100),
                        median_ret_ann=("median_ret", lambda x: x.mean() * 52))
qt["t_rel"] = Q.groupby("q")["ret_rel"].apply(nw_tstat)
qt["t_dpi"] = Q.groupby("q")["dpi"].apply(nw_tstat)
qt["t_dworld"] = Q.groupby("q")["dworld_rel"].apply(nw_tstat)
qt["t_dlocal"] = Q.groupby("q")["dlocal_rel"].apply(nw_tstat)
qt.index = ["Q1 lowest premium", "Q2", "Q3", "Q4", "Q5 highest premium"]
qt.to_csv(os.path.join(T, "quintiles.csv"))
out["quintiles"] = qt.reset_index().rename(columns={"index": "quintile"}).to_dict("records")
out["fm"] = {k: v.reset_index().rename(columns={"index": "var"}).to_dict("records") for k, v in fm.items()}
out["fm_horizons"] = hz.to_dict("records")
print("FM:", {k: (round(v.loc['sig_pct', 'coef'], 4), round(v.loc['sig_pct', 't_nw'], 2)) for k, v in fm.items()})
print(qt.round(3).to_string())
print(hz.round(4).to_string())

# premium buckets (economic size of the signal)
P["rel"] = P["ret_long"] - P.groupby("week")["ret_long"].transform("mean")
edges = [-1, -0.01, -0.0025, 0.0025, 0.01, 1]
labels = ["below −1%", "−1% to −0.25%", "±0.25%", "0.25% to 1%", "above 1%"]
P["bucket"] = pd.cut(P["signal"], edges, labels=labels)
bk = P.groupby("bucket", observed=True).agg(coin_weeks=("rel", "size"), rel_ret_wk=("rel", "mean"), past1=("past1", "mean"),
                                             fund7_ann=("fund7", lambda x: x.mean() * 52))
bk["t"] = P.groupby("bucket", observed=True)["rel"].apply(lambda x: x.mean() / x.std() * np.sqrt(len(x)))
bk.to_csv(os.path.join(T, "premium_buckets.csv"))
out["buckets"] = bk.reset_index().to_dict("records")
out["signal_iqr_bp"] = [float(P["signal"].quantile(.25) * 1e4), float(P["signal"].quantile(.75) * 1e4)]
out["share_abs_signal_below_25bp"] = float((P["signal"].abs() < 0.0025).mean())

# ===================================================================== H3 froth (aggregate premium -> BTC)
weeks = formation_dates(C.REPORT_START, C.LAST_FORMATION)
kbar = pd.Series({M: kr.loc[M - 7 * D:M - D].mean() for M in weeks})
bw = btc_w.reindex(pd.date_range(btc_w.index.min(), btc_w.index.max() + 60 * D))
fwd4 = pd.Series({M: np.log(bw.loc[M + 27 * D] / bw.loc[M - D]) for M in weeks})
fwd1 = pd.Series({M: np.log(bw.loc[M + 6 * D] / bw.loc[M - D]) for M in weeks})
reg4, r2_4, n4 = ols_nw(fwd4.rename("y"), kbar.rename("kappa").to_frame(), 8)
reg1, r2_1, n1 = ols_nw(fwd1.rename("y"), kbar.rename("kappa").to_frame(), 4)
out["h3"] = {"coef_4w": reg4.loc["kappa", "coef"], "t_4w": reg4.loc["kappa", "t"], "r2_4w": r2_4, "n": n4,
             "coef_1w": reg1.loc["kappa", "coef"], "t_1w": reg1.loc["kappa", "t"], "r2_1w": r2_1}
print("H3:", {k: round(v, 3) for k, v in out["h3"].items()})

# overlay: BTC perp long unless kappa_bar above trailing-365d 90th percentile
btc_perp = mk.perp_ret["BTC"]
btc_f = mk.funding["BTC"].fillna(0)
tb = macro["tbill"].ffill()
ov = []
for M in weeks:
    hold = pd.date_range(M, M + 6 * D)
    r_btc = (1 + btc_perp.loc[hold].fillna(0)).prod() - 1 - btc_f.loc[hold].sum()
    thr = kr.loc[M - 365 * D:M - D].quantile(C.FROTH_PCTL)
    froth = kbar.loc[M] > thr
    cash = tb.loc[M - D] / 52
    ov.append({"week": M, "btc": r_btc, "kappa_bar": kbar.loc[M], "threshold": thr, "froth": bool(froth),
               "overlay": cash if froth else r_btc, "cash": cash})
ov = pd.DataFrame(ov).set_index("week")
ov.to_csv(os.path.join(T, "overlay_weekly.csv"))
pb, po = perf(ov["btc"]), perf(ov["overlay"])
out["overlay"] = {"btc": pb, "overlay": po, "froth_weeks": int(ov["froth"].sum()), "weeks": len(ov),
                  "btc_ret_in_froth_weeks_ann": ov.loc[ov.froth, "btc"].mean() * 52,
                  "btc_ret_other_weeks_ann": ov.loc[~ov.froth, "btc"].mean() * 52,
                  "t_diff": (ov.loc[ov.froth, "btc"].mean() - ov.loc[~ov.froth, "btc"].mean()) /
                            np.sqrt(ov.loc[ov.froth, "btc"].var() / ov.froth.sum() + ov.loc[~ov.froth, "btc"].var() / (~ov.froth).sum())}
print("overlay:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["overlay"].items() if not isinstance(v, dict)})
print("  btc", {k: round(v, 3) for k, v in pb.items()}); print("  ovl", {k: round(v, 3) for k, v in po.items()})

# ===================================================================== risk analysis on the main rule
r = res.copy()
btc_wk = ov["btc"].reindex(r.index)
mkt = P.groupby("week")["ret_long"].mean().reindex(r.index)
mom = []
for M, g in P.groupby("week"):
    k = int(np.floor(len(g) * C.QUANTILE))
    o = g.sort_values("past4")
    mom.append((M, o["ret_long"].iloc[-k:].mean() - o["ret_long"].iloc[:k].mean()))
mom = pd.Series(dict(mom)).reindex(r.index)
vixw = macro["vix"].ffill()
krw = macro["krw_per_usd"].ffill()
dvix = pd.Series({M: vixw.loc[M + 6 * D] - vixw.loc[M - D] for M in r.index})
dkrw = pd.Series({M: np.log(krw.loc[M + 6 * D] / krw.loc[M - D]) for M in r.index})
dkap = pd.Series({M: kr.loc[M:M + 6 * D].mean() - kbar.loc[M] for M in r.index})
X = pd.DataFrame({"BTC_up": btc_wk.clip(lower=0), "BTC_down": btc_wk.clip(upper=0), "MKT_EW": mkt - btc_wk,
                  "MOM": mom, "dVIX": dvix / 10, "dKRW": dkrw, "dKAPPA": dkap})
expo, r2e, ne = ols_nw(r["net"], X, 4)
expo.to_csv(os.path.join(T, "exposures.csv"))
out["exposures"] = {"table": expo.reset_index().rename(columns={"index": "factor"}).to_dict("records"), "r2": r2e, "n": ne}
print(expo.round(3).to_string(), "R2", round(r2e, 3))

# episodes
ep = []
for name, (a, b) in C.EPISODES.items():
    M = pd.Timestamp(a)
    if M in r.index:
        ep.append({"episode": name, "week": a, "strategy": r.loc[M, "net"], "long_leg": r.loc[M, "long_ret"],
                   "short_leg": r.loc[M, "short_ret"], "btc": btc_wk.loc[M], "kappa_bar": kbar.loc[M]})
ep = pd.DataFrame(ep)
ep.to_csv(os.path.join(T, "episodes.csv"), index=False)
out["episodes"] = ep.to_dict("records")
print(ep.round(3).to_string())

# liquidity terciles (by Binance perp volume within each week)
P["liq_t"] = P.groupby("week")["perp_vol"].transform(lambda x: pd.qcut(x.rank(method="first"), 3, labels=False))
cm = contrib.merge(P[["week", "coin", "liq_t", "signal"]], on=["week", "coin"], how="left")
liq = cm.groupby("liq_t")["pnl"].sum() / len(r) * 52
liq.index = ["Least liquid third", "Middle third", "Most liquid third"]
liq.to_csv(os.path.join(T, "pnl_by_liquidity.csv"))
out["liquidity"] = liq.to_dict()

# concentration by coin and by side
bycoin = cm.groupby("coin")["pnl"].sum().sort_values()
total = bycoin.sum()
out["concentration"] = {"total_gross_pnl_sum": total, "best5": bycoin.tail(5).to_dict(), "worst5": bycoin.head(5).to_dict(),
                        "n_coins_traded": int(bycoin.size)}
side = cm.assign(side=np.where(cm.weight > 0, "long", "short")).groupby("side")["pnl"].sum() / len(r) * 52
out["side_pnl_ann"] = side.to_dict()
bycoin.to_csv(os.path.join(T, "pnl_by_coin.csv"))

# worst weeks and their drivers
ww = r["net"].nsmallest(10)
wrows = []
for M, v in ww.items():
    c = cm[cm.week == M].sort_values("pnl")
    wrows.append({"week": str(M.date()), "net": v, "btc": btc_wk.loc[M], "drivers": ", ".join(f"{x.coin} ({'short' if x.weight < 0 else 'long'} {x.pnl * 100:+.1f}pp)" for x in c.head(3).itertuples())})
pd.DataFrame(wrows).to_csv(os.path.join(T, "worst_weeks.csv"), index=False)
out["worst_weeks"] = wrows
print(pd.DataFrame(wrows).to_string())

# returns by aggregate-premium regime
reg = pd.cut(kbar.reindex(r.index), [-1, 0, 0.02, 0.05, 1], labels=["discount", "0–2%", "2–5%", "above 5%"])
byreg = r.groupby(reg, observed=True)["net"].agg(["mean", "size"])
byreg["mean"] *= 52
byreg.index.name = "regime"
out["by_kappa_regime"] = byreg.reset_index().to_dict("records")

# ---------------------------------------------------------------- where the money goes, by year
yr = r.groupby(r.index.year).agg(price=("price", "sum"), funding=("funding", "sum"), cost=("cost", "sum"),
                                 net=("net", "sum"), weeks=("net", "size"))
yr["cost"] = -yr["cost"]
yr.to_csv(os.path.join(T, "pnl_by_year.csv"))
out["pnl_by_year"] = yr.reset_index().rename(columns={"week": "year"}).to_dict("records")

# heavy tails: medians and the single worst week
worst = r["net"].idxmin()
out["tails"] = {"median_week_gross": r["gross"].median(), "median_week_net": r["net"].median(),
                "mean_week_net": r["net"].mean(), "hit_rate_net": (r["net"] > 0).mean(),
                "worst_week": str(worst.date()), "worst_week_net": r.loc[worst, "net"],
                "sharpe_net_ex_worst_week": perf(r["net"].drop(worst))["sharpe"],
                "sharpe_gross_ex_worst_week": perf(r["gross"].drop(worst))["sharpe"]}
wc = cm[cm.week == worst].sort_values("pnl").iloc[0]
pw = P[(P.week == worst) & (P.coin == wc.coin)].iloc[0]
out["worst_coin"] = {"week": str(worst.date()), "coin": wc.coin, "weight": float(wc.weight), "pnl": float(wc.pnl),
                     "signal": float(pw.signal), "ret_price": float(pw.ret_price), "fund7_ann": float(pw.fund7 * 52),
                     "n_per_leg": int((cm[cm.week == worst].weight < 0).sum())}

# funding paid by leg (annualised, per $1 of the leg)
lf = cm.merge(P[["week", "coin", "funding"]], on=["week", "coin"])
lf["fund_pnl"] = -lf["weight"] * lf["funding"]
out["funding_by_leg"] = (lf.assign(side=np.where(lf.weight > 0, "long leg", "short leg"))
                         .groupby("side")["fund_pnl"].sum() / len(r) * 52).to_dict()

# ---------------------------------------------------------------- one live week: the last formation
M = r.index.max()
g = P[P.week == M].sort_values("signal")
k = int(np.floor(len(g) * C.QUANTILE))
up = mk.local.loc[M - D, g.coin]
wo = mk.world.loc[M - D, g.coin]
fx = macro.loc[M - D, "krw_per_usd"]
live = g.assign(upbit_krw=up.values, world_usd=wo.values, premium=(np.log(up.values) - np.log(wo.values) - np.log(fx)),
                side=["long"] * k + [""] * (len(g) - 2 * k) + ["short"] * k)
live = live[live.side != ""][["coin", "side", "signal", "premium", "upbit_krw", "world_usd", "fund7", "ret_price", "funding", "ret_long"]]
live.to_csv(os.path.join(T, "live_week.csv"), index=False)
out["live_week"] = {"week": str(M.date()), "n_coins": int(len(g)), "k": k, "kappa_bar": float(kbar.loc[M]),
                    "krw_per_usd": float(fx), "rows": live.to_dict("records"),
                    "net": float(r.loc[M, "net"]), "gross": float(r.loc[M, "gross"])}

json.dump(out, open(os.path.join(T, "analysis.json"), "w"), default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o), indent=1)
print("saved")
