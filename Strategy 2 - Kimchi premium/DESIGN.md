# Kimchi Premium: pre-registration of Strategy 2 (MFE 230GB final project)

## 1. Economic idea

Korea's capital controls segment its crypto market. Korean exchanges trade against the won,
only residents with a real-name bank account can trade on them (foreigners are shut out),
and residents cannot freely send won abroad: outward remittances above small limits need
documentation, and banks and the customs service police transfers linked to crypto
arbitrage. Coins can flow into Korea, but the won proceeds of an arbitrage cannot easily
flow out. So Korean crypto prices can sit above world prices for long periods: the
"kimchi premium" (Makarov and Schoar, 2020, *JFE*). It is a crypto shadow exchange rate for
the won, in the family of onshore/offshore spreads (CNY vs CNH) and CIP deviations: one
asset, two prices, and a constraint that keeps arbitrage capital from closing the gap.

We split the premium into two parts.

* **Aggregate premium κ.** Korean excess demand for crypto as a whole, priced through the
  capital-control wedge. Measured on bitcoin.
* **Coin-specific local premium π.** The extra premium on one coin relative to the Korean
  market as a whole. The exchange rate cancels out of π. Closing it needs no won to leave
  Korea (sell the dear coin in Korea, buy it abroad with BTC, move coins), but only Korean
  residents can do it, transfers take time, and exchanges suspend deposits and
  withdrawals. So π measures local demand pressure on one coin that arbitrage closes only
  slowly.

**Mechanism.** Korean retail demand arrives in bursts (attention, pumps, listing hype).
It pushes the local price up first. Domestic arbitrageurs buy abroad and sell in Korea, so
part of the pressure spills into the world price. When the burst fades the price pressure
reverses, as for flow-driven price pressure in stocks (Coval and Stafford, 2007) and
attention-driven retail buying (Barber and Odean, 2008). Coins at a local discount are the
mirror image: Korean selling pressure that later reverses.

## 2. Hypotheses

* **H1 Segmentation.** κ is large, persistent and rises in crypto booms. The same measure
  for Japan (yen, no capital controls; bitbank prices) is small and short-lived.
  *Tests:* mean, standard deviation, share of days above 2%, AR(1) half-life, correlation
  with the trailing 4-week BTC return; Korea vs Japan.
* **H2 Reversal (main strategy).** Coins with a high local premium π have lower returns on
  Binance over the next week; coins at a local discount have higher returns.
  *Tests:* weekly Fama-MacBeth slope of next-week Binance perp return on π (Newey-West,
  4 lags, on the slope series); quintile spread; trading rule below.
* **H3 Froth.** A high aggregate premium κ predicts lower BTC returns over the next 4 weeks.
  *Tests:* predictive regression of 4-week-ahead BTC return on κ (weekly, Newey-West with
  8 lags for the overlap); the overlay rule below.
* **H4 Channel.** After a high local premium, the gap closes mostly through the Korean
  price, and the world price also falls back (the part the strategy earns). *Test:*
  next-week change in π for top- and bottom-quintile coins, split into the change in the
  Korean price and the change in the world price, each relative to the cross-sectional
  median.

## 3. Data

| Data | Source | Use |
|---|---|---|
| Daily KRW candles (UTC day), all currently listed KRW markets | Upbit public API | Korean prices and won turnover |
| Daily spot USDT klines | Binance public data archive | World price |
| Daily USDT-margined perpetual klines and funding settlements, delisted symbols included | Binance public data archive | Returns, volumes |
| Daily JPY candles | bitbank public API | Japan placebo |
| KRW/USD and JPY/USD noon New York rates (DEXKOUS, DEXJPUS), VIX, 3-month T-bill | FRED | κ, risk states, cash rate |

## 4. Definitions

* Log premium of coin i in Korea at the close of UTC day d:
  p(i,d) = ln P_KRW(i,d) − ln P_USDT(i,d) − ln S_KRW/USD(d),
  with Upbit closes, Binance spot closes (perpetual close if Binance has no spot pair) and
  the FRED noon New York rate for day d, which is set before the 00:00 UTC close (carried
  forward over US holidays). USDT is treated as USD.
