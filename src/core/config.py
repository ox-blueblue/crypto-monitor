import yaml
import os
from typing import List, Dict, Any


class Config:
    """配置加载器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "config.yaml"
            )
        
        self.config_path = config_path
        self._config = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @property
    def symbols(self) -> List[str]:
        return self._config.get("symbols", ["BTC", "BNB", "SOL", "ETH"])
    
    @property
    def timeframes(self) -> List[str]:
        return self._config.get("timeframes", ["1h", "4h", "1d", "1w"])
    
    @property
    def ma_periods(self) -> List[int]:
        return self._config.get("ma_periods", [5, 10, 20, 30, 60, 120])
    
    @property
    def spread_threshold_bull(self) -> float:
        return self._config.get("ma_density_threshold", {}).get("spread_bull", 3.0)
    
    @property
    def spread_threshold_bear(self) -> float:
        return self._config.get("ma_density_threshold", {}).get("spread_bear", 1.5)
    
    @property
    def std_threshold_bull(self) -> float:
        return self._config.get("ma_density_threshold", {}).get("std_bull", 2.0)
    
    @property
    def std_threshold_bear(self) -> float:
        return self._config.get("ma_density_threshold", {}).get("std_bear", 1.0)
    
    @property
    def consecutive_days(self) -> int:
        return self._config.get("consecutive_days", 3)
    
    @property
    def check_interval(self) -> int:
        return self._config.get("check_interval", 300)
    
    @property
    def alert_reset_hours(self) -> int:
        return self._config.get("alert_reset_hours", 6)
    
    @property
    def telegram_token(self) -> str:
        return self._config.get("telegram", {}).get("bot_token", "")
    
    @property
    def telegram_chat_id(self) -> str:
        return self._config.get("telegram", {}).get("chat_id", "")
    
    def reload(self):
        """重新加载配置"""
        self._config = self._load()
