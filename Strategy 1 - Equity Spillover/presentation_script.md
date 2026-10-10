# Equity Spillover into FX — presentation script (target 5:40, hard cap 6:00)

Deck: https://claude.ai/artifact/NWA1dGC6K8eTBMGGw8PG2v · 11 slides · about 920 spoken words. The numbers are on the slides; the script spends its words on why.

---

**Slide 1 · Cover (0:00–0:20)**

The idea in one line: when a country's stock market beats the US, money flows in to buy those stocks, and to buy the stocks you first have to buy the currency. So the currency should go up. We trade that in G10 and emerging markets, and the simplest version is the only one that holds up.

**Slide 2 · The idea (0:20–1:05)**

Why would this work? Exchange rates are set by flows we mostly never see, and it doesn't take much flow to move the price. The flow we're after is a global investor moving money from one stock market to another. Here's the key: if every market is up together, nobody has to move anything. The flow happens when one market pulls ahead, and the biggest pool of money is in the US. So the question isn't "did it go up", it's "did it beat the US". The textbook predicts the opposite sign, that investors rebalance out of winners. The data say no: "beat the US" works, "went up" earns nothing, and a month late it's mostly gone, so the market absorbs this flow in weeks.

**Slide 3 · How we built it (1:05–1:45)**

Two ways to build the book. The usual way: rank the currencies against each other, buy the top, sell the bottom, equal amounts each side; 64 versions of that. The second way skips the ranking. Each country on its own, one question: did its market beat the US? Yes, buy the currency. No, sell it. The whole difference is that the second way keeps the US as the benchmark, and the first throws it away.

**Slide 4 · Selection (1:45–2:35)**

Four examples. A and B rank; C is "did it beat the US"; D is "did it go up". We picked on 2000 to 2015 and looked at the last ten years once, at the end. A and B look great in the first window and die after it. Partly overfitting: B was the best of 64 tries, so some of that was luck. But mostly this: after 2015 the US beat almost everyone, almost every year. Ranking forces you to buy something, so you buy the markets that lagged the US least, while the money was going to the US. C just shorts them all and is long the dollar, where the flow went. D fails the mirror way: "did it go up" is mostly the global market, and a global rally doesn't make anyone move money between countries. So C is the strategy.

**Slide 5 · The rule (2:35–3:05)**

Nine G10 currencies and nine floating EM currencies against the dollar. No managed currencies: if the central bank absorbs the flow, the price can't move. Month end, six-month stock return minus the US, positive long, negative short, one-ninth each, no leverage. Six months because that's how long allocators take to react; one month is noise. Costs are tiny in G10, we flip a currency about four times a year; in EM they eat a quarter of the gross return.

**Slide 6 · G10 performance (3:05–3:30)**

Orange is our book, blue is B, the ranked version. Blue looks better right up to where we stopped choosing, then goes flat. That's the project in one chart: the thing that looked best in sample stopped working, the simple thing kept going.

**Slide 7 · G10 positions and attribution (3:30–4:05)**

This is what we held, one row per currency, one box per year. Every row keeps switching colour, so this isn't secretly a carry or trend trade on one currency, and the net dollar position in the bottom row averages near zero. On the right, where the money came from, with the dollar as one of ten currencies: the dollar leg is under half, and seven of the other nine are positive. G10 works as country selection because these markets move for different reasons: commodities for Australia and Norway, Japan its own story, Europe a third. The signals disagree, so the book is nine views, not one.

**Slide 8 · Emerging markets (4:05–4:35)**

EM, same four constructions, nothing re-tuned. Ranking loses money in both halves; our rule holds out of sample. But the bottom table says the dollar position alone earns almost all of it, and without it the book loses money.

**Slide 9 · EM positions and attribution (4:35–5:05)**

Here's the intuition. Investors don't allocate to Brazil or Poland, they allocate to "emerging markets" as one asset class, through index funds. So when EM beats the US, the money buys the whole basket and all nine currencies move together. Our nine signals mostly agree anyway, because EM stock markets ride the same risk cycle, so the book piles onto one side of the dollar. And "did Brazil beat the US" says nothing about Brazil versus Poland, so the relative legs net to zero. It's a dollar trade, and we say so. It still works, because the signal catches the turn in the cycle before the currencies finish moving. But it's one bet, not nine, and that's how you'd size it.

**Slide 10 · Risk (5:05–5:30)**

