"""Unlicensed public endpoints: best-effort snapshots, not exchange-level realtime."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import akshare as ak
import pandas as pd

TZ = ZoneInfo('Asia/Shanghai')

def now():
    return datetime.now(TZ)

def retry(fn, attempts=3):
    err = None
    for i in range(attempts):
        try:
            x = fn()
            if x is None or x.empty:
                raise ValueError('empty response')
            return x
        except Exception as e:
            err = e
            if i < attempts - 1:
                time.sleep(min(2 ** i, 4))
    raise RuntimeError(f'data feed unavailable: {str(err)[:200]}') from err

def snapshots():
    fetched = now()
    df = retry(ak.stock_zh_a_spot_em)
    fields = ['代码','名称','最新价','涨跌幅','成交额','换手率','量比','最高','最低','今开','昨收','成交量']
    missing = [c for c in fields if c not in df.columns]
    if missing: raise ValueError(f'Changed provider schema: {missing}')
    out = df[fields].copy()
    out['代码'] = out['代码'].astype(str).str.zfill(6)
    for c in fields[2:]: out[c] = pd.to_numeric(out[c], errors='coerce')
    out['抓取时间'] = fetched.isoformat()
    return out

def sectors():
    df = retry(ak.stock_board_industry_name_em)
    return df

def histories(code, days=140):
    end = now().date()
    start = end - timedelta(days=days * 2)
    df = retry(lambda: ak.stock_zh_a_hist(symbol=str(code).zfill(6), period='daily',
                                           start_date=start.strftime('%Y%m%d'),
                                           end_date=end.strftime('%Y%m%d'),adjust='qfq'))
    for c in ['收盘','最高','最低','成交量']:
        if c not in df.columns: raise ValueError(f'missing history field: {c}')
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.sort_values('日期').tail(days)

def news(code):
    # News endpoint frequently changes; failures must not block trading dashboard.
    try:
        df = retry(lambda: ak.stock_news_em(symbol=str(code).zfill(6)), attempts=2)
        return df.head(5).to_dict('records')
    except Exception:
        return []