* Aggregate premium: κ(d) = p(BTC, d).
* Coin-specific premium: π(i,d) = p(i,d) − median over eligible coins j of p(j,d). The
  exchange rate drops out.
* Signal: π̄(i,t) = mean of π(i,d) over the 7 daily closes up to the formation time t
  (Monday 00:00 UTC). κ̄(t) is defined the same way.

## 5. Universe (rebuilt every Monday)

* Upbit KRW market with at least 28 daily closes in the past 35 days, and a Binance
  USDT-margined perpetual with at least 28 days of history.
* Excluded: fiat- and commodity-pegged tokens, and wrapped or staked derivatives.
* Same-asset check (ticker collisions, for example Upbit TON = Tokamak Network vs Binance
  TON = Toncoin): a coin is dropped if its median |p(i,d) − κ(d)| over all days exceeds 15%
  or if the correlation of its daily Upbit and Binance returns is below 0.5. Both checks
  use contemporaneous data only and no return predictability.
* Liquidity: 7-day average Upbit turnover of at least ₩500 million a day and 7-day average
  Binance perpetual volume of at least $5 million a day.
* Blocked-channel filter: drop a coin for the week if |π̄| > 10%. A gap that large means
  deposits or withdrawals are suspended or a delisting is under way, which is a different
  mechanism with jump risk.
* At least 20 eligible coins are needed to trade that week.

## 6. Trading rule

* Rank on π̄. Short the top quintile (highest local premium), long the bottom quintile.
  Equal weights within each leg; $1 long and $1 short (gross exposure 2).
* Rebalance every Monday at 00:00 UTC and hold for 7 days.
* Return: Binance perpetual close-to-close return plus funding (longs pay funding when it is
  positive, shorts receive it).
* Costs: 10 bp per unit of notional traded at every rebalance, including the first.
* Sample: formation weeks from the first Monday of 2020 (or the first with 20 eligible
  coins) through the week ending 28 September 2026.
* Variants reported next to the main rule: beta-neutral legs (each leg scaled to zero
  ex-ante BTC beta from 90 daily returns), rank weights, terciles.

## 7. Overlay (H3)

* BTC perpetual, long $1, funding included. Froth brake: flat (earning the T-bill rate)
  for the week if κ̄ is above the 90th percentile of its own trailing 365 days; otherwise
  long. Compared with always-long BTC.
* We also report the long-short's returns by κ regime.

## 8. Pre-specified robustness and out-of-sample tests

1. Sub-periods 2020–2022 and 2023–2026 (split fixed here).
2. One-day execution lag: the signal uses the 7 closes up to Sunday 00:00 UTC; the trade is
   still Monday 00:00.
3. Costs of 0, 5, 10, 20, 30 and 40 bp.
4. Universe: no liquidity filter; strict filter (₩2 billion and $20 million); no
   blocked-channel filter; a 5% blocked-channel filter.
5. Signal: the change in the premium (π̄ minus its mean over the previous 28 days) instead
   of the level; the premium relative to BTC instead of the median.
6. Japan placebo: the same construction on bitbank's JPY markets.
7. Randomization: π̄ shuffled across coins within each week, 1,000 draws; p-value of the
   main rule's Sharpe ratio.

## 9. Risk analysis (pre-specified)

* Exposures: BTC up- and down-market betas, equal-weighted crypto market, crypto momentum
  (4-week return, long-short in the same universe), weekly changes in VIX, KRW/USD and κ.
* Episodes: LUNA (May 2022), FTX (November 2022), yen carry unwind (August 2024), Korean
  martial-law night (3 December 2024), 10 October 2025 liquidation crash.
* Liquidity: P&L by Binance volume tercile; leg volumes against position size.
* Concentration: share of P&L from the best and worst five coins; worst ten weeks and the
  coins behind them.
