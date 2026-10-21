import json
import os
from pathlib import Path
import pandas as pd
from .settings import STORE

def atomic_csv(df, name):
    target=STORE / name
    temp=STORE / (name+'.tmp')
    df.to_csv(temp,index=False,encoding='utf-8-sig')
    os.replace(temp,target)

def load(name):
    p=STORE/name
    return pd.read_csv(p,dtype={'代码':str}) if p.exists() else pd.DataFrame()

def metadata(**kwargs):
    p=STORE/'status.json'; t=STORE/'status.json.tmp'
    t.write_text(json.dumps(kwargs,ensure_ascii=False,indent=2))
    os.replace(t,p)

def status():
    p=STORE/'status.json'
    try: return json.loads(p.read_text())
    except Exception:return {}
