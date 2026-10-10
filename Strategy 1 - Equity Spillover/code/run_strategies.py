#!/usr/bin/env python3
"""MFE 230GB — replicate Policy Path (OECD) and Terms of Trade (EM).

Run from anywhere:
    python project/code/run_strategies.py
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


def load_fred(name: str) -> pd.Series:
    path = DATA / f"{name}.csv"
    df = pd.read_csv(path)
    date_col = "observation_date" if "observation_date" in df.columns else df.columns[0]
    val_col = [c for c in df.columns if c != date_col][0]
    s = pd.to_numeric(df.set_index(pd.to_datetime(df[date_col]))[val_col], errors="coerce")
    s.name = name
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.replace(0, np.nan)


def fx_return(name: str, invert: bool) -> pd.Series:
    s = load_fred(name)
    r = np.log(s).diff()
    if invert:
        r = -r
    return r


def stats(r: pd.Series, ann: int = 52) -> dict:
    r = r.dropna()
    if r.empty:
        return {}
    mu = float(r.mean() * ann)
    vol = float(r.std() * np.sqrt(ann))
    sharpe = mu / vol if vol else float("nan")
    wealth = (1 + r).cumprod()
    mdd = float((wealth / wealth.cummax() - 1).min())
    active = r[r.abs() > 1e-12]
    return {
        "n": int(len(r)),
        "n_active": int(len(active)),
        "pct_active": round(float((r.abs() > 1e-12).mean()), 3),
        "start": str(r.index.min().date()),
        "end": str(r.index.max().date()),
        "mean": round(mu, 4),
        "vol": round(vol, 4),
        "sharpe": round(sharpe, 3),
        "mdd": round(mdd, 4),
        "hit": round(float((r > 0).mean()), 3),
        "hit_active": round(float((active > 0).mean()), 3) if len(active) else None,
        "cum": round(float(wealth.iloc[-1] - 1), 4),
    }


def equity(r: pd.Series) -> pd.Series:
    return (1 + r.fillna(0)).cumprod() - 1


def apply_costs(weights: pd.DataFrame, rets: pd.DataFrame, half_spread: float) -> pd.Series:
    """Gross portfolio return minus half-spread * turnover."""
    w = weights.fillna(0)
    turnover = w.diff().abs().sum(axis=1)
    gross = (w.shift(1) * rets).sum(axis=1)
    return gross - half_spread * turnover


def vol_target(r: pd.Series, target_ann: float, ann: int, look: int = 26) -> pd.Series:
    trailing = r.rolling(look).std() * np.sqrt(ann)
    scale = (target_ann / trailing).clip(upper=3.0)
    return (r * scale.shift(1)).replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------------------
# Strategy 1: G10 Policy Path
# ---------------------------------------------------------------------------
G10 = {
    "EUR": {"fx": "DEXUSEU", "invert": False, "rate": "IR3TIB01EZM156N"},
    "JPY": {"fx": "DEXJPUS", "invert": True, "rate": "IR3TIB01JPM156N"},
    "GBP": {"fx": "DEXUSUK", "invert": False, "rate": "IR3TIB01GBM156N"},
    "AUD": {"fx": "DEXUSAL", "invert": False, "rate": "IR3TIB01AUM156N"},
    "CAD": {"fx": "DEXCAUS", "invert": True, "rate": "IR3TIB01CAM156N"},
    "CHF": {"fx": "DEXSZUS", "invert": True, "rate": "IR3TIB01CHM156N"},
    "SEK": {"fx": "DEXSDUS", "invert": True, "rate": "IR3TIB01SEM156N"},
    "NOK": {"fx": "DEXNOUS", "invert": True, "rate": "IR3TIB01NOM156N"},
    "NZD": {"fx": "DEXUSNZ", "invert": False, "rate": "IR3TIB01NZM156N"},
}


def build_g10_weekly() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    fx_d = pd.DataFrame({c: fx_return(spec["fx"], spec["invert"]) for c, spec in G10.items()})
    i_us = load_fred("IR3TIB01USM156N") / 100.0
    carry_d = {}
    for c, spec in G10.items():
        i_f = load_fred(spec["rate"]) / 100.0
        # daily carry accrual from monthly rates
        carry_d[c] = (i_f.reindex(fx_d.index).ffill() - i_us.reindex(fx_d.index).ffill()) / 365.0
    carry_d = pd.DataFrame(carry_d)
    xr_d = fx_d + carry_d  # excess return of long FC vs USD

    wk_xr = xr_d.resample("W-FRI").sum(min_count=1)
    wk_fx = fx_d.resample("W-FRI").sum(min_count=1)
    # annualised 13-week carry and vol from daily
    i_diff = {}
    for c, spec in G10.items():
        i_f = load_fred(spec["rate"]) / 100.0
        i_diff[c] = i_f.reindex(i_us.index).ffill() - i_us
    i_diff = pd.DataFrame(i_diff).resample("W-FRI").last().ffill(limit=5)  # monthly OECD rates carried across the weeks of the month
    vol = wk_fx.rolling(13).std() * np.sqrt(52)
    ctv = (i_diff / vol.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)

    vix = load_fred("VIXCLS").resample("W-FRI").last()
    dgs2 = load_fred("DGS2").resample("W-FRI").last()
    dgs10 = load_fred("DGS10").resample("W-FRI").last()
    return wk_xr, ctv, vix, dgs2, dgs10


def g10_weights(ctv: pd.DataFrame, n_long: int = 3) -> pd.DataFrame:
    """Long top n, short bottom n, equal |weight| summing to 1 gross each side."""
    w = pd.DataFrame(0.0, index=ctv.index, columns=ctv.columns)
    for dt, row in ctv.iterrows():
        s = row.dropna()
        if len(s) < 2 * n_long:
            continue
        ranked = s.sort_values()
        shorts = ranked.iloc[:n_long].index
        longs = ranked.iloc[-n_long:].index
        w.loc[dt, longs] = 1.0 / n_long
        w.loc[dt, shorts] = -1.0 / n_long
    return w


def strategy1(wk_xr, ctv, vix, dgs2, dgs10):
    w = g10_weights(ctv)
    raw = apply_costs(w, wk_xr, half_spread=0.0002)

    # VIX filter: skip top quintile of expanding window (min 5y)
    vix_q = vix.expanding(min_periods=52 * 5).quantile(0.80)
    risk_on = (vix < vix_q).astype(float)
    filt = raw * risk_on.reindex(raw.index).ffill()

    # Policy overlay from 2y (proxy when PM is missing): dovish = 2y down
    d2 = dgs2.diff()
    overlay = pd.Series(0.0, index=wk_xr.index)
    # long EUR+JPY vs USD when 2s rally more than 15 bp
    pair = wk_xr[["EUR", "JPY"]].mean(axis=1)
    overlay = overlay + pair.where(d2.shift(1) <= -0.15, 0.0)
    overlay = overlay - pair.where(d2.shift(1) >= 0.15, 0.0)
    # duration sleeve: long bonds when 2s rally (approx 7y duration)
    bond = (-7.0 * dgs10.diff() / 100.0).reindex(wk_xr.index)
    overlay = overlay + bond.where(d2.shift(1) <= -0.15, 0.0) * 0.5

    combined = filt + overlay.reindex(filt.index).fillna(0.0)
    vt = vol_target(combined, 0.10, 52)

    # costs already in raw/filt; overlay roughly 2 bp when on
    return {
        "raw": raw,
        "vix_filter": filt,
        "combined": combined,
        "vol_target": vt,
        "weights": w,
        "risk_on": risk_on,
        "overlay": overlay,
    }


# ---------------------------------------------------------------------------
# Strategy 2: EM terms of trade
# ---------------------------------------------------------------------------
EM = {
    "BRL": {"fx": "DEXBZUS", "invert": True},
    "MXN": {"fx": "DEXMXUS", "invert": True},  # OECD; used only in beta chart
    "ZAR": {"fx": "DEXSFUS", "invert": True},
    "INR": {"fx": "DEXINUS", "invert": True},
    "THB": {"fx": "DEXTHUS", "invert": True},
    "CNY": {"fx": "DEXCHUS", "invert": True},
    "KRW": {"fx": "DEXKOUS", "invert": True},  # OECD; beta chart only
    "JPY": {"fx": "DEXJPUS", "invert": True},
    "EUR": {"fx": "DEXUSEU", "invert": False},
}
EM_TRADE = ["BRL", "ZAR", "INR", "THB", "CNY"]


def strategy2():
    fx = pd.DataFrame({c: fx_return(spec["fx"], spec["invert"]) for c, spec in EM.items()})
    oil = np.log(load_fred("DCOILBRENTEU")).diff()
    usd = np.log(load_fred("DTWEXBGS")).diff()
    wk = pd.concat(
        [fx.resample("W-FRI").sum(min_count=1),
         oil.resample("W-FRI").sum(min_count=1).rename("OIL"),
         usd.resample("W-FRI").sum(min_count=1).rename("USD")],
        axis=1,
    )
    train = wk.loc["2010-01-01":"2019-12-31"].dropna(subset=["OIL", "USD"])
    betas = {}
    for c in EM:
        sub = train[[c, "OIL", "USD"]].dropna()
        y = sub[c].values
        X = np.column_stack([np.ones(len(sub)), sub["OIL"].values, sub["USD"].values])
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        betas[c] = {"oil": float(b[1]), "usd": float(b[2]), "corr": float(sub[c].corr(sub["OIL"]))}

    ranked = sorted(EM_TRADE, key=lambda c: betas[c]["oil"], reverse=True)
    longs, shorts = ranked[:2], ranked[-2:]

    ls = wk[longs].mean(axis=1) - wk[shorts].mean(axis=1)
    oil_lag = wk["OIL"].shift(1)
    sign_all = np.sign(oil_lag).replace(0, np.nan)
    # Shock rule: only stand on the ToT move when last week's oil move is large
    sign_shock = np.sign(oil_lag).where(oil_lag.abs() >= 0.02, 0.0)
    timed = ls * sign_all
    shock = ls * sign_shock

    def net_of_ndf(pos: pd.Series, rt: pd.Series, spread: float = 0.0015) -> pd.Series:
        turnover = pos.diff().abs().fillna(pos.abs())
        return rt - spread * turnover

    timed_net = net_of_ndf(sign_all.fillna(0), timed)
    shock_net = net_of_ndf(sign_shock.fillna(0), shock)
    always_net = ls  # static book: entry cost amortised, not recharged weekly
    vt = vol_target(shock_net, 0.12, 52)

    # Monthly holding period: one NDF roll a month, which is how this book would actually trade
    ls_m = ls.resample("ME").sum()
    oil_m = wk["OIL"].resample("ME").sum()
    sign_m = np.sign(oil_m.shift(1)).replace(0, np.nan)
    timed_m = ls_m * sign_m
    timed_m_net = timed_m - 0.0015 * sign_m.diff().abs().fillna(sign_m.abs())

    return {
        "wk": wk,
        "betas": betas,
        "longs": longs,
        "shorts": shorts,
        "always": ls,
        "timed": timed,
        "timed_net": timed_net,
        "shock": shock,
        "shock_net": shock_net,
        "always_net": always_net,
        "vol_target": vt,
        "timed_m": timed_m,
        "timed_m_net": timed_m_net,
    }


# ---------------------------------------------------------------------------
# Lustig developed carry (net) + VIX split
# ---------------------------------------------------------------------------
def lustig_developed():
    df = pd.read_excel(DATA / "CurrencyPortfolios.xls", sheet_name="Developed currencies (net)", header=0)
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"])
    hml = pd.to_numeric(df.set_index("date")["HML = P5 - P1"], errors="coerce")
    vix = load_fred("VIXCLS").resample("ME").mean()
    h = hml.copy()
    h.index = h.index.to_period("M").to_timestamp("M")
    vix.index = vix.index.to_period("M").to_timestamp("M")
    a = pd.concat([h.rename("hml"), vix.rename("vix")], axis=1, join="inner")
    hi = a.loc[a["vix"] >= a["vix"].median(), "hml"]
    lo = a.loc[a["vix"] < a["vix"].median(), "hml"]
    q80 = a["vix"].quantile(0.8)
    skip = a["hml"].where(a["vix"] < q80, 0.0)
    return {
        "hml": hml,
        "full": stats(hml, 12),
        "since2010": stats(hml.loc["2010":], 12),
        "high_vix": stats(hi, 12),
        "low_vix": stats(lo, 12),
        "skip_top20": stats(skip, 12),
        "raw_aligned": stats(a["hml"], 12),
        "worst": [
            {"date": str(d.date()), "ret": round(float(v), 4)}
            for d, v in hml.nsmallest(5).items()
        ],
        "equity": [
            {"date": str(d.date()), "cum": round(float(x), 4)}
            for d, x in equity(hml).resample("ME").last().dropna().items()
        ],
    }


# ---------------------------------------------------------------------------
# Polymarket: P(cut) for the nearest meeting
# ---------------------------------------------------------------------------
def polymarket_pcut() -> pd.Series:
    path = DATA / "polymarket_prices.json"
    if not path.exists():
        return pd.Series(dtype=float)
    blob = json.loads(path.read_text())
    frames = []
    for key, rec in blob.items():
        if rec.get("kind") not in ("cut25", "cut50"):
            continue
        pts = rec.get("history") or []
        if not pts:
            continue
        idx = pd.to_datetime([p["timestamp"] for p in pts], unit="s", utc=True).tz_convert(None)
        s = pd.Series([p["price"] for p in pts], index=idx, name=f"{rec['slug']}::{rec['kind']}")
        frames.append(s[~s.index.duplicated()].sort_index())
    if not frames:
        return pd.Series(dtype=float)
    df = pd.concat(frames, axis=1).sort_index()
    # P(cut) = cut25 + cut50 within each slug, then take mean across live meetings
    pcut = {}
    slugs = {k.split("::")[0] for k in df.columns}
    for slug in slugs:
        cols = [c for c in df.columns if c.startswith(slug)]
        pcut[slug] = df[cols].sum(axis=1, min_count=1)
    panel = pd.DataFrame(pcut)
    # average across contracts that are live (have a print that week)
    p = panel.mean(axis=1).resample("D").last().ffill()
    p.name = "pcut"
    return p


def lead_lag(x: pd.Series, y: pd.Series, lags=range(-4, 5)) -> list:
    out = []
    a = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    for k in lags:
        c = a["x"].corr(a["y"].shift(-k))  # corr(x_t, y_{t+k}); k>0 means x leads y
        out.append({"lag": int(k), "corr": None if pd.isna(c) else round(float(c), 3)})
    return out


def series_xy(s: pd.Series, n: int = 400) -> list:
    s = s.dropna()
    if len(s) > n:
        s = s.iloc[:: max(1, len(s) // n)]
    return [{"date": str(d.date()), "v": round(float(x), 6)} for d, x in s.items()]


def main():
    lustig = lustig_developed()
    wk_xr, ctv, vix, dgs2, dgs10 = build_g10_weekly()
    s1 = strategy1(wk_xr, ctv, vix, dgs2, dgs10)
    s2 = strategy2()
    pcut = polymarket_pcut()

    # PM overlay on the short sample: when weekly ΔP(cut) > 5pp, add EUR/JPY
    pcut_w = pcut.resample("W-FRI").last()
    dpcut = pcut_w.diff()
    pair = wk_xr[["EUR", "JPY"]].mean(axis=1)
    pm_overlay = pair.where(dpcut.shift(1) >= 0.05, 0.0) - pair.where(dpcut.shift(1) <= -0.05, 0.0)
    s1_pm = s1["vix_filter"].add(pm_overlay.reindex(s1["vix_filter"].index).fillna(0.0), fill_value=0.0)

    usd_wk = np.log(load_fred("DTWEXBGS")).diff().resample("W-FRI").sum(min_count=1)

    payload = {
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "lustig": {
            "full": lustig["full"],
            "since2010": lustig["since2010"],
            "high_vix": lustig["high_vix"],
            "low_vix": lustig["low_vix"],
            "skip_top20": lustig["skip_top20"],
            "raw_aligned": lustig["raw_aligned"],
            "worst": lustig["worst"],
            "equity": lustig["equity"],
        },
        "strategy1": {
            "raw": stats(s1["raw"].loc["2000":]),
            "vix_filter": stats(s1["vix_filter"].loc["2000":]),
            "combined": stats(s1["combined"].loc["2000":]),
            "vol_target": stats(s1["vol_target"].loc["2000":]),
            "oos": stats(s1["combined"].loc["2020":]),
            "pm_overlay": stats(s1_pm.loc["2025":]),
            "equity_raw": series_xy(equity(s1["raw"].loc["2000":])),
            "equity_filt": series_xy(equity(s1["vix_filter"].loc["2000":])),
            "equity_combined": series_xy(equity(s1["combined"].loc["2000":])),
            "leadlag_dgs2_usd": lead_lag(dgs2.diff().loc["2000":], -usd_wk.loc["2000":]),
            "leadlag_pcut_dgs2": lead_lag(dpcut, -dgs2.diff()) if not pcut.empty else [],
        },
        "strategy2": {
            "betas": {k: {"oil": round(v["oil"], 4), "usd": round(v["usd"], 3)} for k, v in s2["betas"].items()},
            "longs": s2["longs"],
            "shorts": s2["shorts"],
            "always": stats(s2["always"].loc["2010":]),
            "timed": stats(s2["timed"].loc["2010":]),
            "timed_net": stats(s2["timed_net"].loc["2010":]),
            "shock": stats(s2["shock"].loc["2010":]),
            "shock_net": stats(s2["shock_net"].loc["2010":]),
            "always_net": stats(s2["always_net"].loc["2010":]),
            "oos": stats(s2["shock"].loc["2020":]),
            "oos_net": stats(s2["shock_net"].loc["2020":]),
            "monthly": stats(s2["timed_m"].loc["2010":], 12),
            "monthly_net": stats(s2["timed_m_net"].loc["2010":], 12),
            "monthly_oos_net": stats(s2["timed_m_net"].loc["2020":], 12),
            "vol_target": stats(s2["vol_target"].loc["2010":]),
            "equity_monthly_net": series_xy(equity(s2["timed_m_net"].loc["2010":])),
            "equity_timed": series_xy(equity(s2["timed"].loc["2010":])),
            "equity_always": series_xy(equity(s2["always"].loc["2010":])),
            "equity_shock": series_xy(equity(s2["shock"].loc["2010":])),
            "equity_shock_net": series_xy(equity(s2["shock_net"].loc["2010":])),
            "leadlag_oil_ls": lead_lag(s2["wk"]["OIL"].loc["2010":], s2["always"].loc["2010":]),
            "crashes": [
                {"date": str(d.date()), "oil": round(float(s2["wk"].loc[d, "OIL"]), 3),
                 "BRL": round(float(s2["wk"].loc[d, "BRL"]), 3) if pd.notna(s2["wk"].loc[d, "BRL"]) else None,
                 "ZAR": round(float(s2["wk"].loc[d, "ZAR"]), 3) if pd.notna(s2["wk"].loc[d, "ZAR"]) else None}
                for d in s2["wk"].loc["2010":, "OIL"].nsmallest(5).index
            ],
        },
        "pm": {
            "pcut": series_xy(pcut, 500),
            "start": str(pcut.index.min().date()) if len(pcut) else None,
            "end": str(pcut.index.max().date()) if len(pcut) else None,
            "n": int(len(pcut.dropna())),
        },
    }

    (OUT / "results.json").write_text(json.dumps(payload, indent=2))
    s1["combined"].rename("s1_combined").to_csv(OUT / "s1_weekly.csv", header=True)
    s2["shock_net"].rename("s2_shock_net").to_csv(OUT / "s2_weekly.csv", header=True)
    print("Strategy 1 combined", payload["strategy1"]["combined"])
    print("Strategy 1 OOS", payload["strategy1"]["oos"])
    print("Strategy 1 PM 2025+", payload["strategy1"]["pm_overlay"])
    print("Strategy 2 timed", payload["strategy2"]["timed"])
    print("Strategy 2 shock", payload["strategy2"]["shock"])
    print("Strategy 2 shock net", payload["strategy2"]["shock_net"])
    print("Strategy 2 OOS shock net", payload["strategy2"]["oos_net"])
    print("Strategy 2 monthly", payload["strategy2"]["monthly"])
    print("Strategy 2 monthly net", payload["strategy2"]["monthly_net"])
    print("Strategy 2 monthly OOS net", payload["strategy2"]["monthly_oos_net"])
    print("S2 longs/shorts", s2["longs"], s2["shorts"])
    print("wrote", OUT / "results.json")


if __name__ == "__main__":
    main()
