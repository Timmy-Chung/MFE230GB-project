"""EM floats companion to equity_spillover.py: reruns constructions A-D, the dollar-component decomposition, placebo and checks on the nine floating EM currencies (slide 8). Run: python3 equity_spillover_floats.py  (needs the data/ folder; writes output/equity_floats.json)."""
import sys, json, numpy as np, pandas as pd
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parent))
import equity_spillover as es
P = es.build_panel("EM")
cols = [c for c, v in P["regime"].items() if v == "float"]
print("floats", cols)
Q = {k: (v[cols] if isinstance(v, pd.DataFrame) else v) for k, v in P.items() if k != "regime"}; Q["regime"] = {c: "float" for c in cols}
out = {"currencies": cols}
def tt(r): return {"train": es.stats(r.loc[:es.SPLIT]).get("sharpe"), "test": es.stats(r.loc[es.SPLIT:]).get("sharpe"), "full": es.stats(r).get("sharpe")}
# four constructions at 6m
rA,_,_ = es.run_spec(Q,"EM","local",6,"tercile",1); rB,_,_ = es.run_spec(Q,"EM","vol_adj",6,"rank",1)
rC,toC,wC = es.run_spec(Q,"EM","rel_us",6,"dollar",1); rD,_,_ = es.run_spec(Q,"EM","local",6,"dollar",1)
out["A"],out["B"],out["C"],out["D"] = tt(rA),tt(rB),tt(rC),tt(rD)
for k in (3,12):
    r,_,_ = es.run_spec(Q,"EM","rel_us",k,"dollar",1); out[f"C_k{k}"]=tt(r)
st = es.stats(rC); out["C_full"] = st
out["sub"] = {f"{a}-{b}": es.stats(rC.loc[a:b]).get("sharpe") for a,b in [("2000","2007"),("2008","2012"),("2013","2019"),("2020","2026")]}
net = wC.sum(axis=1); basket = Q["xr"].mean(axis=1)
us_eq = es.equity("USD").reindex(Q["E"].index); rel_avg = us_eq.diff(6) - Q["E"].diff(6).mean(axis=1)
pos = -np.sign(rel_avg); r_time = (pos.shift(1)*basket).loc[es.START:] - es.COST["EM"]*pos.diff().abs().fillna(0).loc[es.START:]
r_cs = rC - (net.shift(1)*basket).loc[es.START:]
out["dollar_alone"] = tt(r_time); out["dollar_alone_full"]=es.stats(r_time); out["dollar_removed"] = tt(r_cs); out["dollar_removed_full"]=es.stats(r_cs)
out["turnover"] = round(float(toC.mean()*12),1); out["net_fc"] = round(float(net.loc[es.START:].mean()),2); out["share_long_usd"]=round(float((net.loc[es.START:]<0).mean()),2)
rng = np.random.default_rng(1); sh=[]; sig = es.signal_matrix(Q,"rel_us",6)
for _ in range(200):
    shift=int(rng.integers(12,200)); ps=pd.DataFrame(np.roll(sig.values,shift,axis=0),index=sig.index,columns=sig.columns)
    rp,_,_ = es.backtest(es.weights_from_signal(ps,"dollar",3), Q["xr"], es.COST["EM"], 1); sh.append(es.stats(rp.loc[es.START:]).get("sharpe"))
sh=np.array([x for x in sh if x is not None]); out["placebo_p"]=round(float((sh>=st["sharpe"]).mean()),3)
r_sk,_,_ = es.run_spec(Q,"EM","rel_us",6,"dollar",1,skip=1); out["skip"]=es.stats(r_sk).get("sharpe")
r_sp,_,_ = es.run_spec(Q,"EM","rel_us",6,"dollar",1,ret_kind="spot"); out["spot_only"]=es.stats(r_sp).get("sharpe")
w2 = es.weights_from_signal(sig,"dollar",3); r2,_,_ = es.backtest(w2, Q["xr"], 0.0002, 1); out["at_2bp"]=es.stats(r2.loc[es.START:]).get("sharpe")
wealth=(1+rC.fillna(0)).cumprod(); dd=wealth/wealth.cummax()-1; out["mdd"]={"dd":round(float(dd.min()),3),"trough":str(dd.idxmin().date()),"peak":str(wealth.loc[:dd.idxmin()].idxmax().date())}
ann = rC.groupby(rC.index.year).sum(); out["years_pos"]=f"{int((ann>0).sum())} of {len(ann)}"
usd = es.load_fred("DTWEXBGS") if hasattr(es,"load_fred") else None
try:
    u = es.monthly_period_csv("DTWEXBGS") if hasattr(es,"monthly_period_csv") else None
except Exception as e: u=None
lastd = wC.index[(wC.abs().sum(axis=1)>0)][-1]
out["current"]={"date":str(lastd.date()),"longs":[c for c in wC.columns if wC.loc[lastd,c]>0],"shorts":[c for c in wC.columns if wC.loc[lastd,c]<0]}
out["worst"]=[{"date":str(d.date()),"ret":round(float(v)*100,2),"net_fc":round(float(net.shift(1).get(d,np.nan)),2)} for d,v in rC.nsmallest(4).items()]
cum_book = es.equity_curve(rC); cum_dt = es.equity_curve(r_time)
out["curve_book"]=[(str(d.date()),round(float(v),4)) for d,v in cum_book.items()]; out["curve_dollar"]=[(str(d.date()),round(float(v),4)) for d,v in cum_dt.items()]
json.dump(out, open(str(Path(__file__).resolve().parent / 'output' / 'equity_floats.json'),'w'), indent=1, default=str)
for k in ("A","B","C","D","C_k3","C_k12","dollar_alone","dollar_removed","sub","turnover","net_fc","share_long_usd","placebo_p","skip","spot_only","at_2bp","mdd","years_pos","current","worst"): print(k, out[k])
print("C_full", {k:v for k,v in st.items()}); print("max curve", cum_book.max(), cum_dt.max(), cum_dt.min(), cum_book.min())
