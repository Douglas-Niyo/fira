"""Twelve independent month-end snapshots of the supported synthetic AP profile."""
import json
from pathlib import Path
import pandas as pd
from .rules import Rules,load
from .review import build,TIER,CONTEXT

S,I,P,A,C,U="Supplier_Listing Invoices_Received Payments_Made AP_Cash_Application FIRA_Supplier_Change_Log User_Listing".split()
DATE={S:"Entered_Date",I:"Entered_Date",P:"Payment_Date",A:"AP_Application_Date",C:"Changed_Date"}
KEY={S:"Supplier_Account_ID",I:"Invoice_ID",P:"Payment_ID",A:"AP_Application_ID",U:"User_ID"}
COL={S:"Supplier_Account_ID Supplier_Account_Name Supplier_Physical_Street_Address1 Supplier_TIN_Hash Inactive_Date Entered_By Entered_Date Approved_By",I:"Invoice_ID Invoice_Number Invoice_Date Supplier_Account_ID Entered_By Entered_Date Entered_Time Approved_By Invoice_Amount_Local",P:"Payment_ID Supplier_Account_ID Payment_Date Payment_Amount_Local Amount_Credit_Debit_Indicator Entered_By Approved_By",A:"AP_Application_ID AP_Application_Date Supplier_Account_ID Payment_ID Invoice_ID AP_Application_Amount",C:"Supplier_Account_ID Changed_Field Changed_By Changed_Date Changed_Time",U:"User_ID"}
def contract(t,profile):
    if profile.get("mode")!="synthetic_snapshot" or profile.get("currency")!="USD" or profile.get("months")!=12: raise ValueError("Only the synthetic, single-USD, 12-month profile is supported")
    t={k:v.copy() for k,v in t.items() if k in COL}
    for k,cols in COL.items():
        missing=set(cols.split())-set(t[k])
        if missing: raise ValueError(f"Not tested: {k} missing {sorted(missing)}")
    for k,df in t.items():
        if "Supplier_TIN" in df: raise ValueError("Raw tax identifiers are unsupported")
        for col in df:
            if "currency" in col.lower() and not df[col].eq("USD").all(): raise ValueError("Only USD is supported")
        if k in DATE: pd.to_datetime(df[DATE[k]],format="%Y-%m-%d",errors="raise")
        for col in [x for x in df if x in ("Invoice_Amount_Local","Payment_Amount_Local","AP_Application_Amount")]:
            df[col]=pd.to_numeric(df[col],errors="raise")
            if not df[col].between(0,1e12).all(): raise ValueError("Unsupported amount or reversal")
    if not t[P].Amount_Credit_Debit_Indicator.eq("D").all(): raise ValueError("Only unreversed positive synthetic disbursements supported")
    grain=profile.get("invoice_rows")
    if grain=="allocated_by_purchase_order":
        df=t[I]; group=df.groupby("Invoice_ID",sort=False)
        if "Purchase_Order_ID" not in df or df.Purchase_Order_ID.eq("").any() or df.duplicated(["Invoice_ID","Purchase_Order_ID"]).any(): raise ValueError("Ambiguous invoice allocations")
        meta=[x for x in df if x not in ("Purchase_Order_ID","Invoice_Amount_Local","Invoice_ID")]
        if group[meta].nunique(dropna=False).gt(1).any().any(): raise ValueError("Conflicting invoice headers")
        t[I]=group.agg({**{c:"first" for c in meta},"Invoice_Amount_Local":"sum"}).reset_index()
    elif grain!="one_per_invoice": raise ValueError("Declare invoice row structure")
    for k,key in KEY.items():
        if t[k][key].eq("").any() or not t[k][key].is_unique: raise ValueError(f"Ambiguous {k} identifiers")
    for k in [I,P,A,C]:
        if not t[k].Supplier_Account_ID.isin(t[S].Supplier_Account_ID).all(): raise ValueError(f"Unknown supplier in {k}")
    for k,key in [(I,"Invoice_ID"),(P,"Payment_ID")]:
        vendor=t[k].set_index(key).Supplier_Account_ID
        if not t[A][key].map(vendor).eq(t[A].Supplier_Account_ID).all(): raise ValueError(f"Unreconciled application link: {key}")
    if t[C].duplicated(["Supplier_Account_ID","Changed_Date"]).any(): raise ValueError("Multiple supplier changes per day need distinct event IDs")
    return t

