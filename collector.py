"""Run separately: python collector.py; no Streamlit background thread dependency."""
import time
from datetime import datetime, time as clock
from zoneinfo import ZoneInfo
from src.settings import INTERVAL
from src.data_source import snapshots,sectors,now
from src.screener import score_snapshot
from src.store import atomic_csv,metadata,status

TZ=ZoneInfo('Asia/Shanghai')
def is_market(nowdt):
    t=nowdt.time()
    return nowdt.weekday()<5 and (clock(9,30)<=t<=clock(11,30) or clock(13)<=t<=clock(15))

def run_once():
    fetched = now(); session=is_market(fetched)
    df=snapshots()
    if len(df)<1000: raise RuntimeError('全市场数量过少，可能是接口截断')
    atomic_csv(df,'snapshot.csv')
    atomic_csv(score_snapshot(df),'ranked.csv')
    sector_error=''
    try: atomic_csv(sectors(),'sectors.csv')
    except Exception as e:sector_error=str(e)[:200]
    metadata(fetched_at=fetched.isoformat(),during_session=session,count=len(df),
             status='ok',sector_error=sector_error,
             warning='抓取时间不等于交易所行情源时间，免费行情延时未验证')
    print(f'OK {fetched.isoformat()} {len(df)} tickers; sector error={sector_error}')

def main():
    while True:
        try:
            # Avoid hammering API outside the market, but allow startup snapshot.
            run_once()
        except Exception as e:
            prev=status()
            metadata(**{**prev,'status':'error','last_error':str(e)[:300]})
            print('ERROR:',e)
        time.sleep(INTERVAL if is_market(now()) else 900)
if __name__=='__main__': main()
