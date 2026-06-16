#!/usr/bin/env python3
"""
动量监控程序

功能:
- 单次计算各交易对过去5天、10天、20天的动量
- 按周期排序后通过Telegram发送

定时执行由系统 cron 负责。
"""

import os
import sys
import yaml
from datetime import datetime
from typing import List, Dict, Tuple


def sort_periods_for_notification(periods: List[int]) -> List[int]:
    """通知展示周期排序：长周期优先，确保20天排在5天/10天前面。"""
    return sorted(periods, reverse=True)
from loguru import logger

sys.path.insert(0, os.path.dirname(__file__))

from src.data.bitget_client import BitgetClient
from src.notification.telegram import TelegramNotifier


class MoveConfig:
    """动量监控配置"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config",
                "config_move.yaml"
            )
        
        self.config_path = config_path
        self._config = self._load()
    
    def _load(self) -> Dict:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @property
    def symbols(self) -> List[str]:
        return self._config.get("symbols", ["BTC", "BNB", "SOL", "ETH"])
    
    @property
    def periods(self) -> List[int]:
        """从 '5d', '10d', '20d' 解析为 [5, 10, 20]"""
        tfs = self._config.get("timeframes", ["5d", "10d", "20d"])
        return [int(tf.replace("d", "")) for tf in tfs]
    
    @property
    def telegram_bot_token(self) -> str:
        return self._config.get("telegram", {}).get("bot_token", "")
    
    @property
    def telegram_chat_id(self) -> str:
        return self._config.get("telegram", {}).get("chat_id", "")


class MomentumCalculator:
    """动量计算器"""
    
    def __init__(self):
        self.client = BitgetClient()
    
    def calculate(self, symbol: str, period: int) -> Tuple[str, float, float, float]:
        """
        计算单个币种的动量
        
        Args:
            symbol: 代币符号，如 BTC
            period: 周期天数，如 5, 10, 20
        
        Returns:
            (symbol, current_price, past_price, momentum): 币种、当前价格、N天前价格、动量百分比
        """
        try:
            limit = period + 1
            candles = self.client.get_candles(symbol, "1d", limit)
            
            if not candles or len(candles) < limit:
                logger.warning(f"{symbol} 数据不足，period={period}")
                return (symbol, 0.0, 0.0, 0.0)
            
            timestamps = [int(c[0]) for c in candles]
            if timestamps != sorted(timestamps):
                logger.warning(f"{symbol} K线时间未按升序排列，跳过计算")
                return (symbol, 0.0, 0.0, 0.0)
            
            current_price = float(candles[-1][4])
            past_price = float(candles[-1 - period][4])
            
            if past_price == 0:
                return (symbol, current_price, past_price, 0.0)
            
            momentum = (current_price - past_price) / past_price * 100
            return (symbol, current_price, past_price, momentum)
        
        except Exception as e:
            logger.error(f"计算 {symbol} {period}天动量失败: {e}")
            return (symbol, 0.0, 0.0, 0.0)
    
    def calculate_all(self, symbols: List[str], periods: List[int]) -> Dict[int, List[Tuple[str, float, float, float]]]:
        """
        批量计算所有币种所有周期的动量
        
        Returns:
            {period: [(symbol, current_price, past_price, momentum), ...], ...}
        """
        results = {}
        
        for period in periods:
            period_results = []
            for symbol in symbols:
                result = self.calculate(symbol, period)
                period_results.append(result)
            
            period_results.sort(key=lambda x: x[3], reverse=True)
            results[period] = period_results
        
        return results


def format_message(results: Dict[int, List[Tuple[str, float, float, float]]]) -> str:
    """格式化推送消息"""
    lines = []
    lines.append(f"📈 动量监控报告 ({datetime.now().strftime('%Y-%m-%d')})")
    lines.append("")
    
    for period in sort_periods_for_notification(list(results.keys())):
        data = results[period]
        lines.append(f"⏱️ {period}天动量排行")
        lines.append(f"{'币种':<6} {'涨跌幅':>10} {'当前价格':>14} {'前' + str(period) + '天':>14}")
        
        for i, (symbol, current_price, past_price, momentum) in enumerate(data):    
            lines.append(f" {symbol:<5} {momentum:>10.2f}% {current_price:>14,.2f} {past_price:>14,.2f}")
        
        lines.append("")
    
    return "\n".join(lines)


def run_momentum_task():
    """执行动量计算任务"""
    logger.info("开始计算动量...")
    
    config = MoveConfig()
    calculator = MomentumCalculator()
    notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    
    results = calculator.calculate_all(config.symbols, config.periods)
    
    message = format_message(results)
    logger.info(f"\n{message}")
    
    if config.telegram_bot_token and config.telegram_chat_id:
        notifier.send_message(message)
        logger.info("Telegram 消息已发送")
    else:
        logger.warning("Telegram 未配置，跳过发送")


def main():
    """主函数：执行一次动量计算任务。"""
    logger.info("动量监控程序启动")
    run_momentum_task()


if __name__ == "__main__":
    main()