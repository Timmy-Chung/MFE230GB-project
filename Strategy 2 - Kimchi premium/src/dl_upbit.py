"""Download Upbit KRW-market daily candles (UTC day = 09:00 KST boundary) for every
currently listed KRW market.

Usage: python -I src/dl_upbit.py data/raw/upbit [shard nshards]

Upbit's public quotation API only serves markets that are still listed, so coins that
Upbit has delisted are missing (survivorship; see README "Limitations").
Rate limit: 10 requests/s per IP; we stay below it.
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

OUT = sys.argv[1]
SHARD, NSHARD = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research; MFE230GB replication)"}
START = "2017-09-01"


def get(url, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.5 * (k + 1))
                continue
            if e.code == 404:
                return None
            time.sleep(1.0 * (k + 1))
        except Exception:
            time.sleep(1.0 * (k + 1))
    raise RuntimeError(f"failed: {url}")


markets = get("https://api.upbit.com/v1/market/all?isDetails=true")
krw = [m for m in markets if m["market"].startswith("KRW-")]
json.dump(krw, open(os.path.join(OUT, "_markets.json"), "w"), ensure_ascii=False, indent=0)

for i, m in enumerate(krw):
    if i % NSHARD != SHARD:
        continue
    code = m["market"]
    path = os.path.join(OUT, f"{code}.csv")
    if os.path.exists(path):
        continue
    rows, to = [], ""
    while True:
        url = f"https://api.upbit.com/v1/candles/days?market={code}&count=200" + (f"&to={to}" if to else "")
        data = get(url)
        time.sleep(0.13)
        if not data:
            break
        rows += data
        earliest = data[-1]["candle_date_time_utc"]
        if len(data) < 200 or earliest[:10] <= START:
            break
        to = earliest + "Z"
    rows.sort(key=lambda r: r["candle_date_time_utc"])
    seen = set()
    with open(path + ".tmp", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "krw_turnover", "volume"])
        for r in rows:
            d = r["candle_date_time_utc"][:10]
            if d in seen:
                continue
            seen.add(d)
            w.writerow([d, r["opening_price"], r["high_price"], r["low_price"], r["trade_price"],
                        r["candle_acc_trade_price"], r["candle_acc_trade_volume"]])
    os.replace(path + ".tmp", path)
    print(i, code, len(seen), rows[0]["candle_date_time_utc"][:10] if rows else "-", flush=True)
print("done")
