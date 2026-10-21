import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
STORE = ROOT / 'data'
STORE.mkdir(exist_ok=True)
INTERVAL = max(60, int(os.getenv('FETCH_INTERVAL_SECONDS', '180')))
MAX_AGE = int(os.getenv('MAX_SNAPSHOT_AGE_SECONDS', '420'))
MAX_CALLS = int(os.getenv('MAX_AI_CALLS_PER_DAY', '10'))
MIN_TURNOVER = float(os.getenv('MIN_TURNOVER_YUAN', '100000000'))
MAX_PRICE = float(os.getenv('MAX_PRICE_YUAN', '95'))
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
