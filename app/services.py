import numpy as np
import pandas as pd
import networkx as nx
from .db import connect
from ml.model import FEATURES,load_models,load_drift_model,train_behavior_model,train_progress_model,train_drift_model

def get_df(con,uid):
    return pd.read_sql_query(
        "SELECT * FROM interactions WHERE user_id=? ORDER BY event_date",con,params=[uid]
    )

def clamp(x,lo=0,hi=1):
    return max(lo,min(hi,float(x)))

def ensure_models(df):
    if df.empty:return
    b,p=load_models()
    if b is None:train_behavior_model(df)
    if p is None:train_progress_model(df)
    if load_drift_model() is None:train_drift_model(df)

def profile(con,uid):
    df=get_df(con,uid)
    if df.empty:
        return {
            "behavioral_confidence":.12,
            "completion_rate":0.0,
            "avg_switches":0.0,
            "avg_duration":0.0,
            "focus_pattern":"Not enough data yet",
            "top_task":"Getting started",
            "consistency":.12,
            "adaptability":.20,
            "learning_style":"Learning from your activity",
            "focus_window":"Discovering your best window"
        }
    r=df.tail(30)
    morning=df[df.hour.between(7,11)]
    evening=df[df.hour.between(17,21)]
    morning_rate=morning.completed.mean() if not morning.empty else 0
    evening_rate=evening.completed.mean() if not evening.empty else 0
    focus="Morning" if morning_rate>=evening_rate else "Evening"
    return {
        "behavioral_confidence":clamp(.62+.35*min(1,len(df)/90)),
        "completion_rate":r.completed.mean(),
        "avg_switches":r.task_switches.mean(),
        "avg_duration":r.duration_min.mean(),
        "focus_pattern":focus,
        "top_task":r.task_type.mode().iloc[0],
        "consistency":clamp(1-r.task_switches.std()/10 if len(r)>2 else .7),
        "adaptability":clamp(.55+(df.tail(45).completed.mean()-df.head(45).completed.mean())),
        "learning_style":"Practical & visual" if r.help_requests.mean()<1.2 else "Guided & example-driven",
        "focus_window":"08:00–11:00" if focus=="Morning" else "18:00–21:00"
    }

def prediction(con,uid):
    df=get_df(con,uid)
    if df.empty:
        return ([
            {"label":"Learning", "prob":28.0},
            {"label":"Deep Work", "prob":25.0},
            {"label":"Project", "prob":22.0},
            {"label":"Revision", "prob":15.0},
            {"label":"Admin", "prob":10.0},
        ], .12)
    ensure_models(df)
    b,_=load_models()
    x=df.tail(12)[FEATURES].mean().to_frame().T
    probs=b.predict_proba(x)[0]
    pairs=sorted(zip(b.classes_,probs),key=lambda z:z[1],reverse=True)
    return [{"label":k,"prob":round(v*100,1)} for k,v in pairs[:5]],float(pairs[0][1])

def factors(con,uid):
    p=profile(con,uid)
    if get_df(con,uid).empty:
        return [
            ("Behavioral evidence",.12,"BUILDING"),
            ("Routine stability",.18,"BUILDING"),
            ("Preference signals",.15,"BUILDING"),
            ("Goal alignment",.20,"READY"),
            ("Prediction confidence",.12,"EARLY"),
        ]
    return [
        ("Morning completion advantage",.86 if p["focus_pattern"]=="Morning" else .61,"+32%"),
        ("Low task-switch tendency",clamp(1-p["avg_switches"]/10),"+24%"),
        ("Consistency trend",p["consistency"],"+18%"),
        ("Goal alignment",.78,"+14%"),
        ("Recent preference stability",.71,"+10%")
    ]

def drift(con,uid):
    df=get_df(con,uid)
    if len(df)<30:return {"status":"Insufficient data","score":0}
    model=load_drift_model()
    recent=df.tail(15)[FEATURES]
    anomaly=float(np.mean(model.decision_function(recent)<0))
    a=df.head(30)[FEATURES].mean();b=df.tail(30)[FEATURES].mean()
    shift=float(np.mean(np.abs((b-a)/(np.abs(a)+1e-6))))
    score=clamp(.55*anomaly+.45*min(1,shift*2.2))
    return {"status":"Behavioral drift detected" if score>.30 else "Stable pattern","score":score}

