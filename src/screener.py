import numpy as np
import pandas as pd
from .settings import MIN_TURNOVER, MAX_PRICE


def score_snapshot(raw):
    df = raw.copy()

    # 1. 排除 ST、退市及新上市股票
    names = df['名称'].fillna('').astype(str)

    excluded = (
        names.str.contains('ST', case=False, regex=False)
        | names.str.contains('退', regex=False)
        | names.str.startswith(('N', 'C'))
    )

    # 2. 筛选符合短线交易条件的股票
    eligible = (
        df['代码'].astype(str).str.startswith(
            ('00', '60', '601', '603', '605', '002')
        )
        & ~excluded
        & df['最新价'].between(2, MAX_PRICE)
        & (df['成交额'] >= MIN_TURNOVER)
        & df['换手率'].between(1.5, 18)
        & df['量比'].between(1.05, 5)
        & df['涨跌幅'].between(-1, 7.5)
        & (df['最新价'] > 0)
    )

    a = df.loc[eligible].copy()

    if a.empty:
        return a.assign(评分=pd.Series(dtype=float))

    # 3. 计算短线评分（不代表上涨概率）
    a['评分'] = (
        a['量比'].clip(upper=3) * 13
        + a['换手率'].clip(upper=12) * 2
        + a['涨跌幅'].clip(lower=0, upper=5) * 7
        + np.log1p(a['成交额'] / 1e8) * 7
    )

    # 4. 按评分从高到低排列
    return a.sort_values(
        '评分', ascending=False
    ).reset_index(drop=True)

def technical(hist):
    if len(hist) < 61: return {'状态':'不足61根日K线'}
    close = hist['收盘'].astype(float)
    volume = hist['成交量'].astype(float)
    if close.isna().any() or close.iloc[-1] <= 0: return {'状态':'历史数据异常'}
    ma = {f'MA{n}':float(close.rolling(n).mean().iloc[-1]) for n in [5,10,20,60]}
    ema12, ema26 = close.ewm(span=12,adjust=False).mean(), close.ewm(span=26,adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9,adjust=False).mean()
    delta=close.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rsi=float(100 - 100/(1 + gain.iloc[-1]/max(loss.iloc[-1],1e-12)))
    ma['MACD_DIF']=round(float(dif.iloc[-1]),3)
    ma['MACD_DEA']=round(float(dea.iloc[-1]),3)
    ma['RSI14']=round(rsi,1)
    ma['20日区间低']=round(float(hist['最低'].tail(20).min()),2)
    ma['20日区间高']=round(float(hist['最高'].tail(20).max()),2)
    ma['前5日均量比']=round(float(volume.iloc[-1]/max(volume.iloc[-6:-1].mean(),1)),2)
    ma['状态']='日K线指标（收盘前当日K线可能未完整）'
    return {k:round(v,3) if isinstance(v,float) else v for k,v in ma.items()}
