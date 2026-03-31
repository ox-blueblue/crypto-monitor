import requests
import time
from typing import List, Dict
from loguru import logger


class BitgetClient:
    """Bitget API 客户端"""
    
    BASE_URL = "https://api.bitget.com/api/v2/spot/market/candles"
    
    SYMBOL_MAP = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "BNB": "BNBUSDT",
        "SOL": "SOLUSDT",
        "DOGE": "DOGEUSDT",
        "XRP": "XRPUSDT",
        "ADA": "ADAUSDT",
        "AVAX": "AVAXUSDT",
        "DOT": "DOTUSDT",
        "MATIC": "MATICUSDT",
        "LINK": "LINKUSDT",
        "UNI": "UNIUSDT",
        "SAHARA": "SAHARAUSDT",
    }
    
    GRANULARITY_MAP = {
        "1h": "1h",
        "4h": "4h",
        "1d": "1day",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })
    
    def _request(self, params: Dict) -> Dict:
        """发送API请求"""
        for attempt in range(5):
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == "00000":
                    return data.get("data", [])
                else:
                    logger.warning(f"Bitget API 返回错误: {data.get('code')} - {data.get('msg')}")
                    time.sleep(1)
                    continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Bitget API 请求失败 (尝试 {attempt + 1}/5): {e}")
                time.sleep(1)
        logger.error(f"Bitget API 请求失败，已重试5次")
        raise Exception(f"Bitget API request failed after 5 retries")
    
    def _get_symbol(self, symbol: str) -> str:
        """获取Bitget格式的symbol"""
        return self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}USDT")
    
    def get_candles(self, symbol: str, granularity: str, limit: int = 200) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 代币符号，如 BTC
            granularity: 时间周期，如 1h, 4h, 1d
            limit: 获取数量
        
        Returns:
            K线数据列表: [[timestamp, open, high, low, close, volume, ...], ...]
        """
        gran = self.GRANULARITY_MAP.get(granularity, granularity)
        params = {
            "symbol": self._get_symbol(symbol),
            "granularity": gran,
            "limit": limit
        }
        return self._request(params)
    
    def get_closes(self, symbol: str, granularity: str, limit: int = 200) -> List[float]:
        """获取收盘价列表"""
        candles = self.get_candles(symbol, granularity, limit)
        return [float(c[4]) for c in candles]
    
    def get_closes_with_time(self, symbol: str, granularity: str, limit: int = 200) -> List[tuple]:
        """获取收盘价列表（带时间戳）"""
        candles = self.get_candles(symbol, granularity, limit)
        return [(int(c[0]), float(c[4])) for c in candles]
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        candles = self.get_candles(symbol, "1h", 1)
        if candles:
            return float(candles[0][4])
        return 0
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """批量获取价格"""
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_current_price(symbol)
        return prices
