import requests
import time
from typing import List, Dict, Optional


class CryptoCompareClient:
    """CryptoCompare API 客户端 (免费公开API)"""
    
    BASE_URL = "https://min-api.cryptocompare.com/data"
    
    SYMBOL_TO_ID = {
        "BTC": "BTC",
        "ETH": "ETH",
        "BNB": "BNB",
        "SOL": "SOL",
        "DOGE": "DOGE",
        "XRP": "XRP",
        "ADA": "ADA",
        "AVAX": "AVAX",
        "DOT": "DOT",
        "MATIC": "MATIC",
        "LINK": "LINK",
        "UNI": "UNI",
    }
    
    INTERVAL_MAP = {
        "1h": "hour",
        "4h": "hour",   # 需要特殊处理
        "1d": "day",
        "1w": "week",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })
    
    def _request(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 5) -> Dict:
        """发送API请求"""
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data.get("Response") == "Success":
                    return data
                elif "Not available" in str(data):
                    time.sleep(1)
                    continue
                else:
                    return data
                    
            except requests.exceptions.RequestException:
                time.sleep(1)
        raise Exception(f"CryptoCompare API request failed after {max_retries} retries")
    
    def get_historical(
        self,
        symbol: str,
        vs_currency: str = "USD",
        interval: str = "day",
        limit: int = 200
    ) -> List[Dict]:
        """
        获取历史K线数据
        
        Args:
            symbol: 代币符号
            vs_currency: 计价货币
            interval: hour, day, week
            limit: 数量
        """
        endpoint_map = {
            "hour": "histohour",
            "day": "histoday",
            "week": "histoweek"
        }
        
        endpoint = endpoint_map.get(interval, "histoday")
        
        params = {
            "fsym": symbol.upper(),
            "tsym": vs_currency,
            "limit": limit
        }
        
        if interval == "hour":
            params["allData"] = "true"
        
        data = self._request(endpoint, params)
        
        if isinstance(data, dict):
            return data.get("Data", []) or []
        elif isinstance(data, list):
            return data
        return []
    
    def _get_interval_param(self, interval: str) -> Dict:
        """获取interval参数"""
        if interval == "1h":
            return {"interval": "hour", "limit": 200}
        elif interval == "4h":
            return {"interval": "hour", "limit": 800}  # 需要更多数据点
        elif interval == "1d":
            return {"interval": "day", "limit": 200}
        elif interval == "1w":
            return {"interval": "week", "limit": 200}
        return {"interval": "day", "limit": 200}
    
    def get_closes(self, symbol: str, interval: str, limit: int = 200) -> List[float]:
        """获取收盘价列表"""
        interval_params = self._get_interval_param(interval)
        interval_type = interval_params["interval"]
        req_limit = max(limit, interval_params["limit"])
        
        candles = self.get_historical(symbol, "USD", interval_type, req_limit)
        
        closes = [float(c["close"]) for c in candles]
        return closes[-limit:]
    
    def get_closes_with_time(self, symbol: str, interval: str, limit: int = 200) -> List[tuple]:
        """获取收盘价列表（带时间戳）"""
        interval_params = self._get_interval_param(interval)
        interval_type = interval_params["interval"]
        req_limit = max(limit, interval_params["limit"])
        
        candles = self.get_historical(symbol, "USD", interval_type, req_limit)
        
        result = [(c["time"], float(c["close"])) for c in candles]
        return result[-limit:]
    
    def get_ohlc(self, symbol: str, interval: str, limit: int = 200) -> List[List[float]]:
        """获取OHLC数据"""
        interval_params = self._get_interval_param(interval)
        interval_type = interval_params["interval"]
        req_limit = max(limit, interval_params["limit"])
        
        candles = self.get_historical(symbol, "USD", interval_type, req_limit)
        
        ohlc = [
            [c["time"], c["open"], c["high"], c["low"], c["close"]]
            for c in candles
        ]
        return ohlc[-limit:]
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        data = self._request("price", {
            "fsym": symbol.upper(),
            "tsyms": "USD"
        })
        return data.get("USD", 0)
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """批量获取价格"""
        data = self._request("pricemulti", {
            "fsyms": ",".join([s.upper() for s in symbols]),
            "tsyms": "USD"
        })
        return {s: data.get(s.upper(), {}).get("USD", 0) for s in symbols}
    
    def calculate_ma(self, prices: List[float], period: int) -> float:
        """计算简单移动平均线 SMA"""
        if len(prices) < period:
            return 0
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """
        计算指数移动平均线 EMA
        
        使用前period个价格的SMA作为初始EMA，
        然后用后续价格迭代计算
        """
        if len(prices) < period:
            return 0
        
        multiplier = 2 / (period + 1)
        
        # 1. 先计算前period个价格的SMA作为初始EMA
        ema = sum(prices[:period]) / period
        
        # 2. 用后续价格迭代
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def get_ma_values(self, symbol: str, interval: str, periods: List[int]) -> Dict[int, float]:
        """获取多条SMA均线值"""
        closes = self.get_closes(symbol, interval, max(periods) + 10)
        ma_values = {}
        for period in periods:
            ma_values[period] = self.calculate_ma(closes, period)
        return ma_values
    
    def get_ema_values(self, symbol: str, interval: str, periods: List[int]) -> Dict[int, float]:
        """获取多条EMA均线值"""
        closes = self.get_closes(symbol, interval, max(periods) + 10)
        ema_values = {}
        for period in periods:
            ema_values[period] = self.calculate_ema(closes, period)
        return ema_values
