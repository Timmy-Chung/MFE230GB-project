"""Build the daily panels used by every later step.

Usage: python -I src/build_panel.py

Reads data/raw/*, writes data/processed/*.parquet and output/tables/coin_checks.csv.
Day d means the UTC day; its close is the price at 00:00 UTC on d+1 (Upbit, Binance and
bitbank all use this boundary).
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402

RAW, PROC = C.RAW, C.PROC
DAYS = pd.date_range("2017-09-01", "2026-09-30", freq="D")


def read_series(path, col, date_col="date"):
    df = pd.read_csv(path, usecols=[date_col, col])
    s = pd.Series(df[col].astype(float).values, index=pd.to_datetime(df[date_col]))
    return s[~s.index.duplicated()].sort_index()


def wide(dct):
    return pd.DataFrame(dct).reindex(DAYS)


# ---------------------------------------------------------------- Upbit
up_close, up_turn = {}, {}
for f in sorted(glob.glob(os.path.join(RAW, "upbit", "KRW-*.csv"))):
    base = os.path.basename(f)[4:-4]
    up_close[base] = read_series(f, "close")
    up_turn[base] = read_series(f, "krw_turnover")
up_close, up_turn = wide(up_close), wide(up_turn)

# ---------------------------------------------------------------- Binance spot and perps
spot_close, spot_qvol = {}, {}
for f in glob.glob(os.path.join(RAW, "binance", "spot", "*USDT.csv")):
    sym = os.path.basename(f)[:-4]
    spot_close[sym[:-4]] = read_series(f, "close")
    spot_qvol[sym[:-4]] = read_series(f, "quote_volume")
spot_close, spot_qvol = wide(spot_close), wide(spot_qvol)

perp_files = {os.path.basename(f)[:-4]: f for f in glob.glob(os.path.join(RAW, "binance", "perp", "*USDT.csv"))}
fund_files = {os.path.basename(f)[:-4]: f for f in glob.glob(os.path.join(RAW, "binance", "funding", "*USDT.csv"))}


def perp_symbols_for(base):
    out = []
    for pre, mult in C.PERP_MULT.items():
        sym = f"{pre}{base}USDT"
        if sym in perp_files:
            out.append((sym, mult))
    return out


def load_perp(base):
    """Return daily close (in units of one coin), daily return, quote volume, funding for a
    base, choosing the contract with the longest history when several exist."""
    best = None
    for sym, mult in perp_symbols_for(base):
        c = read_series(perp_files[sym], "close")
        if best is None or len(c) > len(best[1]):
            best = (sym, c, mult)
    if best is None:
        return None
    sym, c, mult = best
    q = read_series(perp_files[sym], "quote_volume")
    r = c.pct_change()
    fd = pd.Series(dtype=float)
    if sym in fund_files:
        fr = pd.read_csv(fund_files[sym])
        t = pd.to_datetime(fr["time"]) - pd.Timedelta(seconds=1)   # 00:00 settlement belongs to the day before
        fd = fr.groupby(t.dt.floor("D"))["funding_rate"].sum()
    return {"sym": sym, "close": c / mult, "ret": r, "qvol": q, "fund": fd}


def stitch(series_list):
    """First series wins where present; later ones fill gaps (new symbol first, then old)."""
    out = series_list[0].copy()
    for s in series_list[1:]:
        out = out.combine_first(s)
    return out


bases = sorted(set(up_close.columns))
bb_pairs = json.load(open(os.path.join(RAW, "bitbank", "_pairs.json")))
bb_bases = sorted({C.BITBANK_MAP.get(p.split("_")[0].upper(), p.split("_")[0].upper()) for p in bb_pairs})
all_bases = sorted(set(bases) | set(bb_bases))

world, perp_close, perp_ret, perp_qvol, funding, perp_sym = {}, {}, {}, {}, {}, {}
for b in all_bases:
    chain = [b] + C.RENAMES.get(b, [])
    w_parts, pc, pr, pq, pf, syms = [], [], [], [], [], []
    for bb in chain:
        if bb in spot_close.columns:
            w_parts.append(spot_close[bb].dropna())
        p = load_perp(bb)
        if p is not None:
            pc.append(p["close"]); pr.append(p["ret"]); pq.append(p["qvol"]); pf.append(p["fund"]); syms.append(p["sym"])
    if pc:
        perp_close[b] = stitch(pc)
        perp_ret[b] = stitch(pr)
        perp_qvol[b] = stitch(pq)
        f = [x for x in pf if len(x)]
        funding[b] = stitch(f) if f else pd.Series(dtype=float)
        perp_sym[b] = "+".join(syms)
        w_parts.append(perp_close[b].dropna())      # perp price fills days with no spot pair
    if w_parts:
        world[b] = stitch(w_parts)

world, perp_close, perp_ret, perp_qvol = wide(world), wide(perp_close), wide(perp_ret), wide(perp_qvol)
funding = wide(funding).reindex(DAYS)
# a perp that exists that day but has no settlement recorded pays zero
funding = funding.where(perp_close.notna())
funding = funding.fillna(0.0).where(perp_close.notna())

# ---------------------------------------------------------------- bitbank (Japan placebo)
bb_close = {}
for p in bb_pairs:
    b = C.BITBANK_MAP.get(p.split("_")[0].upper(), p.split("_")[0].upper())
    f = os.path.join(RAW, "bitbank", f"{p}.csv")
    if os.path.exists(f) and os.path.getsize(f) > 100:
        s = read_series(f, "close")
        bb_close[b] = s if b not in bb_close else bb_close[b].combine_first(s)
bb_close = wide(bb_close)
# POL/MATIC and RENDER/RNDR appear twice on bitbank: merge the old ticker into the new one
for new, olds in C.RENAMES.items():
    for o in olds:
        if new in bb_close and o in bb_close:
            bb_close[new] = bb_close[new].combine_first(bb_close[o])
            bb_close = bb_close.drop(columns=o)

# ---------------------------------------------------------------- FRED
def fred(sid):
    df = pd.read_csv(os.path.join(RAW, "fred", f"{sid}.csv"))
    s = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    s.index = pd.to_datetime(df.iloc[:, 0])
    return s.dropna()


krw = fred("DEXKOUS").reindex(DAYS).ffill(limit=7)
jpy = fred("DEXJPUS").reindex(DAYS).ffill(limit=7)
vix = fred("VIXCLS").reindex(DAYS).ffill(limit=7)
tbill = fred("DTB3").reindex(DAYS).ffill(limit=10) / 100.0

# ---------------------------------------------------------------- premia
def premia(local_close, fx, local_bases):
    cols = [b for b in local_bases if b in world.columns and b not in C.EXCLUDE]
    p = np.log(local_close[cols]) - np.log(world[cols]) - np.log(fx).values[:, None]
    return p


p_kr = premia(up_close, krw, bases)
p_jp = premia(bb_close, jpy, bb_close.columns)

# same-asset checks (contemporaneous only)
def checks(p, local_close, kappa):
    rows = []
    for b in p.columns:
        dev = (p[b] - kappa).abs().dropna()
        lr = np.log(local_close[b]).diff()
        wr = np.log(world[b]).diff()
        both = pd.concat([lr, wr], axis=1).dropna()
        corr = both.corr().iloc[0, 1] if len(both) >= 60 else np.nan
        rows.append({"base": b, "days": int(p[b].notna().sum()), "median_abs_dev": dev.median() if len(dev) else np.nan,
                     "ret_corr": corr})
    df = pd.DataFrame(rows).set_index("base")
    df["pass"] = (df["median_abs_dev"] <= C.SAME_ASSET_MAX_MEDIAN_DEV) & (df["ret_corr"] >= C.SAME_ASSET_MIN_CORR)
    return df


kappa_kr = p_kr["BTC"]
kappa_jp = p_jp["BTC"]
chk_kr = checks(p_kr, up_close, kappa_kr)
chk_jp = checks(p_jp, bb_close, kappa_jp)
chk_kr.assign(market="KR").to_csv(os.path.join(C.TABLES, "coin_checks_kr.csv"))
chk_jp.assign(market="JP").to_csv(os.path.join(C.TABLES, "coin_checks_jp.csv"))


def coin_premium(p, chk):
    ok = chk.index[chk["pass"]]
    p = p[ok].copy()
    med0 = p.median(axis=1)
    p = p.where((p.sub(med0, axis=0)).abs() <= 0.5)      # day-level data mismatch guard
    n = p.notna().sum(axis=1)
    med = p.median(axis=1).where(n >= 10)
    return p, p.sub(med, axis=0), med


p_kr_ok, pi_kr, med_kr = coin_premium(p_kr, chk_kr)
p_jp_ok, pi_jp, med_jp = coin_premium(p_jp, chk_jp)

usdt_prem = (np.log(up_close["USDT"]) - np.log(krw)) if "USDT" in up_close else pd.Series(index=DAYS, dtype=float)

# ---------------------------------------------------------------- save
def save(df, name):
    df = df if isinstance(df, pd.DataFrame) else df.to_frame(name)
    df.index.name = "date"
    df.columns = [str(c) for c in df.columns]
    df.to_parquet(os.path.join(PROC, f"{name}.parquet"))


save(up_close, "upbit_close"); save(up_turn, "upbit_turnover")
save(world, "world_close"); save(spot_qvol, "spot_qvol")
save(perp_close, "perp_close"); save(perp_ret, "perp_ret"); save(perp_qvol, "perp_qvol"); save(funding, "funding")
save(bb_close, "bitbank_close")
save(p_kr_ok, "premium_kr"); save(pi_kr, "pi_kr"); save(p_jp_ok, "premium_jp"); save(pi_jp, "pi_jp")
save(pd.DataFrame({"kappa_kr": kappa_kr, "kappa_jp": kappa_jp, "median_kr": med_kr, "median_jp": med_jp,
                   "usdt_premium_kr": usdt_prem, "krw_per_usd": krw, "jpy_per_usd": jpy, "vix": vix, "tbill": tbill}),
     "macro")
pd.Series(perp_sym).rename("perp_symbol").to_csv(os.path.join(C.TABLES, "perp_symbols.csv"))
print("upbit bases", len(bases), "| KR premium coins passing checks", int(chk_kr["pass"].sum()), "of", len(chk_kr),
      "| JP", int(chk_jp["pass"].sum()), "of", len(chk_jp))
print("failed KR checks:", chk_kr[~chk_kr["pass"]].round(3).to_string())
