"""Controlled synthetic benchmark. Development and frozen runs have disjoint seeds."""
import argparse,json,subprocess
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from scipy.stats import wilcoxon
from .monthly import monthly,contract,I,P,S,A,C
from .generator import Config,Generator

DEV={0,1,2,3,4,7,8,11,42}
SIZES=(600,3000,12000)
ATTR="exact_duplicates near_duplicates overpayments bank_redirects fictitious_suppliers split_purchases inactive_payments".split()
def config(seed,size,p,enriched,stress):
    rng=np.random.default_rng(seed+3091)
    # Approximate affected payment counts per scheme; disclose realized prevalence.
    counts=np.ones(7,dtype=int) if enriched else rng.poisson(size*p/7/np.array([1,1,1,1,7.5,2.5,1]))
    return Config(seed=seed,intensity=size/600,stress=stress,**{"n_"+a:int(n) for a,n in zip(ATTR,counts)})

def fsr(n,f,budget):
    if not n:return np.nan
    vals=np.array(list(n.values()),float); target=min(budget,sum(vals));lo,hi=0.,max(vals)
    for _ in range(60):
        mid=(hi+lo)/2
        if np.minimum(vals,mid).sum()<target:lo=mid
        else:hi=mid
    caps=np.minimum(vals,hi)
    return float(np.mean(np.minimum([f.get(key,0) for key in n],caps)/caps))

def scores(pay,month):
    df=pay[pay.Payment_Date.str[:7]<=month].copy()
    if df.empty:return {}
    hist=df.Payment_Date.str[:7]<month; cur=~hist
    if not cur.any() or hist.sum()<20:return {}
    x=np.column_stack([np.log1p(df.Payment_Amount_Local),pd.to_datetime(df.Payment_Date).dt.dayofweek,
                       (df.Entered_By==df.Approved_By).astype(int),(df.Payment_Type=="ACH").astype(int)])
    train=x[hist];test=x[cur]
    clf=IsolationForest(n_estimators=64,max_samples=min(256,len(train)),random_state=117,n_jobs=1).fit(train)
    # Two outlier scores combined as empirical percentiles against past payments.
    def hbos(z):
        h=np.zeros(len(z))
        for j in range(x.shape[1]):
            freq,edges=np.histogram(train[:,j],bins=10)
            ix=np.clip(np.searchsorted(edges,z[:,j],side="right")-1,0,9)
            h-=np.log((freq[ix]+1)/(len(train)+10))
        return h
    def pct(base,v):return np.searchsorted(np.sort(base),v,side="right")/len(base)
    val=(pct(-clf.score_samples(train),-clf.score_samples(test))+pct(hbos(train),hbos(test)))/2
    return dict(zip(df.loc[cur,"Payment_ID"],val))

