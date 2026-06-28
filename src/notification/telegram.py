import requests
from loguru import logger
from ..indicator.ma_density import MADensityResult


class TelegramNotifier:
    """Telegram 通知器"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """发送消息"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram 未配置，跳过通知")
            return False
        
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Telegram 发送失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Telegram 发送异常: {e}")
            return False
    
    def format_alert(
        self,
        symbol: str,
        timeframe: str,
        current_price: float,
        result: MADensityResult
    ) -> str:
        """格式化告警消息"""
        emoji = "🚀" if result.ma_spread_rate < 1.5 else "⚠️"
        
        return f"""{emoji} *均线密集告警*

📌 *{symbol}* ({timeframe})

💰 现价: `${current_price:,.2f}`

📊 均线密集度:
• 极差率: `{result.ma_spread_rate:.2f}%`
• 标准差率: `{result.ma_std_rate:.2f}%`

📐 均线值:
• 最大: `${result.ma_max:,.2f}`
• 最小: `${result.ma_min:,.2f}`
• 均值: `${result.ma_mean:,.2f}`

⏰ 连续密集: `{result.consecutive_days}根`

🔥 状态: *密集!*"""
    
    def send_alert(
        self,
        symbol: str,
        timeframe: str,
        current_price: float,
        result: MADensityResult
    ) -> bool:
        """发送告警"""
        message = self.format_alert(symbol, timeframe, current_price, result)
        return self.send_message(message)
    
    def send_startup_message(self, symbols: list, timeframes: list, intervals: int) -> bool:
        """发送启动消息"""
        message = f"""✅ *监控已启动*

📊 监控代币: {', '.join(symbols)}
⏱️ 时间周期: {', '.join(timeframes)}
🔄 检查间隔: {intervals}秒

等待告警..."""
        return self.send_message(message)
