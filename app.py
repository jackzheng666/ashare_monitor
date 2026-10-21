import json
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from src.store import load,status
from src.data_source import histories,news
from src.screener import technical
from src.ai import analyze
from src.settings import MAX_AGE

TZ=ZoneInfo('Asia/Shanghai')
st.set_page_config(page_title='A股短线观察台',layout='wide')
st.title('A股短线观察台 · 研究用途')
st.caption('免费行情非交易所直连；延时、停牌、复权、交易日及接口可用性均须验证；不提供自动下单。')
meta=status(); raw=load('snapshot.csv'); ranked=load('ranked.csv'); sec=load('sectors.csv')
if raw.empty:
    st.warning('无行情。请在另一个终端先运行 python collector.py。'); st.stop()
try: age=int((datetime.now(TZ)-datetime.fromisoformat(meta['fetched_at'])).total_seconds())
except Exception: age=999999
fresh=meta.get('status')=='ok' and 0<=age<=MAX_AGE
live=fresh and bool(meta.get('during_session'))
cols=st.columns(4)
cols[0].metric('股票数量',len(raw));cols[1].metric('快照年龄',f'{age}s');cols[2].metric('行情状态','盘中待核实' if live else '非盘中/已过期')
cols[3].metric('候选股',len(ranked))
if not live: st.error('当前不符合盘中有效行情条件；请勿按本页面下盘中买单。')
st.warning('报价仅有采集时间戳，没有可验证的交易所撮合时间。即便显示盘中，也必须在券商终端核对实时买卖价。')
if meta.get('status')=='error': st.error('采集失败：'+meta.get('last_error',''))
if meta.get('sector_error'):st.warning('行业板块更新失败：'+meta['sector_error'])
t1,t2,t3=st.tabs(['短线候选','板块热度','AI分析与新闻'])
with t1:
    st.caption('启发式评分≠上涨概率。默认排除ST及部分市场板块，仅对主板按筛选门槛排序。')
    st.dataframe(ranked.head(40),hide_index=True,use_container_width=True)
    st.download_button('下载候选CSV', ranked.to_csv(index=False).encode('utf-8-sig'),'ranked.csv')
with t2:
    if sec.empty:st.info('行业板块暂无数据')
    else:
        sortcol='涨跌幅' if '涨跌幅' in sec.columns else sec.columns[0]
        st.dataframe(sec.sort_values(sortcol,ascending=False).head(30),hide_index=True,use_container_width=True)
with t3:
    available=ranked.head(20)['代码'].tolist() if not ranked.empty else []
    chosen=st.multiselect('请选择最多5只候选股',available,default=available[:3],max_selections=5)
    if st.button('采集日K线和相关新闻（接口可能较慢）'):
        packets=[]
        for code in chosen:
            match=ranked[ranked['代码']==code]
            try: ind=technical(histories(code))
            except Exception as e:ind={'状态':'历史行情错误: '+str(e)[:100]}
            headlines=news(code)
            packets.append({'代码':code,'快照':match.iloc[0].to_dict() if not match.empty else {},
                            '技术指标':ind,'新闻':headlines})
        st.session_state['packets']=packets
    packets=st.session_state.get('packets',[])
    if packets:
        st.json(packets,expanded=False)
        if st.button('调用 GPT 生成短线风险分析',disabled=not live):
            payload={'快照采集时间':meta.get('fetched_at'),'数据年龄秒':age,
                     '行业板块摘要':sec.head(10).to_dict('records') if not sec.empty else [],
                     '股票研究包':packets,'新闻注意':'新闻抓取结果未经独立核验，缺失不代表无事件'}
            try:st.session_state['ai_result']=analyze(payload,age,live)
            except Exception as e:st.error('AI请求失败：'+str(e))
    if st.session_state.get('ai_result'):st.markdown(st.session_state['ai_result'])
st.caption('刷新网页不会自行采集行情。collector.py 独立轮询；页面手动刷新可见新数据。')
