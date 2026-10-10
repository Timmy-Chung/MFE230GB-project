"""Slide-level diagnostics for the equity-spillover deck (slides 7, 9 and 10).

Reruns the chosen rule (construction C: 6-month local equity return minus the US, long/short vs USD,
equal weight) on the G10 book and on the nine floating EM currencies, then computes
  * positions by year: share of months each currency was held long, and the average net position (slides 7, 9)
  * return attribution by currency with USD as one of the ten legs: each currency's net exposure (USD = minus the
    net position) times its return against the equal-weight basket of all ten; the ten sum to the book before costs
  * risk table: vol, drawdowns, worst month, VaR/CVaR, skew, kurtosis, hit rate, Sortino, Calmar, beta to the dollar
Run:  python3 equity_spillover_slides.py     (needs data/; writes output/equity_slides.json)
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import equity_spillover as es

ROOT = Path(__file__).resolve().parent
ORDER = {"DM": ["EUR", "GBP", "CHF", "SEK", "NOK", "JPY", "AUD", "NZD", "CAD"],
         "EM": ["BRL", "MXN", "CLP", "COP", "ZAR", "PLN", "HUF", "CZK", "KRW"]}


def panel(uni):
    P = es.build_panel(uni)
    if uni == "EM":                                                   # floating currencies only (Topic 2 / IMF AREAER)
        cols = [c for c, v in P["regime"].items() if v == "float"]
        P = {k: (v[cols] if isinstance(v, pd.DataFrame) else v) for k, v in P.items() if k != "regime"} | {"regime": {c: "float" for c in cols}}
    return P


def risk(r, usd):
    r = r.dropna(); ann = 12
    wealth = (1 + r).cumprod(); dd = wealth / wealth.cummax() - 1
    runs, c = [], 0
    for u in (dd < 0).astype(int):
        c = c + 1 if u else 0; runs.append(c)
    ab = pd.concat([r.rename("r"), usd.rename("u")], axis=1).dropna()
    return {"mean": r.mean() * ann, "vol": r.std() * np.sqrt(ann), "sharpe": r.mean() / r.std() * np.sqrt(ann),
            "mdd": dd.min(), "mdd_peak": str(wealth.loc[:dd.idxmin()].idxmax().date()), "mdd_trough": str(dd.idxmin().date()),
            "longest_dd_months": int(max(runs)), "worst_month": r.min(), "best_month": r.max(),
            "var95": np.percentile(r, 5), "cvar95": r[r <= np.percentile(r, 5)].mean(), "skew": r.skew(), "kurt": r.kurt(),
            "hit": (r > 0).mean(), "sortino": r.mean() * ann / (r[r < 0].std() * np.sqrt(ann)), "calmar": r.mean() * ann / abs(dd.min()),
            "beta_usd": float(np.polyfit(ab.u, ab.r, 1)[0]), "corr_usd": ab.r.corr(ab.u),
            "worst_months": {str(d.date()): float(v) for d, v in r.nsmallest(4).items()}}


def main():
    usd = np.log(es.load_fred("DTWEXBGS")).diff().resample("ME").sum(min_count=1)
    out, books = {}, {}
    for uni, order in ORDER.items():
        P = panel(uni)
        sig = es.signal_matrix(P, "rel_us", 6)
        w = es.weights_from_signal(sig, "dollar", 3).fillna(0)
        r_full, to, _ = es.backtest(w, P["xr"], es.COST[uni], 1)
        r = r_full.loc[es.START:]; books[uni] = r
        wl = w.loc[es.START:]; net = wl.sum(axis=1)
        # positions by year
        years = sorted({d.year for d in wl.index})
        share_long_by_year = {c: {y: float((wl[c].loc[str(y)] > 0).sum() / max((wl[c].loc[str(y)] != 0).sum(), 1)) for y in years} for c in order}
        net_by_year = {y: float(net.loc[str(y)].mean()) for y in years}
        # attribution, ten legs
        xr = P["xr"][order].fillna(0); ws = w[order].shift(1).fillna(0)
        basket = xr.sum(axis=1) / (len(order) + 1)
        rb = xr.sub(basket, axis=0); e_usd = -ws.sum(axis=1)
        attrib = {c: float((ws[c] * rb[c]).loc[es.START:].mean() * 12) for c in order}
        attrib["USD"] = float((e_usd * (-basket)).loc[es.START:].mean() * 12)
        cost = float((es.COST[uni] * to).loc[es.START:].mean() * 12)
        n = wl.ne(0).sum(axis=1); longs = wl.gt(0).sum(axis=1); maj = np.maximum(longs, n - longs) / n
        out[uni] = {"currencies": order, "share_long": {c: float((wl[c] > 0).sum() / (wl[c] != 0).sum()) for c in order},
                    "share_long_by_year": share_long_by_year, "net_by_year": net_by_year,
                    "net_mean": float(net.mean()), "share_months_net_long_usd": float((net < 0).mean()),
                    "share_months_all_one_side": float((net.abs() >= 0.99).mean()), "share_months_7of9_one_side": float((maj >= 7 / 9).mean()),
                    "attribution": attrib, "attribution_sum": float(sum(attrib.values())), "cost": cost, "book_mean": float(r.mean() * 12),
                    "risk": risk(r, usd),
                    "monthly": {str(d.date()): float(v) for d, v in r.items()}}
    out["corr_between_books"] = float(pd.concat([books["DM"], books["EM"]], axis=1).dropna().corr().iloc[0, 1])
    (ROOT / "output" / "equity_slides.json").write_text(json.dumps(out, indent=1, default=float))
    for uni in ORDER:
        o = out[uni]; k = o["risk"]
        print(f"{uni}: book {o['book_mean']*100:.2f}%/yr = sum of ten legs {o['attribution_sum']*100:.2f}% - costs {o['cost']*100:.2f}% | USD leg {o['attribution']['USD']*100:.2f}% | "
              f"vol {k['vol']*100:.1f}% MDD {k['mdd']*100:.1f}% longest DD {k['longest_dd_months']}m VaR95 {k['var95']*100:.2f}% skew {k['skew']:.2f} hit {k['hit']:.0%}")
    print("corr between books", round(out["corr_between_books"], 2))


if __name__ == "__main__":
    main()
