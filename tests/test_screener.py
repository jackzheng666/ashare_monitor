import pandas as pd
from src.screener import score_snapshot

def test_exclude_st():
    base={'代码':['600001','600002'],'名称':['普通公司','*ST风险'],
      '最新价':[12,12],'涨跌幅':[3,3],'成交额':[2e8,2e8],
      '换手率':[4,4],'量比':[1.8,1.8]}
    result=score_snapshot(pd.DataFrame(base))
    assert result['代码'].tolist()==['600001']
