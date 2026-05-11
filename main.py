#!/usr/bin/env python3
"""
Web3代币均线密集度监控程序

功能:
- 监控BTC、BNB、SOL、ETH等代币的均线密集度
- 支持1h、4h、1d时间周期
- 计算MA均线密集度
- 达标时发送Telegram告警
"""

import os
import sys
import argparse
from loguru import logger

sys.path.insert(0, os.path.dirname(__file__))

from src.core.config import Config
from src.monitor.monitor import MAMonitor
from src.notification.telegram import TelegramNotifier


def create_parser():
    """创建参数解析器"""
    return argparse.ArgumentParser(
        description="Web3代币均线密集度监控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 main.py              # 默认运行
  python3 main.py -h           # 显示帮助
  python3 main.py -b           # 熊市模式
  python3 main.py -i 600       # 自定义间隔
        """
    )


def parse_args():
    """解析命令行参数"""
    parser = create_parser()
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="配置文件路径"
    )
    parser.add_argument(
        "-b", "--bear",
        action="store_true",
        help="熊市模式 (使用更严格的阈值)"
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=None,
        help="检查间隔(秒)"
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    if args.interval is not None and args.interval <= 0:
        logger.error("检查间隔必须大于0")
        sys.exit(1)
    
    config = Config(args.config)
    
    is_bull_market = not args.bear
    
    telegram = TelegramNotifier(
        bot_token=config.telegram_token,
        chat_id=config.telegram_chat_id
    )
    
    interval = args.interval if args.interval else config.check_interval
    
    monitor = MAMonitor(
        symbols=config.symbols,
        timeframes=config.timeframes,
        ma_periods=config.ma_periods,
        spread_threshold_bull=config.spread_threshold_bull,
        spread_threshold_bear=config.spread_threshold_bear,
        std_threshold_bull=config.std_threshold_bull,
        std_threshold_bear=config.std_threshold_bear,
        consecutive_days=config.consecutive_days,
        check_interval=interval,
        telegram=telegram,
        is_bull_market=is_bull_market,
        alert_reset_hours=config.alert_reset_hours
    )
    
    market_type = "牛市" if is_bull_market else "熊市"
    logger.info(f"Running in {market_type} mode")
    logger.info(f"Threshold - 极差: {config.spread_threshold_bull}%/{config.spread_threshold_bear}%, 标准差: {config.std_threshold_bull}%/{config.std_threshold_bear}%")
    
    monitor.start()


if __name__ == "__main__":
    main()
