#!/usr/bin/env python3
"""MFE 230GB — FX Value in G10: real-exchange-rate deviation (CPI) and Big Mac misvaluation, with a funding-currency filter.

Run from anywhere:
    python project/code/run_value.py      # writes output/value_results.json, output/value_monthly.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

G10 = {
    "EUR": {"fx": "DEXUSEU", "invert": False, "rate": "IR3TIB01EZM156N", "bigmac": "EUR"},
    "JPY": {"fx": "DEXJPUS", "invert": True, "rate": "IR3TIB01JPM156N", "bigmac": "JPY"},
    "GBP": {"fx": "DEXUSUK", "invert": False, "rate": "IR3TIB01GBM156N", "bigmac": "GBP"},
    "AUD": {"fx": "DEXUSAL", "invert": False, "rate": "IR3TIB01AUM156N", "bigmac": "AUD"},
    "CAD": {"fx": "DEXCAUS", "invert": True, "rate": "IR3TIB01CAM156N", "bigmac": "CAD"},
    "CHF": {"fx": "DEXSZUS", "invert": True, "rate": "IR3TIB01CHM156N", "bigmac": "CHF"},
    "SEK": {"fx": "DEXSDUS", "invert": True, "rate": "IR3TIB01SEM156N", "bigmac": "SEK"},
    "NOK": {"fx": "DEXNOUS", "invert": True, "rate": "IR3TIB01NOM156N", "bigmac": "NOK"},
    "NZD": {"fx": "DEXUSNZ", "invert": False, "rate": "IR3TIB01NZM156N", "bigmac": "NZD"},
}
LOOKBACK = 60          # months of real-exchange-rate history that define "fair"
N_LEG = 3              # long 3 / short 3
HALF_SPREAD = 0.0002   # 2 bp per unit of turnover
CPI_LAG = 1            # months: CPI for month t is known in month t+1
START = "2004-01-31"   # first month with all nine currencies and five years of RER history


def load_fred(name: str) -> pd.Series:
    df = pd.read_csv(DATA / f"{name}.csv")
    dc = "observation_date" if "observation_date" in df.columns else df.columns[0]
    vc = [c for c in df.columns if c != dc][0]
    s = pd.to_numeric(df.set_index(pd.to_datetime(df[dc]))[vc], errors="coerce")
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.replace(0, np.nan)


def load_cpi(ccy: str) -> pd.Series:
    """Monthly CPI index, month-end stamped. Quarterly series are placed at quarter end and carried forward.
    Extended past the last print by trailing 12-month inflation so the signal exists to the latest spot date."""
    df = pd.read_csv(DATA / f"CPI_{ccy}.csv")
    per = df["period"].astype(str)
    if per.str.contains("Q").any():
        idx = pd.PeriodIndex(per, freq="Q").to_timestamp(how="end").normalize()
    else:
        idx = pd.PeriodIndex(per, freq="M").to_timestamp(how="end").normalize()
    s = pd.Series(pd.to_numeric(df["cpi"], errors="coerce").values, index=idx).dropna()
    s = s.resample("ME").last().ffill()
    # extend to Oct 2026 with trailing 12m inflation
    end = pd.Timestamp("2026-10-31")
    if s.index[-1] < end:
        g = (s.iloc[-1] / s.iloc[-13]) ** (1 / 12)
        ext_idx = pd.date_range(s.index[-1] + pd.offsets.MonthEnd(1), end, freq="ME")
        ext = pd.Series([s.iloc[-1] * g ** (k + 1) for k in range(len(ext_idx))], index=ext_idx)
        s = pd.concat([s, ext])
    return s


def stats(r: pd.Series, ann: int = 12) -> dict:
    r = r.dropna()
    if r.empty:
        return {}
    mu = float(r.mean() * ann)
    vol = float(r.std() * np.sqrt(ann))
    wealth = (1 + r).cumprod()
    mdd = float((wealth / wealth.cummax() - 1).min())
    return {
        "n": int(len(r)), "start": str(r.index.min().date()), "end": str(r.index.max().date()),
        "mean": round(mu, 4), "vol": round(vol, 4), "sharpe": round(mu / vol, 3) if vol else None,
        "mdd": round(mdd, 4), "hit": round(float((r > 0).mean()), 3), "cum": round(float(wealth.iloc[-1] - 1), 4),
        "skew": round(float(r.skew()), 2),
    }


def equity(r: pd.Series) -> pd.Series:
    return (1 + r.fillna(0)).cumprod() - 1


def series_xy(s: pd.Series, n: int = 500) -> list:
    s = s.dropna()
    if len(s) > n:
        s = s.iloc[:: max(1, len(s) // n)]
    return [{"date": str(d.date()), "v": round(float(x), 6)} for d, x in s.items()]


def rank_weights(sig: pd.DataFrame, n_leg: int = N_LEG) -> pd.DataFrame:
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for dt, row in sig.iterrows():
        s = row.dropna()
        if len(s) < 2 * n_leg:
            continue
        ranked = s.sort_values()
        w.loc[dt, ranked.index[:n_leg]] = -1.0 / n_leg
        w.loc[dt, ranked.index[-n_leg:]] = 1.0 / n_leg
    return w


def backtest(weights: pd.DataFrame, xr: pd.DataFrame, half_spread: float = HALF_SPREAD) -> tuple[pd.Series, pd.Series]:
    w = weights.fillna(0)
    turnover = w.diff().abs().sum(axis=1)
    gross = (w.shift(1) * xr).sum(axis=1)
    return gross - half_spread * turnover, turnover


def trap_filter(sig: pd.DataFrame, carry: pd.DataFrame, k: int = 2) -> pd.DataFrame:
    """Funding-currency filter (Topic 3): never long a cheap currency that is among the k lowest-carry
    currencies, never short an expensive currency that is among the k highest-carry. The misvaluation of a
    funding currency closes only when its rate gap closes, so value alone walks into the trap."""
    out = sig.copy()
    for dt, row in sig.iterrows():
        cr = carry.loc[dt].dropna() if dt in carry.index else pd.Series(dtype=float)
        if len(cr) < 6:
            continue
        for c in cr.nsmallest(k).index:
            if pd.notna(row.get(c)) and row[c] > 0:
                out.loc[dt, c] = np.nan
        for c in cr.nlargest(k).index:
            if pd.notna(row.get(c)) and row[c] < 0:
                out.loc[dt, c] = np.nan
    return out


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)


def main():
    # ---------------- monthly panel ----------------
    spot = {}
    for c, spec in G10.items():
        s = load_fred(spec["fx"])
        if spec["invert"]:
            s = 1 / s
        spot[c] = np.log(s).resample("ME").last()          # log USD per unit of foreign currency
    logS = pd.DataFrame(spot)
    cpi_us = np.log(load_cpi("USD"))
    rer = pd.DataFrame({c: logS[c] + np.log(load_cpi(c)).reindex(logS.index) - cpi_us.reindex(logS.index) for c in G10})
    rer_known = rer.shift(CPI_LAG)                           # CPI publication lag
    fair = rer_known.rolling(LOOKBACK, min_periods=36).mean()
    sig_cpi = -(rer_known - fair)                            # positive = undervalued vs its own 5-year history

    i_us = load_fred("IR3TIB01USM156N").resample("ME").last().ffill() / 100
    i_us = i_us.reindex(logS.index).ffill(limit=12)
    carry = pd.DataFrame({c: (load_fred(spec["rate"]).resample("ME").last().ffill() / 100).reindex(logS.index).ffill(limit=12) - i_us for c, spec in G10.items()})  # monthly OECD rates carried to the latest spot month
    xr = logS.diff() + carry.shift(1) / 12                   # monthly excess return of long FC vs USD

    bm = pd.read_csv(DATA / "bigmac_full_index.csv", parse_dates=["date"])
    bm = bm[bm["currency_code"].isin([spec["bigmac"] for spec in G10.values()])]
    bm_raw = bm.pivot_table(index="date", columns="currency_code", values="USD_raw")
    bm_adj = bm.pivot_table(index="date", columns="currency_code", values="USD_adjusted")   # GDP-adjusted (Balassa-Samuelson)
    for p in (bm_raw, bm_adj):
        p.index = p.index + pd.offsets.MonthEnd(0)
    sig_bm = -bm_adj.reindex(logS.index).ffill()             # positive = undervalued; held until the next release
    sig_bm_raw = -bm_raw.reindex(logS.index).ffill()

    sig_two = (zscore(sig_cpi) + zscore(sig_bm)) / 2         # two measures of the same thing
    sig_book = trap_filter(sig_two, carry, 2)                # plus the funding-currency filter

    def run(sig, start=START, n_leg=N_LEG, spread=HALF_SPREAD):
        w = rank_weights(sig, n_leg)
        r, to = backtest(w, xr, spread)
        return r.loc[start:], to.loc[start:], w.loc[start:]

    layers = {}
    r_cpi, to_cpi, w_cpi = run(sig_cpi)
    r_bm, to_bm, w_bm = run(sig_bm)
    r_two, to_two, w_two = run(sig_two)
    book, to_book, w_book = run(sig_book)
    r_carry, to_carry, w_carry = run(carry)
    r_cpi_trap, _, _ = run(trap_filter(sig_cpi, carry, 2))
    layers["cpi_value"] = stats(r_cpi); layers["cpi_value"]["turnover_per_year"] = round(float(to_cpi.mean() * 12), 2)
    layers["bigmac_value"] = stats(r_bm); layers["bigmac_value"]["turnover_per_year"] = round(float(to_bm.mean() * 12), 2)
    layers["two_measure_value"] = stats(r_two); layers["two_measure_value"]["turnover_per_year"] = round(float(to_two.mean() * 12), 2)
    layers["book"] = stats(book); layers["book"]["turnover_per_year"] = round(float(to_book.mean() * 12), 2)
    layers["book_gross"] = stats(book + HALF_SPREAD * to_book)
    layers["cpi_value_with_filter"] = stats(r_cpi_trap)
    layers["carry_rank_book"] = stats(r_carry)

    # ---------------- sub-periods ----------------
    sub = {}
    for a, b in [("2004", "2012"), ("2013", "2019"), ("2020", "2026"), ("2004", "2014"), ("2015", "2026")]:
        sub[f"{a}-{b}"] = {"cpi_value": stats(r_cpi.loc[a:b]), "two_measure": stats(r_two.loc[a:b]), "book": stats(book.loc[a:b]), "carry_rank": stats(r_carry.loc[a:b])}

    # ---------------- robustness of the book ----------------
    rob = {}
    for k in (1, 2, 3):
        r, _, _ = run(trap_filter(sig_two, carry, k)); rob[f"filter_k{k}"] = stats(r)
    for lb in (36, 60, 120):
        f = rer_known.rolling(lb, min_periods=min(36, lb)).mean()
        s = trap_filter((zscore(-(rer_known - f)) + zscore(sig_bm)) / 2, carry, 2)
        r, _, _ = run(s, start="2004-01-31" if lb <= 60 else "2009-01-31"); rob[f"cpi_lookback_{lb}m"] = stats(r)
    r, _, _ = run(trap_filter((zscore(sig_cpi) + zscore(sig_bm_raw)) / 2, carry, 2)); rob["bigmac_raw_not_adjusted"] = stats(r)
    r, _, _ = run(trap_filter((zscore(-(rer_known - rer_known.shift(60))) + zscore(sig_bm)) / 2, carry, 2)); rob["cpi_five_year_change"] = stats(r)
    r, _, _ = run(sig_book, n_leg=2); rob["long2_short2"] = stats(r)
    r, _, _ = run(sig_book, spread=0.0010); rob["cost_10bp"] = stats(r)
    w = rank_weights(sig_book)
    r_spot = (w.shift(1) * logS.diff()).sum(axis=1) - HALF_SPREAD * w.diff().abs().sum(axis=1)
    rob["spot_only_no_carry"] = stats(r_spot.loc[START:])
    sq = sig_book.copy(); sq[~sq.index.month.isin([3, 6, 9, 12])] = np.nan; sq = sq.ffill()
    r, to, _ = run(sq); rob["quarterly_rebalance"] = stats(r); rob["quarterly_rebalance"]["turnover_per_year"] = round(float(to.mean() * 12), 2)
    rng = np.random.default_rng(0)
    sh = []
    sig_v = sig_book.loc[START:]
    for _ in range(500):
        p = sig_v.apply(lambda row: pd.Series(rng.permutation(row.values), index=row.index), axis=1)
        wp = rank_weights(p)
        rp = (wp.shift(1) * xr.loc[START:]).sum(axis=1) - HALF_SPREAD * wp.diff().abs().sum(axis=1)
        sh.append(stats(rp)["sharpe"])
    sh = np.array([x for x in sh if x is not None])
    rob["placebo_shuffle_cross_section"] = {"mean": round(float(sh.mean()), 3), "p95": round(float(np.percentile(sh, 95)), 3),
                                            "pval": round(float((sh >= stats(book)["sharpe"]).mean()), 3)}
    sig8 = sig_cpi.drop(columns=["EUR"])
    w8 = rank_weights(trap_filter(sig8, carry.drop(columns=["EUR"]), 2))
    r8 = (w8.shift(1) * logS.drop(columns=["EUR"]).diff()).sum(axis=1) - HALF_SPREAD * w8.diff().abs().sum(axis=1)
    rob["long_sample_cpi_value_filter_spot_1980_2003"] = stats(r8.loc["1980-01-31":"2003-12-31"])
    w8p = rank_weights(sig8)
    r8p = (w8p.shift(1) * logS.drop(columns=["EUR"]).diff()).sum(axis=1) - HALF_SPREAD * w8p.diff().abs().sum(axis=1)
    rob["long_sample_cpi_value_plain_spot_1980_2003"] = stats(r8p.loc["1980-01-31":"2003-12-31"])

    # ---------------- risk ----------------
    vix = load_fred("VIXCLS").resample("ME").mean()
    usd = np.log(load_fred("DTWEXBGS")).diff().resample("ME").sum(min_count=1)
    hml_df = pd.read_excel(DATA / "CurrencyPortfolios.xls", sheet_name="Developed currencies (net)", header=0)
    hml_df = hml_df.rename(columns={hml_df.columns[0]: "date"})
    hml = pd.to_numeric(hml_df.set_index(pd.to_datetime(hml_df["date"]))["HML = P5 - P1"], errors="coerce")
    hml.index = hml.index.to_period("M").to_timestamp("M")

    risk = {}
    a = pd.concat([book.rename("v"), r_cpi.rename("plain"), vix.rename("vix"), usd.rename("usd"), hml.rename("hml"), r_carry.rename("carry")], axis=1).loc[START:]
    q = a["vix"].quantile(0.8)
    risk["high_vix_months"] = stats(a.loc[a.vix >= q, "v"]); risk["low_vix_months"] = stats(a.loc[a.vix < q, "v"])
    ab = a.dropna(subset=["usd", "v"])
    risk["corr_usd"] = round(float(ab["v"].corr(ab["usd"])), 3); risk["beta_usd"] = round(float(np.polyfit(ab["usd"], ab["v"], 1)[0]), 3)
    risk["corr_hml"] = round(float(a["v"].corr(a["hml"])), 3); risk["corr_carry_rank_book"] = round(float(a["v"].corr(a["carry"])), 3)
    hb = a.dropna(subset=["hml"]); wc = hb.nsmallest(int(len(hb) * 0.1), "hml")
    risk["book_in_worst_carry_decile"] = {"n": int(len(wc)), "book_mean_pct": round(float(wc["v"].mean() * 100), 2), "plain_value_mean_pct": round(float(wc["plain"].mean() * 100), 2),
                                          "hml_mean_pct": round(float(wc["hml"].mean() * 100), 2), "book_other_months_pct": round(float(hb.drop(wc.index)["v"].mean() * 100), 2)}
    cb = a.dropna(subset=["carry"]); wcb = cb.nsmallest(int(len(cb) * 0.1), "carry")
    risk["book_in_worst_carry_rank_decile"] = {"n": int(len(wcb)), "book_mean_pct": round(float(wcb["v"].mean() * 100), 2), "carry_mean_pct": round(float(wcb["carry"].mean() * 100), 2)}
    us = a.nlargest(int(len(a) * 0.1), "usd"); risk["book_in_dollar_surge_decile"] = {"n": int(len(us)), "book_mean_pct": round(float(us["v"].mean() * 100), 2)}
    wealth = (1 + book.fillna(0)).cumprod(); dd = wealth / wealth.cummax() - 1
    risk["mdd"] = {"trough": str(dd.idxmin().date()), "dd": round(float(dd.min()), 3), "peak": str(wealth.loc[:dd.idxmin()].idxmax().date())}
    under = (dd < 0).astype(int); cur, best, best_end = 0, 0, None
    for d, u in under.items():
        cur = cur + 1 if u else 0
        if cur > best: best, best_end = cur, d
    risk["longest_underwater_months"] = {"months": int(best), "end": str(best_end.date()) if best_end is not None else None}
    risk["worst_months"] = [{"date": str(d.date()), "ret": round(float(v) * 100, 2), "longs": [c for c in G10 if w_book.shift(1).loc[d, c] > 0],
                             "shorts": [c for c in G10 if w_book.shift(1).loc[d, c] < 0], "usd": round(float(usd.get(d, np.nan)) * 100, 2),
                             "vix": round(float(vix.get(d, np.nan)), 1)} for d, v in book.nsmallest(6).items()]
    risk["best_months"] = [{"date": str(d.date()), "ret": round(float(v) * 100, 2)} for d, v in book.nlargest(4).items()]
    risk["long_freq"] = {c: round(float((w_book[c] > 0).mean()), 2) for c in G10}
    risk["short_freq"] = {c: round(float((w_book[c] < 0).mean()), 2) for c in G10}
    risk["filtered_out_freq"] = {c: round(float(((sig_two.loc[START:, c].notna()) & (sig_book.loc[START:, c].isna())).mean()), 2) for c in G10}
    contrib = (w_book.shift(1) * xr.loc[START:]).sum(); risk["contrib_pct"] = {c: round(float(contrib[c]) * 100, 1) for c in G10}
    contrib_p = (w_cpi.shift(1) * xr.loc[START:]).sum(); risk["plain_contrib_pct"] = {c: round(float(contrib_p[c]) * 100, 1) for c in G10}
    risk["jpy_plain_since_2021"] = {"months_long": int((w_cpi["JPY"] > 0).loc["2021":].sum()), "of": int(len(w_cpi.loc["2021":])), "pnl_pct": round(float((w_cpi["JPY"].shift(1) * xr["JPY"]).loc["2021":].sum() * 100), 1)}
    risk["jpy_book_since_2021"] = {"months_long": int((w_book["JPY"] > 0).loc["2021":].sum()), "pnl_pct": round(float((w_book["JPY"].shift(1) * xr["JPY"]).loc["2021":].sum() * 100), 1)}
    risk["annual_book"] = {int(y): round(float(v) * 100, 1) for y, v in book.groupby(book.index.year).sum().items()}
    risk["annual_plain"] = {int(y): round(float(v) * 100, 1) for y, v in r_cpi.groupby(r_cpi.index.year).sum().items()}
    risk["turnover_per_year"] = round(float(to_book.mean() * 12), 2); risk["cost_per_year_bp"] = round(float(to_book.mean() * 12 * HALF_SPREAD * 1e4), 1)
    pos = book[book > 0].sort_values(ascending=False); risk["top5pct_share"] = round(float(pos.head(max(1, int(len(pos) * 0.05))).sum() / pos.sum()), 3)
    risk["avg_holding_months"] = round(float(1 / max(to_book.mean() / 2, 1e-9) * (1.0)), 1)   # gross one-side turnover per month -> months per full rotation

    # ---------------- Big Mac detail ----------------
    agree = []
    for d in bm_adj.index:
        if d in sig_cpi.index:
            a_ = pd.concat([(-bm_adj.loc[d]).rename("bm"), sig_cpi.loc[d].rename("cpi")], axis=1).dropna()
            if len(a_) >= 6: agree.append(a_["bm"].rank().corr(a_["cpi"].rank()))
    bigmac = {"releases": int(bm_adj.shape[0]), "first": str(bm_adj.index[0].date()), "latest_date": str(bm_adj.index[-1].date()),
              "latest_adjusted": {c: round(float(v), 3) for c, v in bm_adj.iloc[-1].dropna().sort_values().items()},
              "latest_raw": {c: round(float(v), 3) for c, v in bm_raw.iloc[-1].dropna().sort_values().items()},
              "rank_corr_with_cpi_value_mean": round(float(np.nanmean(agree)), 3),
              "stats_2000": stats(run(sig_bm, start="2000-05-31")[0]), "stats_raw_2000": stats(run(sig_bm_raw, start="2000-05-31")[0])}

    # ---------------- current snapshot ----------------
    last = sig_book.dropna(how="all").index[-1]
    current = {"date": str(last.date()),
               "cpi_dev_pct": {c: round(float(-sig_cpi.loc[last, c]) * 100, 1) for c in G10 if pd.notna(sig_cpi.loc[last, c])},
               "bigmac_adj_pct": {c: round(float(-sig_bm.loc[last, c]) * 100, 1) for c in G10 if pd.notna(sig_bm.loc[last, c])},
               "carry_pct": {c: round(float(carry.loc[last, c]) * 100, 2) for c in G10 if pd.notna(carry.loc[last, c])},
               "score": {c: round(float(sig_two.loc[last, c]), 2) for c in G10 if pd.notna(sig_two.loc[last, c])},
               "filtered_out": [c for c in G10 if pd.notna(sig_two.loc[last, c]) and pd.isna(sig_book.loc[last, c])],
               "longs": [c for c in G10 if w_book.loc[last, c] > 0], "shorts": [c for c in G10 if w_book.loc[last, c] < 0]}

    payload = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "spec": {"lookback_months": LOOKBACK, "n_leg": N_LEG, "half_spread": HALF_SPREAD, "cpi_lag_months": CPI_LAG, "start": START, "filter_k": 2,
                 "cpi_last_print": {c: str(pd.read_csv(DATA / f"CPI_{c}.csv")["period"].iloc[-1]) for c in list(G10) + ["USD"]}},
        "layers": layers, "sub": sub, "robustness": rob, "risk": risk, "bigmac": bigmac, "current": current,
        "hml_same_window": stats(hml.loc[START:"2021-05-31"]),
        "equity_cpi": series_xy(equity(r_cpi)), "equity_two": series_xy(equity(r_two)), "equity_book": series_xy(equity(book)),
        "equity_carry_rank": series_xy(equity(r_carry)), "equity_bigmac": series_xy(equity(r_bm)),
        "dev_jpy": series_xy((-sig_cpi["JPY"] * 100).loc[START:]), "dev_chf": series_xy((-sig_cpi["CHF"] * 100).loc[START:]),
        "dev_aud": series_xy((-sig_cpi["AUD"] * 100).loc[START:]), "dev_gbp": series_xy((-sig_cpi["GBP"] * 100).loc[START:]),
    }
    (OUT / "value_results.json").write_text(json.dumps(payload, indent=2, default=str))
    pd.concat([book.rename("book_net"), r_cpi.rename("cpi_value_net"), r_two.rename("two_measure_net"), r_carry.rename("carry_rank_net"), to_book.rename("book_turnover")], axis=1).to_csv(OUT / "value_monthly.csv")
    w_book.to_csv(OUT / "value_weights.csv")
    print("layers", json.dumps(layers, indent=0))
    print("sub", json.dumps(sub, indent=0))
    print("rob", json.dumps(rob, indent=0))
    print("risk", json.dumps(risk, indent=0, default=str))
    print("bigmac", json.dumps(bigmac, indent=0))
    print("current", json.dumps(current, indent=0))


if __name__ == "__main__":
    main()
