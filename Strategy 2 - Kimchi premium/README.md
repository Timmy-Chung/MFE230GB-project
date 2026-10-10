# Kimchi Premium

## Main idea

* Korea's capital controls let coins flow into Korea but stop won from flowing out, so crypto
  trades at a premium in Seoul: the "kimchi premium", a crypto shadow exchange rate for the won
  (Makarov and Schoar, 2020).
* We split it into an aggregate premium κ (bitcoin, Upbit won price over Binance dollar price
  times the market won rate) and a coin-specific premium π (a coin's premium minus the median
  coin's; the exchange rate cancels).
* Hypothesis: Korean retail demand pushes local prices up in bursts, arbitrageurs carry part of
  it into world prices, and the pressure reverses. Trade: each Monday, short the fifth of coins
  with the highest π and buy the fifth with the lowest, in Binance perpetuals, for a week.
* The hypotheses and the rule were pre-registered in `DESIGN.md` before the first backtest. The
  reported window, the last five years, was chosen afterwards (see "Reported window" below).

## Results (last five years: October 2021 – September 2026, 260 weeks, net of 10 bp)

| | |
|---|---|
| Korea's bitcoin premium, daily | average 1.7%, above 2% on 37% of days, peak 11.7% on 19 Mar 2024, half-life 8.4 days |
| Japan's (bitbank, no capital controls) | average 0.1%, never above 2%, half-life 0.6 days |
| Next-week return per point of local premium π | −1.9% (Fama–MacBeth t = −2.7; −2.1%, t = −2.6 with controls) |
| Top-quintile premium closed within a week | 18 of 30 bp (t = −4.7): Korean price −0.97%, world price −0.79% vs the universe |
| BTC 4-week return per point of κ (H3) | −0.84% (t = −1.2): not supported in this window |
| Long-short, per year | price +40.5%, funding −11.1%, costs −14.7%, net +14.8% |
| Sharpe, gross / net | 1.01 / 0.51 (Newey–West t = 1.3); volatility 29%; max drawdown −40.5%; turnover 2.8× a week; break-even cost 20 bp |
| Japan placebo (same rule on bitbank, 184 weeks from March 2023) | net −27.2% a year, Sharpe −0.63; Korea over the same weeks +9.8%, Sharpe 0.37 |

The signal carries information and, over the last five years, the trade pays: +14.8% a year
after funding and costs. But funding (the arbitrageurs' crowded hedge) and turnover costs take
nearly two-thirds of the price gain, the result is not statistically significant (t = 1.3), and
it breaks even at 20 bp per unit traded. The same rule loses money in Japan, where capital moves
freely, which is the one robustness test we present. Risk analysis is in `output/tables` and on
the interactive page; `output/tables/slide_numbers.json` holds every number on the slides.


## Layout

```
DESIGN.md              pre-registration, written before any backtest, with a deviations log
AI_USAGE.md            how AI was used: prompts, outputs, safeguards
run_all.sh             rebuilds everything
requirements.txt
src/
  config.py            every parameter fixed in DESIGN.md
  dl_upbit.py          Upbit KRW daily candles (public API)
  dl_bitbank.py        bitbank JPY daily candles (Japan placebo)
  dl_fred.py           FRED: DEXKOUS, DEXJPUS, VIXCLS, DTB3
  dl_lists.py          Binance public-archive symbol lists
  dl_binance.py        Binance spot klines, USDT-M perpetual klines and funding (delisted kept)
  build_panel.py       daily panels: prices, premia κ and π, returns, funding, volumes
  strategy.py          weekly panel, portfolio construction, backtest, statistics
  run_backtest.py      main rule, cost grid, Japan placebo (last five years); with "full": the
                       pre-registered 2020–26 run with variants, robustness grid, randomization
  run_analysis.py      H1–H4 tests, froth overlay, exposures, episodes, liquidity, concentration
  make_figures.py      PNG figures used on the slides (dark theme, JetBrains Mono if available)
  slide_numbers.py     every number quoted on the slides -> output/tables/slide_numbers.json
  export_page_data.py  JSON for the interactive page
  build_page.py        assembles output/page/kimchi_premium.html
  page/                page template, page script and the chart kit shared with Strategy 1
data/
  raw/                 download snapshot of 7 Oct 2026 for Upbit, bitbank and FRED (Binance is re-downloaded)
  processed/           daily and weekly panels (parquet)
output/
  tables/              every number reported (CSV, analysis.json, slide_numbers.json)
    full_sample_2020_2026/  the pre-registered full-sample run and its robustness grid
  figures/             slide figures (PNG)
  page/                kimchi_premium.html, the self-contained interactive page
```

## Reproduce

```
pip install -r requirements.txt
SKIP_DOWNLOAD=1 bash run_all.sh   # from the shipped processed data, about 8 minutes
bash run_all.sh                   # from scratch, about 45 minutes (mostly downloads)
```

Python 3.10 or later. Results are deterministic (the randomization test uses seed 20261007).
A fresh download can differ slightly: Upbit's API only serves coins still listed on the day
you download, so the shipped `data/raw/upbit` snapshot is the one behind the reported numbers.

## Timing and data conventions

* Day d is the UTC day; its close is the price at 00:00 UTC on d+1 for Upbit, Binance and bitbank.
* The signal uses the 7 daily closes up to Monday 00:00 UTC; positions are opened at that
  Monday's 00:00 UTC price and held for 7 days. A one-day lag is a robustness test.
* Perpetual returns include funding: longs pay when the rate is positive. Settlements at
  00:00 UTC count toward the previous day.
* κ uses the FRED noon New York rate of the same day, which is set before the 00:00 UTC close.
  π needs no exchange rate.
* Renamed tokens (MATIC→POL, RNDR→RENDER, EOS→A) are stitched; 1000× perpetual contracts are
  rescaled; ticker collisions are removed by a same-asset check (`output/tables/coin_checks_kr.csv`).

## Limitations

* Survivorship on the Korean side: Upbit's API serves only coins still listed. Coins Upbit later
  delisted usually traded at a Korean discount first, so they would have been in the long leg as
  their prices fell. The true result is probably worse than reported.
* USDT is treated as a dollar; Binance is assumed solvent and orderly; market impact beyond
  10 bp per unit traded is not modelled.
* The five-year window was chosen after the full-sample result was known (see above).
* Japan has 20 eligible coins only from March 2023, so the placebo covers 184 weeks.

