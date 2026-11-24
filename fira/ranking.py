"""Ordering policies for already-generated monthly review candidates."""
import numpy as np
import pandas as pd

# Each item gets exactly one bucket (first matching family in this fixed order).
FAMILIES = (("unsupported", {"R15"}), ("overpayment", {"R04"}),
            ("bank change", {"R05"}), ("supplier control", {"R06"}),
            ("duplicate", {"R01","R02","R03"}), ("split", {"R09"}),
            ("approval", {"R08"}), ("supplier record", {"R10","R11"}))

def family(rules):
    for name, codes in FAMILIES:
        if codes.intersection(rules): return name
    raise ValueError(f"No family for {rules}")

def order(pool, method, k, scores, families, exact_amount):
    """A pool contains one month only. No labels enter any ordering decision."""
    if k < 0: raise ValueError("negative review budget")
    if method == "B0":
        return sorted((v for v in pool if v[1] in exact_amount),
                      key=lambda v:(-exact_amount[v[1]],v[1]))[:k]
    if method not in {"B1","B2","B3","B3_min","B4"}: raise ValueError(method)
    summaries=sorted((v for v in pool if v[1].startswith("summary:")),key=lambda v:(-v[3],v[1]))
    items=[v for v in pool if not v[1].startswith("summary:")]
    if method=="B4":
        # Protect one highest-priority item; charge its family for that first slot.
        # Then take the least-represented available family, breaking equal counts
        # by its strongest item's severity/amount/ID. Never spend a slot twice.
        queues={}
        for v in sorted(items,key=lambda v:(v[2],-v[3],v[1])):
            queues.setdefault(families[v[1]],[]).append(v)
        counts={f:0 for f in queues}; ranked=[]
        while queues and len(ranked)<k:
            f=min(queues,key=lambda f:(counts[f],queues[f][0][2],-queues[f][0][3],queues[f][0][1]))
            ranked.append(queues[f].pop(0)); counts[f]+=1
            if not queues[f]: del queues[f]
    else:
        ranked=sorted(items,key=lambda v:(0 if method=="B2" else v[2],
                      0 if method=="B1" else -scores[v[1]],-v[3],v[1]))
    return (ranked+summaries)[:k]

def relative_features(pay):
    """For each payment, use only completed months preceding its own month."""
    month=pay.Payment_Date.str[:7]
    out=pd.DataFrame(0.,index=pay.index,columns=["log_amount_gap","method_surprise"])
    for m in sorted(month.unique()):
        past=pay.loc[month<m]; cur=pay.loc[month==m]
        groups=past.groupby("Supplier_Account_ID")
        count=cur.Supplier_Account_ID.map(groups.size()).fillna(0)
        enough=count>=3
        if not enough.any(): continue
        median=cur.Supplier_Account_ID.map(groups.Payment_Amount_Local.median())
        gap=np.log1p(cur.Payment_Amount_Local)-np.log1p(median)
        freq=past.groupby(["Supplier_Account_ID","Payment_Type"]).size()
        same=freq.reindex(pd.MultiIndex.from_frame(cur[["Supplier_Account_ID","Payment_Type"]])).fillna(0).to_numpy()
        # Rarity in this supplier's own prior payment mix (one pseudo-observation).
        rare=1-(same+1)/(count+1)
        out.loc[cur.index,:]=np.column_stack([gap.where(enough,0),rare.where(enough,0)])
    return out.to_numpy()
