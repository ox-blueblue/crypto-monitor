import time
from typing import Dict, List
from loguru import logger
from ..data.bitget_client import BitgetClient
from ..indicator.ma_density import MADensityCalculator, MADensityResult
from ..notification.telegram import TelegramNotifier


class MAMonitor:
    """均线密集度监控器"""
    
    def __init__(
        self,
        symbols: List[str],
        timeframes: List[str],
        ma_periods: List[int],
        spread_threshold_bull: float,
        spread_threshold_bear: float,
        std_threshold_bull: float,
        std_threshold_bear: float,
        consecutive_days: int,
        check_interval: int,
        telegram: TelegramNotifier,
        is_bull_market: bool = True,
        alert_reset_hours: int = 6
    ):
        self.symbols = symbols
        self.timeframes = timeframes
        self.ma_periods = ma_periods
        self.spread_threshold_bull = spread_threshold_bull
        self.spread_threshold_bear = spread_threshold_bear
        self.std_threshold_bull = std_threshold_bull
        self.std_threshold_bear = std_threshold_bear
        self.consecutive_days = consecutive_days
        self.check_interval = check_interval
        self.telegram = telegram
        self.is_bull_market = is_bull_market
        self.alert_reset_hours = alert_reset_hours
        
        self.client = BitgetClient()
        self.calculator = MADensityCalculator(
            ma_periods=self.ma_periods,
            spread_threshold_bull=self.spread_threshold_bull,
            spread_threshold_bear=self.spread_threshold_bear,
            std_threshold_bull=self.std_threshold_bull,
            std_threshold_bear=self.std_threshold_bear,
            consecutive_days=self.consecutive_days,
            is_bull_market=self.is_bull_market
        )
        self.alerted: Dict[str, bool] = {}
        self.last_alert_reset_time = time.time()
    
    def _make_key(self, symbol: str, timeframe: str) -> str:
        """生成唯一键"""
        return f"{symbol}_{timeframe}"
    
    def check_symbol_timeframe(
        self,
        symbol: str,
        timeframe: str
    ) -> Dict:
        """检查单个代币-时间周期"""
        try:
            kline_data = self.client.get_closes_with_time(symbol, timeframe)
            
            if len(kline_data) < max(self.ma_periods) + self.consecutive_days:
                logger.warning(f"{symbol}/{timeframe} 数据不足")
                return {"success": False, "error": "Insufficient data"}
            
            closes = [c[1] for c in kline_data]
            current_price = closes[-1]
            
            result = self.calculator.calculate(current_price, symbol, timeframe, kline_data)
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "price": current_price,
                "result": result
            }
        except Exception as e:
            logger.error(f"检查 {symbol}/{timeframe} 失败: {e}")
            return {"success": False, "error": str(e)}
    
    def run_single_check(self) -> List[Dict]:
        """执行一次检查"""
        results = []
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                time.sleep(1)
                key = self._make_key(symbol, timeframe)
                check_result = self.check_symbol_timeframe(symbol, timeframe)
                
                if check_result["success"]:
                    result = check_result["result"]
                    
                    if result.is_dense and not self.alerted.get(key, False):
                        sent = self.telegram.send_alert(
                            symbol,
                            timeframe,
                            check_result["price"],
                            result
                        )
                        if sent:
                            self.alerted[key] = True
                            logger.success(f"发送告警: {symbol} {timeframe}")
                    
                    results.append({
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "spread_rate": result.ma_spread_rate,
                        "std_rate": result.ma_std_rate,
                        "consecutive": result.consecutive_days,
                        "is_dense": result.is_dense
                    })
                else:
                    logger.warning(f"{symbol}/{timeframe} 检查失败: {check_result['error']}")
        
        return results
    
    def start(self):
        """启动监控循环"""
        logger.info("Starting MA Density Monitor...")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Timeframes: {self.timeframes}")
        logger.info(f"Interval: {self.check_interval}s")
        logger.info(f"Alert reset: {self.alert_reset_hours}h")
        
        self.telegram.send_startup_message(
            self.symbols,
            self.timeframes,
            self.check_interval
        )
        
        while True:
            try:
                elapsed = time.time() - self.last_alert_reset_time
                reset_hours_seconds = self.alert_reset_hours * 3600
                
                if self.alert_reset_hours > 0 and elapsed >= reset_hours_seconds:
                    alerted_count = sum(1 for v in self.alerted.values() if v)
                    self.alerted = {}
                    self.last_alert_reset_time = time.time()
                    logger.info(f"告警已重置 (已发送 {alerted_count} 个告警)")
                
                results = self.run_single_check()
                
                logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 均线密集度检查 - {len(results)} 个交易对")
                for r in results:
                    status = "🔥密集" if r["is_dense"] else ""
                    alerted = "📢已告警" if self.alerted.get(self._make_key(r["symbol"], r["timeframe"]), False) else ""
                    logger.info(f"  {r['symbol']:6} {r['timeframe']:3} | 极差: {r['spread_rate']:6.2f}% | 标准差: {r['std_rate']:6.2f}% | 连续: {r['consecutive']}根 {status} {alerted}")
                
                dense_count = sum(1 for r in results if r["is_dense"])
                logger.info(f"总计: {len(results)} 个交易对, {dense_count} 个密集")
                
                if self.alert_reset_hours > 0:
                    remaining = reset_hours_seconds - elapsed
                    logger.debug(f"下次告警重置: {int(remaining/3600)}h {int((remaining%3600)/60)}m 后")
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
            
            time.sleep(self.check_interval)
