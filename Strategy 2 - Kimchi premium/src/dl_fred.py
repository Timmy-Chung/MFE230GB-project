"""Download FRED series: KRW/USD and JPY/USD noon NY rates, VIX, 3-month T-bill.

Usage: python -I src/dl_fred.py data/raw/fred

Uses curl (FRED's CSV endpoint can stall Python's urllib behind some proxies).
"""
import os
import subprocess
import sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
for sid in ["DEXKOUS", "DEXJPUS", "VIXCLS", "DTB3"]:
    path = os.path.join(OUT, f"{sid}.csv")
    for k in range(5):
        r = subprocess.run(["curl", "-s", "-f", "-m", "60", "-o", path,
                            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"])
        if r.returncode == 0 and os.path.getsize(path) > 1000:
            print(sid, "ok")
            break
        print(sid, "retry")
