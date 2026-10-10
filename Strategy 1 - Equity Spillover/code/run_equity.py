#!/usr/bin/env python3
"""MFE 230GB — Equity spillover into FX: countries whose equity markets outperform see their currency appreciate next.

Developed-market book (9 G10 currencies vs USD) and emerging-market book (13 currencies vs USD).
Runs a grid of construction methods, selects on 2000-2015, validates on 2016-2026.

    python project/code/run_equity.py   # writes output/equity_results.json, output/equity_monthly.csv
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

START, SPLIT, END = "2000-01-31", "2015-12-31", "2026-12-31"
DM = {  # fx file, invert (file is FC per USD), 3-month rate file, equity file
    "EUR": ("DEXUSEU", False, "IR3TIB01EZM156N"), "JPY": ("DEXJPUS", True, "IR3TIB01JPM156N"), "GBP": ("DEXUSUK", False, "IR3TIB01GBM156N"),
    "AUD": ("DEXUSAL", False, "IR3TIB01AUM156N"), "CAD": ("DEXCAUS", True, "IR3TIB01CAM156N"), "CHF": ("DEXSZUS", True, "IR3TIB01CHM156N"),
    "SEK": ("DEXSDUS", True, "IR3TIB01SEM156N"), "NOK": ("DEXNOUS", True, "IR3TIB01NOM156N"), "NZD": ("DEXUSNZ", False, "IR3TIB01NZM156N"),
}
EM = {  # source, file, rate file (None = spot only), regime per IMF AREAER 2026 / Topic 2
    "BRL": ("fred", "DEXBZUS", None, "float"), "MXN": ("fred", "DEXMXUS", "IR3TIB01MXM156N", "float"), "ZAR": ("fred", "DEXSFUS", "IR3TIB01ZAM156N", "float"),
    "INR": ("fred", "DEXINUS", None, "managed"), "KRW": ("fred", "DEXKOUS", "IR3TIB01KRM156N", "float"), "CNY": ("fred", "DEXCHUS", None, "managed"),
    "PLN": ("ecb", "ECBFX_PLN", "IR3TIB01PLM156N", "float"), "HUF": ("ecb", "ECBFX_HUF", "IR3TIB01HUM156N", "float"), "CZK": ("ecb", "ECBFX_CZK", "IR3TIB01CZM156N", "float"),
    "TRY": ("ecb", "ECBFX_TRY", "IR3TIB01TRM156N", "managed"), "IDR": ("ecb", "ECBFX_IDR", "IR3TIB01IDM156N", "managed"),
    "CLP": ("imf", "IMFFX_CLP", "IR3TIB01CLM156N", "float"), "COP": ("imf", "IMFFX_COP", None, "float"),
}
COST = {"DM": 0.0002, "EM": 0.0015}
FREELY_FALLING_RATE = 0.30   # exclude a currency while its 3-month rate is above 30% (Topic 2: freely falling)


def load_fred(name):
    df = pd.read_csv(DATA / f"{name}.csv")
    dc = "observation_date" if "observation_date" in df.columns else df.columns[0]
    vc = [c for c in df.columns if c != dc][0]
    s = pd.to_numeric(df.set_index(pd.to_datetime(df[dc]))[vc], errors="coerce")
    return s[~s.index.duplicated(keep="last")].sort_index().replace(0, np.nan)


def monthly_period_csv(name, col):
    df = pd.read_csv(DATA / f"{name}.csv")
    idx = pd.PeriodIndex(df["period"].astype(str), freq="M").to_timestamp(how="end").normalize()
    return pd.Series(pd.to_numeric(df[col], errors="coerce").values, index=idx).resample("ME").last()


def equity(ccy):
    return np.log(monthly_period_csv(f"EQ_{ccy}", "share_price_index"))


def stats(r, ann=12):
    r = r.dropna()
    if len(r) < 12:
        return {}
    mu, vol = float(r.mean() * ann), float(r.std() * np.sqrt(ann))
    w = (1 + r).cumprod()
    return {"n": int(len(r)), "start": str(r.index.min().date()), "end": str(r.index.max().date()), "mean": round(mu, 4), "vol": round(vol, 4),
            "sharpe": round(mu / vol, 3) if vol else None, "mdd": round(float((w / w.cummax() - 1).min()), 4),
            "hit": round(float((r > 0).mean()), 3), "cum": round(float(w.iloc[-1] - 1), 4), "skew": round(float(r.skew()), 2)}


def equity_curve(r):
    return (1 + r.fillna(0)).cumprod() - 1


def series_xy(s, n=500):
    s = s.dropna()
    if len(s) > n:
        s = s.iloc[:: max(1, len(s) // n)]
    return [{"date": str(d.date()), "v": round(float(x), 6)} for d, x in s.items()]


def build_panel(universe):
    i_us = load_fred("IR3TIB01USM156N").resample("ME").last().ffill() / 100
    logS, carry, E, regime = {}, {}, {}, {}
    if universe == "DM":
        for c, (fx, inv, rate) in DM.items():
            s = load_fred(fx)
            s = 1 / s if inv else s
            logS[c] = np.log(s).resample("ME").last()
            carry[c] = load_fred(rate).resample("ME").last().ffill() / 100
            E[c] = equity(c)
    else:
        usd_per_eur = monthly_period_csv("ECBFX_USD", "per_eur")
        for c, (src, f, rate, reg) in EM.items():
            if src == "fred":
                logS[c] = np.log(1 / load_fred(f)).resample("ME").last()
            elif src == "ecb":
                per_eur = monthly_period_csv(f, "per_eur")
                logS[c] = -np.log(per_eur / usd_per_eur)            # log USD per unit
            else:
                logS[c] = -np.log(monthly_period_csv(f, "per_usd"))
            if rate:
                carry[c] = load_fred(rate).resample("ME").last().ffill() / 100
            E[c] = equity(c)
            regime[c] = reg
    logS = pd.DataFrame(logS)
    logS = logS.loc["1995-01-31":]
    E = pd.DataFrame(E).reindex(logS.index)
    rate = pd.DataFrame(carry).reindex(logS.index).ffill(limit=12).reindex(columns=logS.columns)
    carry = rate.sub(i_us.reindex(logS.index).ffill(limit=12), axis=0)
    xr = logS.diff() + carry.shift(1).fillna(0) / 12            # spot change plus carry where a rate exists
    spot = logS.diff()
    # freely-falling exclusion
    ok = ~(rate > FREELY_FALLING_RATE)
    return {"logS": logS, "E": E, "rate": rate, "carry": carry, "xr": xr, "spot": spot, "ok": ok, "regime": regime}


def signal_matrix(P, measure, k):
    E, logS, rate = P["E"], P["logS"], P["rate"]
    if measure == "local":
        sig = E.diff(k)
    elif measure == "usd":
        sig = (E + logS).diff(k)
    elif measure == "excess":                                    # local equity return minus local cash return
        sig = E.diff(k) - rate.rolling(k).mean() * k / 12
    elif measure == "vol_adj":                                   # local return scaled by trailing 12m equity vol
        sig = E.diff(k) / (E.diff().rolling(12).std() * np.sqrt(k))
    elif measure == "rel_us":
        sig = E.diff(k).sub(equity("USD").reindex(E.index).diff(k), axis=0)
    else:
        raise ValueError(measure)
    return sig.where(P["ok"].reindex(sig.index).fillna(True))


def weights_from_signal(sig, scheme, n_leg):
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for dt, row in sig.iterrows():
        s = row.dropna()
        if len(s) < (1 if scheme == "dollar" else 2 * n_leg):
            continue
        if scheme == "tercile":
            ranked = s.sort_values()
            w.loc[dt, ranked.index[:n_leg]] = -1.0 / n_leg
            w.loc[dt, ranked.index[-n_leg:]] = 1.0 / n_leg
        elif scheme == "rank":                                   # linear in rank, long/short, each side sums to 1
            r = s.rank() - (len(s) + 1) / 2
            w.loc[dt, r.index] = r / r.abs().sum() * 2 / 1.0 * 0.5
            w.loc[dt, r.index] = w.loc[dt, r.index] / w.loc[dt, r.index].clip(lower=0).sum()
        elif scheme == "dollar":                                 # time-series vs USD: +1/n if signal > 0 else -1/n
            w.loc[dt, s.index] = np.sign(s) / len(s)
    return w


def backtest(w, ret, cost, hold=1):
    if hold > 1:                                                 # overlapping portfolios: average of the last `hold` monthly books
        w = w.rolling(hold, min_periods=1).mean()
    w = w.fillna(0)
    turnover = w.diff().abs().sum(axis=1)
    gross = (w.shift(1) * ret).sum(axis=1)
    return gross - cost * turnover, turnover, w


def run_spec(P, universe, measure, k, scheme, hold, ret_kind="xr", skip=0, vix_on=None):
    sig = signal_matrix(P, measure, k).shift(skip)
    n_leg = 3 if universe == "DM" else 3
    w = weights_from_signal(sig, scheme, n_leg)
    if vix_on is not None:
        w = w.mul(vix_on.reindex(w.index).fillna(0), axis=0)
    ret = P[ret_kind]
    r, to, w_used = backtest(w, ret, COST[universe], hold)
    return r.loc[START:], to.loc[START:], w_used.loc[START:]


def main():
    vix = load_fred("VIXCLS").resample("ME").mean()
    vix_q = vix.expanding(min_periods=60).quantile(0.8)
    risk_on = (vix < vix_q).astype(float)
    usd = np.log(load_fred("DTWEXBGS")).diff().resample("ME").sum(min_count=1)
    results = {"generated": pd.Timestamp.now().strftime("%Y-%m-%d"), "spec": {"start": START, "split": SPLIT, "cost": COST, "freely_falling_rate": FREELY_FALLING_RATE}}

    for universe in ("DM", "EM"):
        P = build_panel(universe)
        grid = []
        for measure, k, scheme, hold in product(("local", "usd", "excess", "vol_adj"), (1, 3, 6, 12), ("tercile", "rank"), (1, 3)):
            r, to, _ = run_spec(P, universe, measure, k, scheme, hold)
            a, b, full = stats(r.loc[:SPLIT]), stats(r.loc[SPLIT:]), stats(r)
            grid.append({"measure": measure, "k": k, "scheme": scheme, "hold": hold, "sharpe_train": a.get("sharpe"), "sharpe_test": b.get("sharpe"),
                         "sharpe_full": full.get("sharpe"), "mean_full": full.get("mean"), "mdd_full": full.get("mdd"), "turnover": round(float(to.mean() * 12), 1)})
        grid_df = pd.DataFrame(grid)
        best = grid_df.sort_values("sharpe_train", ascending=False).iloc[0].to_dict()
        # dollar-relative (time-series) variants
        ts = []
        for measure, k in product(("rel_us", "local"), (3, 6, 12)):
            r, to, _ = run_spec(P, universe, measure, k, "dollar", 1)
            ts.append({"measure": measure, "k": k, "scheme": "dollar", "sharpe_train": stats(r.loc[:SPLIT]).get("sharpe"), "sharpe_test": stats(r.loc[SPLIT:]).get("sharpe"), "sharpe_full": stats(r).get("sharpe"), "turnover": round(float(to.mean() * 12), 1)})
        # chosen spec detail
        bm, bk, bs, bh = best["measure"], int(best["k"]), best["scheme"], int(best["hold"])
        r, to, w = run_spec(P, universe, bm, bk, bs, bh)
        r_spot, _, _ = run_spec(P, universe, bm, bk, bs, bh, ret_kind="spot")
        r_skip, _, _ = run_spec(P, universe, bm, bk, bs, bh, skip=1)
        r_von, _, _ = run_spec(P, universe, bm, bk, bs, bh, vix_on=risk_on)
        r_def, to_def, w_def = run_spec(P, universe, "local", 6, "tercile", 1)
        # placebo for chosen spec: shuffle the cross-section each month
        rng = np.random.default_rng(0)
        sig = signal_matrix(P, bm, bk)
        sh = []
        for _ in range(300):
            p = sig.apply(lambda row: pd.Series(rng.permutation(row.values), index=row.index), axis=1)
            wp = weights_from_signal(p, bs, 3)
            rp, _, _ = backtest(wp, P["xr"], COST[universe], bh)
            sh.append(stats(rp.loc[START:]).get("sharpe"))
        sh = np.array([x for x in sh if x is not None])
        # FX momentum control: same spec on FX return instead of equity
        fxmom = P["logS"].diff(bk).where(P["ok"].reindex(P["logS"].index).fillna(True))
        wfx = weights_from_signal(fxmom, bs, 3)
        r_fxmom, _, _ = backtest(wfx, P["xr"], COST[universe], bh)
        # pooled predictive regression
        sig_l = signal_matrix(P, "local", bk)
        a = pd.concat([P["xr"].shift(-1).loc[START:].stack().rename("y"), sig_l.loc[START:].stack().rename("x")], axis=1).dropna()
        pooled = {"beta": round(float(np.polyfit(a.x, a.y, 1)[0]), 4), "corr": round(float(a.x.corr(a.y)), 3), "n": int(len(a))}
        a2 = pd.concat([P["spot"].loc[START:].stack().rename("y"), P["E"].diff().loc[START:].stack().rename("x")], axis=1).dropna()
        contemp = round(float(a2.x.corr(a2.y)), 3)
        # risk
        wealth = (1 + r.fillna(0)).cumprod(); dd = wealth / wealth.cummax() - 1
        ab = pd.concat([r.rename("r"), usd.rename("usd"), vix.rename("vix")], axis=1).loc[START:].dropna()
        risk = {"corr_usd": round(float(ab.r.corr(ab.usd)), 3), "beta_usd": round(float(np.polyfit(ab.usd, ab.r, 1)[0]), 3),
                "high_vix_sharpe": stats(ab.loc[ab.vix >= ab.vix.quantile(0.8), "r"]).get("sharpe"), "low_vix_sharpe": stats(ab.loc[ab.vix < ab.vix.quantile(0.8), "r"]).get("sharpe"),
                "mdd": {"dd": round(float(dd.min()), 3), "trough": str(dd.idxmin().date()), "peak": str(wealth.loc[:dd.idxmin()].idxmax().date())},
                "worst_months": [{"date": str(d.date()), "ret": round(float(v) * 100, 2), "longs": [c for c in w.columns if w.shift(1).loc[d, c] > 0.01],
                                  "shorts": [c for c in w.columns if w.shift(1).loc[d, c] < -0.01], "usd": round(float(usd.get(d, np.nan)) * 100, 2)} for d, v in r.nsmallest(5).items()],
                "annual": {int(y): round(float(v) * 100, 1) for y, v in r.groupby(r.index.year).sum().items()},
                "long_freq": {c: round(float((w[c] > 0.01).mean()), 2) for c in w.columns}, "short_freq": {c: round(float((w[c] < -0.01).mean()), 2) for c in w.columns},
                "contrib_pct": {c: round(float((w.shift(1)[c] * P["xr"].loc[START:, c]).sum() * 100), 1) for c in w.columns},
                "turnover_per_year": round(float(to.mean() * 12), 1), "cost_per_year_bp": round(float(to.mean() * 12 * COST[universe] * 1e4), 1)}
        pos = r[r > 0].sort_values(ascending=False); risk["top5pct_share"] = round(float(pos.head(max(1, int(len(pos) * 0.05))).sum() / pos.sum()), 3)
        last = w.index[(w.abs().sum(axis=1) > 0)][-1]
        current = {"date": str(last.date()), "longs": [c for c in w.columns if w.loc[last, c] > 0.01], "shorts": [c for c in w.columns if w.loc[last, c] < -0.01],
                   "signal": {c: round(float(signal_matrix(P, bm, bk).loc[last, c]) * 100, 1) for c in w.columns if pd.notna(signal_matrix(P, bm, bk).loc[last, c])}}

        # ---- dollar-relative (time-series) version: long FC if its equity beat US equity over k months, else short ----
        dollar = {}
        for k in (3, 6, 12):
            rd, tod, wd = run_spec(P, universe, "rel_us", k, "dollar", 1)
            net_pos = wd.sum(axis=1)                                   # net foreign-currency exposure (negative = net long USD)
            basket = P["xr"].mean(axis=1)                              # equal-weight basket of the universe vs USD
            # pure dollar timing: long USD vs basket when US equity beat the universe average over k months
            us_eq = equity("USD").reindex(P["E"].index)
            rel_avg = us_eq.diff(k) - P["E"].diff(k).mean(axis=1)
            pos = -np.sign(rel_avg)                                    # +1 = long basket (foreign), -1 = long USD
            r_time = (pos.shift(1) * basket).loc[START:] - COST[universe] * pos.diff().abs().fillna(0).loc[START:]
            # cross-sectional residual: dollar variant minus its net-dollar component
            r_cs = (rd - (net_pos.shift(1) * basket).loc[START:])
            # placebo: circularly shift the signal in time (300 random shifts of 12..200 months)
            rng = np.random.default_rng(1); sh = []
            sig = signal_matrix(P, "rel_us", k)
            for _ in range(200):
                shift = int(rng.integers(12, 200))
                ps = pd.DataFrame(np.roll(sig.values, shift, axis=0), index=sig.index, columns=sig.columns)
                wp = weights_from_signal(ps, "dollar", 3)
                rp, _, _ = backtest(wp, P["xr"], COST[universe], 1)
                sh.append(stats(rp.loc[START:]).get("sharpe"))
            sh = np.array([x for x in sh if x is not None])
            ab2 = pd.concat([rd.rename("r"), usd.rename("usd")], axis=1).loc[START:].dropna()
            wealth_d = (1 + rd.fillna(0)).cumprod(); dd_d = wealth_d / wealth_d.cummax() - 1
            lastd = wd.index[(wd.abs().sum(axis=1) > 0)][-1]
            dollar[f"k{k}"] = {
                "full": stats(rd), "train": stats(rd.loc[:SPLIT]), "test": stats(rd.loc[SPLIT:]),
                "sub": {f"{a_}-{b_}": stats(rd.loc[a_:b_]).get("sharpe") for a_, b_ in [("2000", "2007"), ("2008", "2012"), ("2013", "2019"), ("2020", "2026")]},
                "turnover_per_year": round(float(tod.mean() * 12), 1), "avg_net_fc_exposure": round(float(net_pos.loc[START:].mean()), 2),
                "share_months_net_long_usd": round(float((net_pos.loc[START:] < 0).mean()), 2),
                "dollar_timing_only": stats(r_time), "dollar_timing_train": stats(r_time.loc[:SPLIT]), "dollar_timing_test": stats(r_time.loc[SPLIT:]),
                "cross_sectional_residual": stats(r_cs),
                "placebo_time_shift": {"mean": round(float(sh.mean()), 3), "p95": round(float(np.percentile(sh, 95)), 3), "pval": round(float((sh >= stats(rd)["sharpe"]).mean()), 3)},
                "corr_usd": round(float(ab2.r.corr(ab2.usd)), 3), "beta_usd": round(float(np.polyfit(ab2.usd, ab2.r, 1)[0]), 3),
                "mdd": {"dd": round(float(dd_d.min()), 3), "trough": str(dd_d.idxmin().date()), "peak": str(wealth_d.loc[:dd_d.idxmin()].idxmax().date())},
                "annual": {int(y): round(float(v) * 100, 1) for y, v in rd.groupby(rd.index.year).sum().items()},
                "worst_months": [{"date": str(d.date()), "ret": round(float(v) * 100, 2), "net_fc": round(float(net_pos.shift(1).get(d, np.nan)), 2), "usd": round(float(usd.get(d, np.nan)) * 100, 2)} for d, v in rd.nsmallest(5).items()],
                "current": {"date": str(lastd.date()), "longs": [c for c in wd.columns if wd.loc[lastd, c] > 0], "shorts": [c for c in wd.columns if wd.loc[lastd, c] < 0],
                            "signal_pct": {c: round(float(sig.loc[lastd, c]) * 100, 1) for c in wd.columns if pd.notna(sig.loc[lastd, c])}},
                "equity": series_xy(equity_curve(rd)), "equity_dollar_timing": series_xy(equity_curve(r_time)), "net_exposure": series_xy(net_pos.loc[START:]),
            }
            if k == 6:
                r_sk, _, _ = run_spec(P, universe, "rel_us", k, "dollar", 1, skip=1); dollar["k6"]["skip_month"] = stats(r_sk)
                r_sp, _, _ = run_spec(P, universe, "rel_us", k, "dollar", 1, ret_kind="spot"); dollar["k6"]["spot_only"] = stats(r_sp)
                r_q, _, _ = run_spec(P, universe, "rel_us", k, "dollar", 3); dollar["k6"]["hold3"] = stats(r_q)
                r_lo, _, _ = run_spec(P, universe, "local", k, "dollar", 1); dollar["k6"]["local_not_rel_us"] = stats(r_lo)
                if universe == "EM":
                    r2b, _, _ = backtest(weights_from_signal(signal_matrix(P, "rel_us", k), "dollar", 3), P["xr"], 0.0002, 1); dollar["k6"]["at_2bp"] = stats(r2b.loc[START:])
                    for reg in ("float", "managed"):
                        cols = [c for c, v in P["regime"].items() if v == reg]
                        sub = {k_: (v[cols] if isinstance(v, pd.DataFrame) else v) for k_, v in P.items() if k_ != "regime"}; sub["regime"] = {c: reg for c in cols}
                        rr, _, _ = run_spec(sub, "EM", "rel_us", k, "dollar", 1)
                        dollar["k6"][f"regime_{reg}"] = {"currencies": cols, "full": stats(rr), "train": stats(rr.loc[:SPLIT]), "test": stats(rr.loc[SPLIT:])}
        print(f"  DOLLAR variant {universe}:")
        for kk, v in dollar.items():
            print(f"    {kk}: full {v['full'].get('sharpe')} train {v['train'].get('sharpe')} test {v['test'].get('sharpe')} sub {v['sub']} to {v['turnover_per_year']} net_fc {v['avg_net_fc_exposure']} longUSD {v['share_months_net_long_usd']} | timing-only {v['dollar_timing_only'].get('sharpe')} (train {v['dollar_timing_train'].get('sharpe')} test {v['dollar_timing_test'].get('sharpe')}) cs-resid {v['cross_sectional_residual'].get('sharpe')} | placebo {v['placebo_time_shift']} corr_usd {v['corr_usd']} mdd {v['mdd']}")
            for e in ("skip_month", "spot_only", "hold3", "local_not_rel_us", "at_2bp", "regime_float", "regime_managed"):
                if e in v: print(f"      {e}: {v[e] if 'full' not in v[e] else {kk2: v[e][kk2].get('sharpe') for kk2 in ('full','train','test')}}")
            print("      worst", v["worst_months"]); print("      annual", v["annual"]); print("      current", v["current"])
        out = {"grid": grid, "dollar": dollar, "time_series_variants": ts, "best_by_train": best,
               "best": {"full": stats(r), "train": stats(r.loc[:SPLIT]), "test": stats(r.loc[SPLIT:]), "spot_only": stats(r_spot), "skip_month": stats(r_skip), "risk_on_only": stats(r_von),
                        "sub": {f"{a_}-{b_}": stats(r.loc[a_:b_]) for a_, b_ in [("2000", "2007"), ("2008", "2012"), ("2013", "2019"), ("2020", "2026")]},
                        "placebo": {"mean": round(float(sh.mean()), 3), "p95": round(float(np.percentile(sh, 95)), 3), "pval": round(float((sh >= stats(r)["sharpe"]).mean()), 3)},
                        "fx_momentum_same_spec": stats(r_fxmom.loc[START:]), "pooled": pooled, "contemporaneous_corr": contemp, "risk": risk, "current": current},
               "default_local_6_tercile": {"full": stats(r_def), "train": stats(r_def.loc[:SPLIT]), "test": stats(r_def.loc[SPLIT:]), "turnover": round(float(to_def.mean() * 12), 1)},
               "equity_best": series_xy(equity_curve(r)), "equity_default": series_xy(equity_curve(r_def)), "equity_fxmom": series_xy(equity_curve(r_fxmom.loc[START:]))}
        if universe == "EM":
            for reg in ("float", "managed"):
                cols = [c for c, v in P["regime"].items() if v == reg]
                sub = {k_: (v[cols] if isinstance(v, pd.DataFrame) else v) for k_, v in P.items() if k_ != "regime"}
                sub["regime"] = {c: reg for c in cols}
                rr, tt, _ = run_spec(sub, "EM", bm, bk, bs, bh) if len(cols) >= 6 else run_spec(sub, "EM", bm, bk, "dollar", bh)
                out[f"regime_{reg}"] = {"currencies": cols, "scheme": bs if len(cols) >= 6 else "dollar", "full": stats(rr), "train": stats(rr.loc[:SPLIT]), "test": stats(rr.loc[SPLIT:])}
                a3 = pd.concat([sub["xr"].shift(-1).loc[START:].stack().rename("y"), signal_matrix(sub, "local", bk).loc[START:].stack().rename("x")], axis=1).dropna()
                out[f"regime_{reg}"]["pooled"] = {"beta": round(float(np.polyfit(a3.x, a3.y, 1)[0]), 4), "corr": round(float(a3.x.corr(a3.y)), 3), "n": int(len(a3))}
            # EM with DM-sized costs, to show what the spread costs
            r2, _, _ = backtest(weights_from_signal(signal_matrix(P, bm, bk), bs, 3), P["xr"], 0.0002, bh)
            out["best"]["at_2bp"] = stats(r2.loc[START:])
        results[universe] = out
        pd.concat([r.rename(f"{universe}_best_net"), r_def.rename(f"{universe}_default_net")], axis=1).to_csv(OUT / f"equity_monthly_{universe}.csv")
        print(f"==== {universe} ==== best by train: {best}")
        print("  full", out["best"]["full"]); print("  train", out["best"]["train"]); print("  test", out["best"]["test"])
        print("  default local/6/tercile full", out["default_local_6_tercile"]["full"]["sharpe"], "train", out["default_local_6_tercile"]["train"]["sharpe"], "test", out["default_local_6_tercile"]["test"]["sharpe"])
        print("  placebo", out["best"]["placebo"], " fxmom same spec", out["best"]["fx_momentum_same_spec"].get("sharpe"), " spot-only", out["best"]["spot_only"].get("sharpe"), " skip", out["best"]["skip_month"].get("sharpe"), " risk-on", out["best"]["risk_on_only"].get("sharpe"))
        print("  pooled", pooled, "contemp", contemp)
        print("  sub", {k_: v.get("sharpe") for k_, v in out["best"]["sub"].items()})
        print("  ts variants", ts)
        print("  grid top 8 by train:"); print(grid_df.sort_values("sharpe_train", ascending=False).head(8).to_string())
        print("  grid summary by measure (mean train/test):"); print(grid_df.groupby("measure")[["sharpe_train", "sharpe_test", "sharpe_full"]].mean().round(2).to_string())
        print("  grid summary by k:"); print(grid_df.groupby("k")[["sharpe_train", "sharpe_test", "sharpe_full"]].mean().round(2).to_string())
        print("  grid summary by scheme/hold:"); print(grid_df.groupby(["scheme", "hold"])[["sharpe_train", "sharpe_test", "sharpe_full"]].mean().round(2).to_string())
        print("  risk", {k_: v for k_, v in risk.items() if k_ not in ("worst_months", "annual")}); print("  worst", risk["worst_months"]); print("  annual", risk["annual"]); print("  current", current)
        if universe == "EM":
            print("  regime float", out["regime_float"]); print("  regime managed", out["regime_managed"]); print("  at 2bp", out["best"]["at_2bp"])

    (OUT / "equity_results.json").write_text(json.dumps(results, indent=2, default=str))
    print("wrote", OUT / "equity_results.json")


if __name__ == "__main__":
    main()
