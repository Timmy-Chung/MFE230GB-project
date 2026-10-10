"""Weekly signals, portfolio construction, backtest and performance statistics.

Everything here follows DESIGN.md sections 4-8. Formation happens at Monday 00:00 UTC
(date M). The signal uses daily closes of days M-7..M-1 (lag 0); the position is held
over days M..M+6 and earns the Binance perpetual return plus funding.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402


def load(name):
    return pd.read_parquet(os.path.join(C.PROC, f"{name}.parquet"))


class Market:
    """Daily data for one local market (KR = Upbit, JP = bitbank)."""

    def __init__(self, market="KR"):
        self.market = market
        if market == "KR":
            self.pi = load("pi_kr")
            self.p = load("premium_kr")
            self.local = load("upbit_close")
            self.turn = load("upbit_turnover")
        else:
            self.pi = load("pi_jp")
            self.p = load("premium_jp")
            self.local = load("bitbank_close")
            self.turn = None
        self.world = load("world_close")
        self.perp_close = load("perp_close")
        self.perp_ret = load("perp_ret")
        self.perp_qvol = load("perp_qvol")
        self.funding = load("funding")
        self.macro = load("macro")
        coins = [c for c in self.pi.columns if c in self.perp_close.columns]
        self.coins = coins
        self.perp_first = self.perp_close[coins].apply(lambda s: s.first_valid_index())


def formation_dates(start=C.FIRST_FORMATION, end=C.LAST_FORMATION):
    return pd.date_range(start, end, freq="W-MON")


def weekly_panel(mk, lag=0, signal="level", base="median", liq="base", blocked=C.BLOCKED_CHANNEL,
                 start=C.FIRST_FORMATION, end=C.LAST_FORMATION):
    """One row per (formation week, eligible coin)."""
    D = pd.Timedelta(days=1)
    rows = []
    coins = mk.coins
    pi = mk.pi[coins] if base == "median" else mk.p[coins].sub(mk.p["BTC"] if "BTC" in mk.p else 0, axis=0)
    for M in formation_dates(start, end):
        sig_days = pd.date_range(M - (7 + lag) * D, M - (1 + lag) * D)
        hold_days = pd.date_range(M, M + 6 * D)
        s = pi.loc[sig_days]
        n_obs = s.notna().sum()
        pibar = s.mean().where(n_obs >= C.MIN_SIGNAL_DAYS)
        if signal == "change":
            prior = pi.loc[pd.date_range(M - 35 * D, M - 8 * D)].mean()
            pibar = pibar - prior
        # eligibility
        up_days = mk.local.loc[pd.date_range(M - 35 * D, M - D), coins].notna().sum()
        ok = pibar.notna() & (up_days >= C.MIN_UPBIT_DAYS)
        ok &= mk.perp_first.reindex(coins).le(M - C.MIN_PERP_AGE_DAYS * D).fillna(False)
        ok &= mk.perp_close.loc[M - D, coins].notna()
        last7 = pd.date_range(M - 7 * D, M - D)
        pv = mk.perp_qvol.loc[last7, coins].mean()
        if liq != "none":
            min_up = C.STRICT_UPBIT_TURNOVER_KRW if liq == "strict" else C.MIN_UPBIT_TURNOVER_KRW
            min_pv = C.STRICT_PERP_VOLUME_USD if liq == "strict" else C.MIN_PERP_VOLUME_USD
            ok &= pv.ge(min_pv).fillna(False)
            if mk.turn is not None:
                ok &= mk.turn.loc[last7, coins].mean().ge(min_up).fillna(False)
        if blocked is not None:
            ok &= pibar.abs().le(blocked).fillna(False)
        el = [c for c in coins if ok.get(c, False)]
        if not el:
            continue
        r = mk.perp_ret.loc[hold_days, el]
        alive = mk.perp_close.loc[hold_days, el].notna()
        r = r.where(alive, 0.0).fillna(0.0)
        ret_price = (1 + r).prod() - 1
        fund = mk.funding.loc[hold_days, el].fillna(0.0).sum()
        # past returns (world price) for controls
        wc = mk.world[el]
        past1 = np.log(wc.loc[M - D] / wc.loc[M - 8 * D])
        past4 = np.log(wc.loc[M - D] / wc.loc[M - 29 * D])
        # next-week change in local and world prices (channel test, H4)
        dloc = np.log(mk.local.loc[M + 6 * D, el] / mk.local.loc[M - D, el])
        dwor = np.log(mk.world.loc[M + 6 * D, el] / mk.world.loc[M - D, el])
        pi_next = pi.loc[hold_days, el].mean()
        pi_last = pi.loc[M - D, el]
        pi_end = pi.loc[M + 6 * D, el]
        fund7 = mk.funding.loc[last7, el].fillna(0.0).sum()
        df = pd.DataFrame({
            "week": M, "coin": el, "signal": pibar[el].values, "ret_price": ret_price.values,
            "funding": fund.values, "ret_long": (ret_price - fund).values,
            "past1": past1.values, "past4": past4.values, "perp_vol": pv[el].values,
            "dlocal": dloc.values, "dworld": dwor.values, "pi_next": pi_next.values, "fund7": fund7.values,
            "pi_last": pi_last.values, "pi_end": pi_end.values,
        })
        rows.append(df)
    panel = pd.concat(rows, ignore_index=True)
    return panel


def btc_betas(mk, M, coins, window=C.BETA_WINDOW):
    D = pd.Timedelta(days=1)
    days = pd.date_range(M - window * D, M - D)
    x = mk.perp_ret.loc[days, "BTC"]
    b = {}
    for c in coins:
        y = mk.perp_ret.loc[days, c]
        m = y.notna() & x.notna()
        b[c] = np.cov(y[m], x[m])[0, 1] / np.var(x[m], ddof=1) if m.sum() >= 30 else 1.0
    return pd.Series(b)


def build_weights(panel, q=C.QUANTILE, scheme="quintile", min_coins=C.MIN_COINS, mk=None, beta_neutral=False):
    """Return dict week -> Series of weights (long +, short -). $1 long and $1 short."""
    W = {}
    for M, g in panel.groupby("week"):
        if len(g) < min_coins:
            continue
        s = g.set_index("coin")["signal"]
        if scheme == "rank":
            rk = s.rank()
            dev = -(rk - rk.mean())               # high premium -> short
            pos, neg = dev.clip(lower=0), (-dev).clip(lower=0)
            w = pos / pos.sum() - neg / neg.sum()
        else:
            k = max(1, int(np.floor(len(s) * q)))
            order = s.sort_values()
            w = pd.Series(0.0, index=s.index)
            w[order.index[:k]] = 1.0 / k          # lowest local premium: long
            w[order.index[-k:]] = -1.0 / k        # highest local premium: short
        w = w[w != 0]
        if beta_neutral and mk is not None:
            b = btc_betas(mk, M, w.index)
            bl = max(b[w[w > 0].index].mean(), 0.1)
            bs = max(b[w[w < 0].index].mean(), 0.1)
            a, c = 2 * bs / (bl + bs), 2 * bl / (bl + bs)
            w = w.where(w < 0, w * a).where(w > 0, w * c)
        W[M] = w
    return W


def backtest(panel, W, cost_bp=C.COST_BP):
    """Weekly gross/net returns, turnover, funding and price components."""
    idx = panel.set_index(["week", "coin"])
    out, prev = [], pd.Series(dtype=float)
    contrib = []
    for M in sorted(W):
        w = W[M]
        g = idx.loc[M].reindex(w.index)
        price = (w * g["ret_price"]).sum()
        fund = -(w * g["funding"]).sum()
        gross = price + fund
        # turnover: trade from drifted previous holdings to new targets
        trades = w.sub(prev, fill_value=0.0).abs().sum()
        cost = cost_bp / 1e4 * trades
        out.append({"week": M, "gross": gross, "price": price, "funding": fund, "turnover": trades,
                    "cost": cost, "net": gross - cost, "n_long": int((w > 0).sum()), "n_short": int((w < 0).sum()),
                    "long_ret": (w[w > 0] * g.loc[w > 0, "ret_long"]).sum(),
                    "short_ret": (w[w < 0] * (g.loc[w < 0, "ret_price"] - g.loc[w < 0, "funding"])).sum()})
        contrib.append(pd.DataFrame({"week": M, "coin": w.index, "weight": w.values,
                                     "pnl": (w * g["ret_price"] - w * g["funding"]).values}))
        prev = w * (1 + g["ret_price"])
    res = pd.DataFrame(out).set_index("week")
    return res, pd.concat(contrib, ignore_index=True)


def nw_tstat(x, lags=4):
    x = pd.Series(x).dropna().values
    n = len(x)
    if n < 10:
        return np.nan
    e = x - x.mean()
    s = (e @ e) / n
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        s += 2 * w * (e[L:] @ e[:-L]) / n
    return x.mean() / np.sqrt(s / n)


def perf(r, periods=52):
    r = pd.Series(r).dropna()
    wealth = (1 + r).cumprod()
    dd = wealth / wealth.cummax() - 1
    vol = r.std() * np.sqrt(periods)
    mean = r.mean() * periods
    return {"ann_return": mean, "ann_vol": vol, "sharpe": mean / vol if vol > 0 else np.nan,
            "t_nw": nw_tstat(r), "max_dd": dd.min(), "final_wealth": wealth.iloc[-1] if len(wealth) else np.nan,
            "cagr": wealth.iloc[-1] ** (periods / len(r)) - 1 if len(r) else np.nan,
            "skew": r.skew(), "worst_week": r.min(), "best_week": r.max(), "hit_rate": (r > 0).mean(), "weeks": len(r)}


def fama_macbeth(panel, y="ret_long", xs=("signal",), min_n=C.MIN_COINS, lags=4, standardize=False):
    coefs = []
    for M, g in panel.groupby("week"):
        g = g.dropna(subset=[y] + list(xs))
        if len(g) < min_n:
            continue
        X = g[list(xs)].astype(float)
        if standardize:
            X = (X - X.mean()) / X.std()
        X = np.column_stack([np.ones(len(g)), X.values])
        b, *_ = np.linalg.lstsq(X, g[y].values.astype(float), rcond=None)
        coefs.append(pd.Series(b, index=["const"] + list(xs), name=M))
    B = pd.DataFrame(coefs)
    return pd.DataFrame({"coef": B.mean(), "t_nw": B.apply(lambda c: nw_tstat(c, lags)), "weeks": len(B)}), B
