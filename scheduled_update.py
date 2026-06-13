"""
定时数据更新 — 从 ESPN 获取最新赛程和赛果

用法：
    # 单次更新
    python scheduled_update.py

    # 定时更新（每2小时）
    python scheduled_update.py --schedule

    # 启动前更新
    python scheduled_update.py --startup
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests, json, logging, time, argparse
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent / "data" / "bundled"

# ESPN API 配置（多个端点）
ESPN_URLS = [
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world.cup/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world.cup.2026/scoreboard",
    # 添加日期参数的端点
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260612",
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260613",
    # 尝试其他日期格式
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260612-20260613",
]

def update_from_espn():
    """从 ESPN 获取所有比赛数据（包括已结束的）"""
    all_events = []

    for url in ESPN_URLS:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])

                if events:
                    all_events.extend(events)
                    logger.info(f'从 {url} 获取到 {len(events)} 场比赛')
            else:
                logger.warning(f'ESPN API 返回状态码: {response.status_code} ({url})')
        except Exception as e:
            logger.warning(f'ESPN 数据获取失败: {e} ({url})')

    # 去重（根据比赛 ID）
    seen_ids = set()
    unique_events = []
    for event in all_events:
        event_id = event.get("id")
        if event_id not in seen_ids:
            seen_ids.add(event_id)
            unique_events.append(event)

    if unique_events:
        # 保存到文件
        results_file = DATA_DIR / "live_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'source': 'espn',
                'events': unique_events
            }, f, ensure_ascii=False, indent=2)

        logger.info(f'总共获取到 {len(unique_events)} 场比赛')
        return unique_events

    return []

def update():
    """执行一次更新"""
    logger.info('=== 数据更新开始 ===')
    events = update_from_espn()
    logger.info(f'=== 数据更新完成: {len(events)} 场比赛 ===')
    return events

def schedule_update(interval_hours=2):
    """
    定时更新

    Args:
        interval_hours: 更新间隔（小时）
    """
    logger.info(f'=== 启动定时更新（每 {interval_hours} 小时）===')

    while True:
        try:
            update()
        except Exception as e:
            logger.error(f'更新失败: {e}')

        # 等待下一次更新
        wait_seconds = interval_hours * 3600
        logger.info(f'等待 {interval_hours} 小时后再次更新...')
        time.sleep(wait_seconds)

def main():
    parser = argparse.ArgumentParser(description='数据更新脚本')
    parser.add_argument('--schedule', action='store_true',
                       help='启动定时更新（每2小时）')
    parser.add_argument('--startup', action='store_true',
                       help='启动前更新一次')
    parser.add_argument('--interval', type=int, default=2,
                       help='定时更新间隔（小时），默认2小时')

    args = parser.parse_args()

    if args.startup:
        # 启动前更新
        logger.info('=== 启动前更新 ===')
        update()
    elif args.schedule:
        # 定时更新
        schedule_update(args.interval)
    else:
        # 单次更新
        update()

if __name__ == '__main__':
    main()
