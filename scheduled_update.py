"""
定时数据更新 — 每12小时从竞彩+ESPN获取最新数据
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, json, logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent / "data" / "bundled"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.sporttery.cn/',
    'Origin': 'https://www.sporttery.cn',
}

def update_results():
    """从竞彩获取最新赛果"""
    try:
        url = 'https://webapi.sporttery.cn/gateway/jc/football/getMatchResultV1.qry'
        r = requests.get(url, params={'matchPage': 1, 'matchBeginDate': '2026-06-12', 'matchEndDate': '2026-07-20', 'leagueId': 72}, headers=HEADERS, timeout=15)
        data = r.json()
        if data.get('success'):
            results = data['value'].get('matchResult', [])
            results_file = DATA_DIR / "live_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({'updated_at': datetime.now().isoformat(), 'results': results}, f, ensure_ascii=False, indent=2)
            logger.info(f'竞彩赛果: {len(results)} 场')
    except Exception as e:
        logger.warning(f'赛果获取失败: {e}')

def main():
    logger.info('=== 定时更新开始 ===')
    update_results()
    logger.info('=== 定时更新完成 ===')

if __name__ == '__main__':
    main()