def monthly(t,start):
    start=pd.Timestamp(start)
    if start.day!=1: raise ValueError("Fiscal calendar must start on day 1")
    seen=set(); batches=[]
    calendar=pd.period_range(start,periods=12,freq="M").astype(str).tolist()
    for m in calendar:
        end=str(pd.Period(m).end_time.date())
        sub={k:(d.loc[d[DATE[k]]<=end].copy() if k in DATE else d.copy()) for k,d in t.items()}
        sub[S].loc[sub[S].Inactive_Date>end,"Inactive_Date"]=""
        # Synthetic approvals and static supplier identity are known on entry.
        # Do not use a later payment to explain an earlier application.
        sub[A]=sub[A][sub[A].Payment_ID.isin(sub[P].Payment_ID)&sub[A].Invoice_ID.isin(sub[I].Invoice_ID)]
        a=Rules(sub).run()
        keep=[]
        for r in a.itertuples():
            key=(r.rule,r.table,r.record_id,r.related_records if r.rule=="R05" else "")
            if key not in seen:
                seen.add(key); keep.append(r.Index)
        batch=a.loc[keep].copy(); batch["event_date"]=batch.date
        batch["date"]=batch.date.map(lambda d:max(d,m+"-01")); batch["observed_month"]=m
        batches.append(batch)
    a=pd.concat(batches,ignore_index=True); a["alert_id"]=[f"A{i:05d}" for i in range(1,len(a)+1)]
    items,summary,detail=build(a)
    by={(r.month,r.tier,r.supplier_id):r.item_id for r in items.itertuples()}
    links=[]
    for r in a.itertuples():
        if r.rule in TIER: dest=[by[r.observed_month,TIER[r.rule],r.supplier_id]]
        elif r.rule=="R07":dest=[f"summary:{r.observed_month}:{r.user_id}"]
        elif r.rule in CONTEXT:dest=[v for (m,tier,sid),v in by.items() if (m,sid)==(r.observed_month,r.supplier_id)] or ["context:"+r.alert_id]
        else:raise ValueError(r.rule)
        refs=[(r.table,r.record_id)]
        rt={"R04":P,"R05":C,"R11":S}.get(r.rule,I)
        refs.extend((rt,x) for x in r.related_records.split(";") if x)
        refs.extend((A,x) for x in r.application_ids.split(";") if x)
        if r.invoice_id:refs.append((I,r.invoice_id))
        for d in dest:
            for table,key in dict.fromkeys(refs):links.append((r.alert_id,r.observed_month,d,table,key))
    links=pd.DataFrame(links,columns=["alert_id","month","destination","table","record_id"])
    months=pd.DataFrame({"month":calendar})
    for name,df in [("items",items),("summaries",summary)]:
        months[name]=months.month.map(df.groupby("month").size()).fillna(0).astype(int)
    months["lines"]=months["items"]+months.summaries
    for k in [5,10,20]:months[f"over_{k}"]=months.lines>k
    return dict(raw_alerts=a,review_items=items,self_approval_summary=summary,self_approval_detail=detail,alert_links=links,monthly_load=months)

def export(data,out):
    src=Path(data); out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (src/"AP_Adjustments.csv").exists():raise ValueError("Adjustment import not supported")
    profile=json.loads((src/"profile.json").read_text())
    raw=load(src)
    srcmap=raw[I][["Invoice_ID"]+(["Purchase_Order_ID"] if "Purchase_Order_ID" in raw[I] else [])].copy()
    srcmap.insert(0,"source_csv_line",range(2,len(srcmap)+2))
    t=contract(raw,profile); pack=monthly(t,profile["start"])
    for name,df in {**pack,"invoice_source_rows":srcmap}.items(): df.to_csv(out/(name+".csv"),index=False)
    print(f"{len(pack['raw_alerts'])} raw alerts; {pack['monthly_load'].lines.sum()} displayed lines in 12 months")
    return pack