def one(seed,size,p,enriched,stress):
    t=Generator(config(seed,size,p,enriched,stress)).run(); lab=t.pop("labels"); t=contract(t,{"mode":"synthetic_snapshot","currency":"USD","months":12,"invoice_rows":"one_per_invoice"}); pack=monthly(t,"2025-07-01")
    a,items,summary,links=[pack[k] for k in ("raw_alerts","review_items","self_approval_summary","alert_links")]
    months=list(pack["monthly_load"].month); end="2026-06-30"
    valid={I:set(t[I].loc[t[I].Entered_Date<=end,"Invoice_ID"]),P:set(t[P].loc[t[P].Payment_Date<=end,"Payment_ID"]),S:set(t[S].loc[t[S].Entered_Date<=end,"Supplier_Account_ID"]),C:set((t[C].Supplier_Account_ID+"@"+t[C].Changed_Date)[t[C].Changed_Date<=end])}
    lab=lab.loc[[r.record_id in valid.get(r.table,set()) for r in lab.itertuples()]]
    typed=lab.drop_duplicates("scheme_id").set_index("scheme_id").type.to_dict();n=pd.Series(list(typed.values()),dtype=str).value_counts().to_dict()
    truth=defaultdict(set)
    for r in lab.itertuples():truth[r.table,r.record_id].add(r.scheme_id)
    # Count primary records only, not automatic credit for opening an entire supplier history.
    pri=links.merge(a[["alert_id","table","record_id","rule"]],on=["alert_id","table","record_id"])
    pri=pri[~pri.rule.isin(["R13","R14"])]
    recs=defaultdict(set); exact=defaultdict(set);exact_amount={}
    for r in pri.itertuples():
        recs[r.destination].add((r.table,r.record_id))
        if r.rule=="R01":
            exact[r.destination].add((r.table,r.record_id))
            exact_amount[r.destination]=max(exact_amount.get(r.destination,0),float(a.loc[a.alert_id==r.alert_id,"amount"].iloc[0]))
    appl=t[A].merge(t[P][["Payment_ID","Payment_Date"]],on="Payment_ID")
    candidates=[]; scores_by_dest={}
    for m in months:
        sc=scores(t[P],m); inv_sc=appl.loc[appl.AP_Application_Date.str[:7]<=m].assign(score=lambda d:d.Payment_ID.map(sc)).groupby("Invoice_ID").score.max().dropna().to_dict()
        for r in items[items.month==m].itertuples():candidates.append((m,r.item_id,2*r.tier,float(r.largest_amount) if pd.notna(r.largest_amount) else 0))
        for r in summary[summary.month==m].itertuples():candidates.append((m,f"summary:{m}:{r.user}",3,float(r.payments_dollars+r.invoices_dollars)))
        for mm,d,_,_ in candidates:
            if m==mm:scores_by_dest[d]=max([sc.get(r,0) if tb==P else inv_sc.get(r,0) if tb==I else 0 for tb,r in recs[d]] or [0])
    found_pack=set().union(*(truth[r] for dest,group in recs.items() if not dest.startswith("summary:") for r in group))
    raw=len(a); lines=len(candidates);paycount=len(valid[P]);out=[]
    base=dict(seed=seed,size=size,family="enriched" if enriched else "prevalence",target=0 if enriched else p,stress=stress,invoices=len(valid[I]),payments=paycount,
              realized=len(set(lab.loc[lab.table==P,"record_id"]))/max(1,paycount),schemes=len(typed),raw=raw,lines=lines,
              reduction=1-lines/raw if raw else None,pack_retention=len(found_pack)==len(typed),trace=set(a.alert_id)==set(links.alert_id))
    for k in (5,10,20):
        pressure=sum(sum(mm==m for mm,*_ in candidates)>k for m in months)/12
        for method in ("B0","B1","B2","B3"):
            rr=exact if method=="B0" else recs
            selected=[]
            for m in months:
                pool=[v for v in candidates if v[0]==m and (method!="B0" or v[1] in exact)]
                def rank(v):
                    _,d,tier,amt=v
                    if method=="B0":amt=exact_amount[d]
                    return (tier if method in ("B1","B3") else 0,-scores_by_dest[d] if method in ("B2","B3") else 0,-amt,d)
                selected+=sorted(pool,key=rank)[:k]
            hits=[set() if v[1].startswith("summary:") else set().union(*(truth[r] for r in rr[v[1]])) for v in selected]
            found=set().union(*hits);f=pd.Series([typed[j] for j in found],dtype=str).value_counts().to_dict()
            paid_ids={r for v in selected if not v[1].startswith("summary:") for tb,r in rr[v[1]] if tb==P and truth[tb,r]}
            dollars=t[P].loc[t[P].Payment_ID.isin(paid_ids),"Payment_Amount_Local"].sum()
            first={}
            for v,h in zip(selected,hits):
                for j in h:first.setdefault(typed[j],v[0])
            out.append(dict(**base,k=k,method=method,pressure=pressure,reviewed=len(selected),fsr=fsr(n,f,12*k),
                 coverage=len(f)/len(n) if n else None,recall=len(found)/len(typed) if typed else None,
                 precision=sum(bool(h) for h in hits)/len(hits) if hits else None,found_by_type=json.dumps(f),present_by_type=json.dumps(n),first_hit=json.dumps(first),linked_planted_payment_dollars=round(dollars,2)))
    return out

def jobs():
    seed=700000
    for size,reps in zip(SIZES,(100,30,30)):
        for p in (.001,.005,.01,0.):
            for i in range(reps if p else 30):
                seed+=1
                if seed in DEV:raise ValueError("Development seed collision")
                yield seed,size,p,not p,i%2==1

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--formal",action="store_true");parser.add_argument("--out",required=True);args=parser.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    if args.formal:
        git=lambda *x:subprocess.check_output(["git",*x],text=True).strip()
        if git("rev-parse","HEAD")!=git("rev-parse","FIRA-eval-freeze^{commit}") or git("status","--porcelain","--untracked-files=no") or not Path("docs/evaluation-v0.4.md").read_text().startswith("# FROZEN"):
            raise SystemExit("Use a clean author-approved frozen commit and tag, per README.")
        cases=list(jobs())
    else:cases=[(42,600,0,True,False),(7,600,.001,False,False)]
    rows=[]
    for case in cases:
        subset=one(*case); rows+=subset
        pd.DataFrame(subset).to_csv(out/f"seed-{case[0]}.csv",index=False)
    df=pd.DataFrame(rows);df.to_csv(out/"all.csv",index=False)
    result=[]
    for keys,g in df[df.k==10].groupby(["size","family","target"]):
        for metric in ["fsr","coverage"]:
            v=g.pivot(index="seed",columns="method",values=metric); d=(v.B3-v.B1).dropna().to_numpy()
            rng=np.random.default_rng(2301);ci=np.quantile(rng.choice(d,(2000,len(d))).mean(1),[.025,.975]) if len(d) else [None,None]
            result.append(dict(size=keys[0],family=keys[1],target=keys[2],metric=metric,n=len(d),pressure=g.pressure.mean(),delta=d.mean() if len(d) else None,lo=ci[0],hi=ci[1],p=wilcoxon(d).pvalue if len(d) and np.any(d) else None))
    pd.DataFrame(result).to_csv(out/"paired.csv",index=False)
if __name__=="__main__":main()
