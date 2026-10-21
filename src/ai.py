import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from .settings import STORE, MODEL, MAX_CALLS, MAX_AGE

BUDGET = STORE / 'ai_usage.json'

def analyze(payload, snapshot_age_s, during_session):
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('请先在 .env 设置 OPENAI_API_KEY')
    if not during_session or snapshot_age_s > MAX_AGE:
        raise RuntimeError('非交易时间或行情过期：禁止生成盘中可执行买入建议')
    today = datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
    usage = {'date':today,'calls':0}
    if BUDGET.exists():
        try: usage = json.loads(BUDGET.read_text())
        except Exception: pass
    if usage.get('date') != today: usage = {'date':today,'calls':0}
    if usage['calls'] >= MAX_CALLS: raise RuntimeError('今天的AI调用次数已达预算上限')
    # Count attempts before call, so a repeated failure cannot cause unlimited billable retries.
    usage['calls'] += 1
    BUDGET.write_text(json.dumps(usage))
    prompt = '''你是A股交易风险研究助手。只依据提供的定量数据和新闻标题；新闻与政策未核实就注明未核实。
不得保证上涨，不得把评分当概率，不得虚构实时行情、机构资金或具体事件。
最多分析5只；根据支撑/压力给出条件式关注位、无效位和风险；若数据不足建议观望。
特别考虑A股T+1、100股交易单位及涨跌停板；不要声称执行了交易。中文回答，简洁。'''
    client = OpenAI(timeout=28.0, max_retries=2)
    res = client.responses.create(model=MODEL, instructions=prompt,
                                  input=json.dumps(payload,ensure_ascii=False,default=str)[:22000],
                                  max_output_tokens=1100)
    return res.output_text
