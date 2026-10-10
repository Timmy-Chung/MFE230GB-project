"""List the Binance public-archive symbols (spot and USDT-margined perpetual klines).

Usage: python -I src/dl_lists.py data/raw   ->  data/raw/symbol_lists.json
Run after dl_upbit.py (it stores Upbit's market list alongside).
"""
import json
import os
import re
import sys
import urllib.request

RAW = sys.argv[1]
UA = {"User-Agent": "Mozilla/5.0 (research; MFE230GB replication)"}


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return r.read().decode()


def s3_dirs(prefix):
    out, marker = [], ""
    while True:
        b = get(f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix={prefix}&marker={marker}")
        ps = re.findall(r"<Prefix>([^<]+)</Prefix>", b)[1:]
        out += [p[len(prefix):].strip("/") for p in ps]
        if "<IsTruncated>true</IsTruncated>" in b:
            nm = re.findall(r"<NextMarker>([^<]+)</NextMarker>", b)
            marker = nm[0] if nm else ps[-1]
        else:
            return out


upbit = json.load(open(os.path.join(RAW, "upbit", "_markets.json")))
spot = s3_dirs("data/spot/monthly/klines/")
perp = s3_dirs("data/futures/um/monthly/klines/")
json.dump({"upbit": upbit, "spot": spot, "perp": perp}, open(os.path.join(RAW, "symbol_lists.json"), "w"))
print("spot dirs", len(spot), "perp dirs", len(perp))
