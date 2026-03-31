import statistics
import talib
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class MADensityResult:
    """均线密集度计算结果"""
    ma_spread_rate: float      # 均线极差率 (SMA+EMA取大)
    ma_std_rate: float         # 均线标准差率 (SMA+EMA取大)
    ma_max: float              # 最大均线
    ma_min: float              # 最小均线
    ma_mean: float             # 均线均值
    consecutive_days: int      # 连续密集次数
    is_dense: bool             # 是否密集


class MADensityCalculator:
    """均线密集度计算器"""
    
    def __init__(
        self,
        ma_periods: List[int] = None,
        spread_threshold_bull: float = 3.0,
        spread_threshold_bear: float = 1.5,
        std_threshold_bull: float = 2.0,
        std_threshold_bear: float = 1.0,
        consecutive_days: int = 3,
        is_bull_market: bool = True
    ):
        self.ma_periods = ma_periods or [5, 10, 20, 30, 60, 120]
        self.spread_threshold_bull = spread_threshold_bull
        self.spread_threshold_bear = spread_threshold_bear
        self.std_threshold_bull = std_threshold_bull
        self.std_threshold_bear = std_threshold_bear
        self.consecutive_days = consecutive_days
        self.is_bull_market = is_bull_market
        
        self.spread_threshold = spread_threshold_bull if is_bull_market else spread_threshold_bear
        self.std_threshold = std_threshold_bull if is_bull_market else std_threshold_bear
    
    def calculate_ma_spread_rate(self, ma_values: Dict[int, float], reference_price: float) -> float:
        """
        计算均线极差率
        
        公式: (MA_max - MA_min) / 参考价 × 100%
        """
        ma_list = list(ma_values.values())
        if not ma_list:
            return 100.0
        
        ma_max = max(ma_list)
        ma_min = min(ma_list)
        
        if reference_price == 0:
            return 100.0
        
        return ((ma_max - ma_min) / reference_price) * 100
    
    def calculate_ma_std_rate(self, ma_values: Dict[int, float]) -> float:
        """
        计算均线标准差率
        
        公式: MA_std / MA_mean × 100%
        """
        ma_list = list(ma_values.values())
        if len(ma_list) < 2:
            return 100.0
        
        ma_mean = statistics.mean(ma_list)
        if ma_mean == 0:
            return 100.0
        
        ma_std = statistics.stdev(ma_list)
        return (ma_std / ma_mean) * 100
    
    def _calc_ma_values(self, prices: List[float]) -> Tuple[Dict[int, float], Dict[int, float]]:
        """使用 TA-Lib 计算 SMA 和 EMA，返回 (sma_values, ema_values)"""
        prices_arr = np.array(prices, dtype=np.float64)
        sma_values = {}
        ema_values = {}
        for period in self.ma_periods:
            if len(prices_arr) >= period:
                sma = talib.SMA(prices_arr, timeperiod=period)
                ema = talib.EMA(prices_arr, timeperiod=period)
                sma_values[period] = float(sma[-1])
                ema_values[period] = float(ema[-1])
        return sma_values, ema_values
    
    def _count_consecutive(self, group_results: List[dict]) -> int:
        """根据预计算的3组结果统计连续密集次数"""
        count = 0
        for group in group_results:
            is_dense = (group["spread"] <= self.spread_threshold and 
                        group["std"] <= self.std_threshold)
            if is_dense:
                count += 1
            else:
                break
        return count
    
    def calculate(
        self,
        current_price: float,
        symbol: str = "",
        timeframe: str = "",
        kline_closes: List[tuple] = None
    ) -> MADensityResult:
        """
        计算均线密集度 (SMA和EMA取较大值)
        
        Args:
            current_price: 当前价格
            symbol: 代币符号
            timeframe: 时间周期
            kline_closes: K线数据 [(timestamp, close), ...]
        
        Returns:
            MADensityResult
        """
        if not kline_closes:
            logger.warning(f"{symbol}/{timeframe} 无K线数据")
            return MADensityResult(100, 100, 0, 0, 0, 0, False)
        
        prices = [c[1] for c in kline_closes]
        
        group_results = []
        for end_idx in [len(prices) - 2, len(prices) - 1, len(prices)]:
            group_prices = prices[:end_idx]
            if len(group_prices) < max(self.ma_periods):
                continue
            
            sma_values, ema_values = self._calc_ma_values(group_prices)
            
            if not sma_values or not ema_values:
                continue
            
            all_values = {}
            for k, v in sma_values.items():
                all_values[f"sma_{k}"] = v
            for k, v in ema_values.items():
                all_values[f"ema_{k}"] = v
            
            ma_mean = statistics.mean(all_values.values())
            reference_price = ma_mean if ma_mean > 0 else group_prices[-1]
            
            spread_rate = max(
                self.calculate_ma_spread_rate(sma_values, reference_price),
                self.calculate_ma_spread_rate(ema_values, reference_price)
            )
            std_rate = max(
                self.calculate_ma_std_rate(sma_values),
                self.calculate_ma_std_rate(ema_values)
            )
            
            group_results.append({
                "spread": spread_rate,
                "std": std_rate,
                "all_values": all_values,
                "reference_price": reference_price
            })
        
        if not group_results:
            return MADensityResult(100, 100, 0, 0, 0, 0, False)
        
        latest = group_results[-1]
        ma_spread_rate = latest["spread"]
        ma_std_rate = latest["std"]
        all_values = latest["all_values"]
        
        ma_max = max(all_values.values())
        ma_min = min(all_values.values())
        ma_mean = statistics.mean(all_values.values())
        
        consecutive_days = self._count_consecutive(group_results)
        is_dense = consecutive_days >= self.consecutive_days
        
        return MADensityResult(
            ma_spread_rate=round(ma_spread_rate, 4),
            ma_std_rate=round(ma_std_rate, 4),
            ma_max=round(ma_max, 2),
            ma_min=round(ma_min, 2),
            ma_mean=round(ma_mean, 2),
            consecutive_days=consecutive_days,
            is_dense=is_dense
        )