def goals(con,uid):
    return [dict(r) for r in con.execute(
        "SELECT * FROM goals WHERE user_id=? ORDER BY id",[uid]).fetchall()]

def goal_risk(con,uid):
    df=get_df(con,uid); gs=goals(con,uid)
    if df.empty:return []
    r=df.tail(21)
    completion=r.completed.mean()
    consistency=clamp(1-r.task_switches.mean()/10)
    revision=(r.task_type=="Revision").mean()
    risk=clamp(.35*(1-completion)+.25*(1-consistency)+.25*(1-completion)+.15*(1-revision))
    out=[]
    for g in gs:
        adj=clamp(risk+(.10 if g["progress"]<.5 else 0))
        label="High" if adj>.48 else "Medium" if adj>.28 else "Low"
        out.append({"goal":g["title"],"risk":adj,"label":label,"progress":g["progress"]})
    return out

def what_if(con,uid,study_hours=2,sleep=7,exercise=3,switches=3):
    df=get_df(con,uid)
    if df.empty:
        current=.12
        focus="Discovering your best window"
        confidence=.12
    else:
        current_hours=max(.25,df.tail(21).duration_min.sum()/60/21)
        current=clamp(.52+.24*min(current_hours/2,1)+.14*(1-min(df.tail(21).task_switches.mean()/10,1))+.10*df.tail(21).completed.mean())
        focus=profile(con,uid)["focus_window"]
        confidence=.58+.3*min(1,len(df)/90)
    scenario=clamp(.42+.28*min(study_hours/2,1)+.08*min(sleep/8,1)+.08*min(exercise/5,1)+.14*(1-min(switches/10,1)))
    return {"current":round(current*100,1),"scenario":round(scenario*100,1),
            "delta":round((scenario-current)*100,1),"confidence":round(confidence,2),
            "focus_window":focus}

def decision_sim(con,uid,a,b):
    p=profile(con,uid)
    def score(text):
        t=text.lower();s=50;reasons=[]
        rules=[(("remote","flexible"),18,"Flexibility preference"),
               (("growth","learning"),14,"Growth orientation"),
               (("salary","high"),8,"Reward preference"),
               (("commute","long"),-12,"Long-commute friction"),
               (("structured","fixed"),7,"Structured-routine compatibility")]
        for words,pts,label in rules:
            if any(w in t for w in words):s+=pts;reasons.append((label,pts))
        return clamp(s/100),reasons
    sa,ra=score(a);sb,rb=score(b);total=sa+sb or 1;pa=sa/total;pb=sb/total
    return {"a":round(pa*100,1),"b":round(pb*100,1),"ra":ra,"rb":rb,
            "confidence":round(abs(pa-pb)*.75+.25,2)}

def knowledge_graph():
    edges=[("Python","NumPy"),("NumPy","Pandas"),("Statistics","Machine Learning"),
           ("Probability","Machine Learning"),("Machine Learning","Deep Learning"),
           ("Deep Learning","Deployment"),("Flask","Deployment"),("Deep Learning","AI Projects")]
    g=nx.DiGraph();g.add_edges_from(edges)
    return [{"id":n} for n in g.nodes()],[{"source":a,"target":b} for a,b in g.edges()]

def timeline(con,uid):
    df=get_df(con,uid)
    if df.empty:return []
    parts=np.array_split(df,3)
    labels=["Explorer Phase","Learning Phase","Goal-Oriented Phase"]
    colors=["cyan","violet","green"]
    return [{"period":labels[i],"pattern":"High task switching" if x.task_switches.mean()>3 else "Consistent deep work",
             "focus":round(x.completed.mean()*100),"duration":round(x.duration_min.mean()),"color":colors[i]}
            for i,x in enumerate(parts)]

def analytics(con,uid):
    r=get_df(con,uid).tail(30)
    if r.empty:
        return {"sessions":0,"completion":0,"avg_duration":0,"switches":0,"difficulty":0}
    return {"sessions":len(r),"completion":round(r.completed.mean()*100),"avg_duration":round(r.duration_min.mean()),
            "switches":round(r.task_switches.mean(),1),"difficulty":round(r.difficulty.mean(),1)}