Two things about the shape. First, no fat left tail: skew is zero or positive and the worst month is about one standard deviation, so this is not carry, collecting pennies and losing a year in a week. Second, the cost is time, not depth: drawdowns of nine or ten percent, but three years under water in G10 and five in EM. When it loses, it's the dollar jumping against the net position. The signal looks back six months, so when the cycle turns suddenly, January 2009, September 2022, we're still set up for the old regime.

**Slide 11 · Close (5:30–5:50)**

Three numbers. 0.46 then 0.38: our G10 rule before and after we chose it. 0.70 then 0.07: the ranked version, what happens when you pick the winner in sample. 0.38 versus minus 0.17: in EM, the dollar position alone versus everything else. Stock market winners pull in flow, the flow shows up in the currency next month, and the simplest way to trade it is the one that works. Thank you.

---

**If asked**

- *What's the difference between ranking and your rule?* Ranking compares countries with each other, so a market that lagged the US can still be a buy if the others lagged more, and you always have equal longs and shorts. Our rule compares each country with the US only, so the book can end up net long or net short dollars.
- *Why not rank?* Ranking throws away the US benchmark. A and B on slide 4 go flat after 2015, the years when the US beat nearly everyone and the flow went to the US.
- *Isn't this just FX momentum?* We ran the same rule on currency returns instead of stock returns: minus 0.30. And acting a month late drops it to 0.12, so it's a flow that gets absorbed fast, not a trend.
- *Why does "went up" fail when "beat the US" works?* A global rally lifts every market, so nobody reallocates between countries and no currency flow follows. Only relative performance moves money across borders.
- *Why six months?* Chosen on 2000 to 2015. Three and twelve also work; one month doesn't. Allocators react to performance over quarters, not weeks.
- *What do you mean by the dollar position or dollar component?* Because every currency is judged against the US, the book is usually net long or net short dollars. "Alone" means trading only that: long dollars against the whole basket when the US beat the average foreign market over six months, otherwise the reverse. "Removed" means the book minus that. G10: removed 0.42, alone 0.13. EM floats: alone 0.38, removed minus 0.17.
- *Worst months?* Jan 2009 minus 5.2% and Sep 2022 minus 3.2%, net long foreign currency into a dollar spike; Apr 2011 minus 3.2%, net short all nine as the dollar fell; Apr 2000 minus 3.4%, long the markets that had beaten the Nasdaq as it turned.
- *VaR?* Historical monthly 95% VaR is minus 1.8% in G10 and minus 2.1% in EM; CVaR minus 2.7% and minus 2.9%. The two books have a correlation of 0.15.
- *How big is the net dollar exposure?* G10: averages minus 5% of the book, long dollars 54% of months. EM floats: plus 13%, long dollars 40% of months. All nine EM currencies sit on one side in 11% of months, four times G10.
- *How did you do the attribution?* Ten legs, the dollar included. Each currency's net exposure, and for the dollar that's minus the net position, times its return against the equal-weight basket of all ten. The ten add up exactly to the book before costs.
- *What does "ranked" mean in B?* Sort the nine by vol-adjusted six-month return. Best gets the biggest long, worst the biggest short, weights proportional to rank, equal longs and shorts.
- *Why only floating EM currencies?* Topic 2. When the central bank absorbs the flow with reserves, the price doesn't move. The four managed ones, INR, CNY, IDR and TRY, earn minus 0.38 out of sample; it's in the package.
- *Isn't CNH a free float?* It's freely tradable offshore, but it tracks the onshore CNY, which has a daily fixing and a ±2% band, so Topic 2 classes China as a managed float. CNY spot vol is about 3% a year against 10 to 16% for the floats, and the rule on CNY alone earns nothing: minus 0.33 in sample, 0.04 after.
- *Why is the dollar leg so dominant in EM but not in G10?* Two reasons. The book is more one-sided in EM: seven or more of the nine sit on the same side of the dollar in 51% of months, against 39% in G10. And the predictability sits in the shared move: "US beat the EM average" forecasts EM-versus-dollar well, because flows into EM come at the asset-class level and push all nine currencies together, while country-versus-country equity performance doesn't map to a country-specific flow. In G10, allocations are by country and the markets move for different reasons, so the country legs carry the return.
- *Why is EM still worth running if it's a dollar trade?* It's a systematic way to time the dollar against EM from equity flows, 0.24 out of sample at 15 basis points. We just don't call it country selection.
- *Data?* OECD share-price indices to May 2026, FRED, ECB and IMF rates, all in the package. `equity_spillover.py` rebuilds all 70 constructions and `equity_spillover_floats.py` rebuilds the EM floats slide.
