"""
Configuration manager for IBKR paper trading
Loads and manages all trading parameters
"""

import configparser
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingConfig:
    """Manages trading configuration from INI file"""
    
    def __init__(self, config_file: str = 'config_paper_trading.ini'):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            logger.info("Creating default config...")
            self._create_default_config()
        else:
            self.config.read(self.config_file)
            logger.info(f"✓ Loaded config from {config_file}")
    
    def _create_default_config(self):
        """Create default configuration if missing"""
        # This would create default values
        pass
    
    # Connection Settings
    @property
    def ibkr_host(self) -> str:
        return self.config.get('connection', 'host', fallback='127.0.0.1')
    
    @property
    def ibkr_port(self) -> int:
        return self.config.getint('connection', 'port', fallback=7497)
    
    @property
    def client_id(self) -> int:
        return self.config.getint('connection', 'clientId', fallback=1)
    
    # Account Settings
    @property
    def account_size(self) -> float:
        return self.config.getfloat('account', 'account_size', fallback=10000)
    
    @property
    def currency(self) -> str:
        return self.config.get('account', 'currency', fallback='USD')
    
    @property
    def trading_mode(self) -> str:
        """paper or live"""
        return self.config.get('account', 'trading_mode', fallback='paper')
    
    # Risk Management
    @property
    def max_risk_percent(self) -> float:
        return self.config.getfloat('risk_management', 'max_risk_percent', fallback=2.0)
    
    @property
    def max_position_size(self) -> int:
        return self.config.getint('risk_management', 'max_position_size', fallback=100)
    
    @property
    def min_profit_target(self) -> float:
        return self.config.getfloat('risk_management', 'min_profit_target', fallback=1.5)
    
    @property
    def max_positions(self) -> int:
        return self.config.getint('risk_management', 'max_positions', fallback=5)
    
    @property
    def use_atr_stops(self) -> bool:
        return self.config.getboolean('risk_management', 'use_atr_stops', fallback=True)
    
    @property
    def stop_loss_atr_multiplier(self) -> float:
        return self.config.getfloat('risk_management', 'stop_loss_atr_multiplier', fallback=1.0)
    
    @property
    def take_profit_atr_multiplier(self) -> float:
        return self.config.getfloat('risk_management', 'take_profit_atr_multiplier', fallback=2.0)
    
    # Predictions
    @property
    def min_confidence(self) -> float:
        return self.config.getfloat('predictions', 'min_confidence', fallback=60.0)
    
    @property
    def timeframe(self) -> str:
        return self.config.get('predictions', 'timeframe', fallback='1 min')
    
    @property
    def duration(self) -> int:
        return self.config.getint('predictions', 'duration', fallback=60)
    
    @property
    def lookback_period(self) -> int:
        return self.config.getint('predictions', 'lookback_period', fallback=20)
    
    # Trading
    @property
    def auto_trading_mode(self) -> str:
        """auto, manual, or dry_run"""
        return self.config.get('trading', 'trading_mode', fallback='dry_run')
    
    @property
    def order_type(self) -> str:
        """bracket, market, or limit"""
        return self.config.get('trading', 'order_type', fallback='bracket')
    
    @property
    def trading_start(self) -> str:
        return self.config.get('trading', 'trading_start', fallback='09:30')
    
    @property
    def trading_end(self) -> str:
        return self.config.get('trading', 'trading_end', fallback='16:00')
    
    @property
    def skip_first_minute(self) -> bool:
        return self.config.getboolean('trading', 'skip_first_minute', fallback=True)
    
    # Symbols
    def get_symbols(self, category: str = 'stocks') -> list:
        """Get symbols by category"""
        try:
            symbols_str = self.config.get('symbols', category, fallback='')
            symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
            return symbols
        except:
            return []
    
    @property
    def all_symbols(self) -> list:
        """Get all configured symbols"""
        all_symbols = []
        try:
            for option in self.config.options('symbols'):
                symbols = self.get_symbols(option)
                all_symbols.extend(symbols)
        except:
            pass
        return list(set(all_symbols))  # Remove duplicates
    
    # Technical Indicators
    @property
    def rsi_period(self) -> int:
        return self.config.getint('technical_indicators', 'rsi_period', fallback=14)
    
    @property
    def rsi_overbought(self) -> float:
        return self.config.getfloat('technical_indicators', 'rsi_overbought', fallback=70)
    
    @property
    def rsi_oversold(self) -> float:
        return self.config.getfloat('technical_indicators', 'rsi_oversold', fallback=30)
    
    @property
    def adx_trend_threshold(self) -> float:
        return self.config.getfloat('technical_indicators', 'adx_trend_threshold', fallback=20)
    
    # Filters
    @property
    def min_volume(self) -> int:
        return self.config.getint('filters', 'min_volume', fallback=1000000)
    
    @property
    def min_price(self) -> float:
        return self.config.getfloat('filters', 'min_price', fallback=5.0)
    
    @property
    def max_price(self) -> float:
        return self.config.getfloat('filters', 'max_price', fallback=500.0)
    
    @property
    def skip_penny_stocks(self) -> bool:
        return self.config.getboolean('filters', 'skip_penny_stocks', fallback=True)
    
    # Adaptive Weights
    @property
    def weights_file(self) -> str:
        return self.config.get('adaptive_weights', 'weights_file', 
                             fallback='models/regime_weights_20251210_135927.pkl')
    
    @property
    def use_adaptive_weights(self) -> bool:
        return self.config.getboolean('adaptive_weights', 'use_adaptive_weights', fallback=True)
    
    # Debug
    @property
    def debug_mode(self) -> bool:
        return self.config.getboolean('debug', 'debug_mode', fallback=False)
    
    @property
    def dry_run_mode(self) -> bool:
        return self.config.getboolean('debug', 'dry_run_mode', fallback=True)
    
    @property
    def print_predictions(self) -> bool:
        return self.config.getboolean('debug', 'print_predictions', fallback=True)
    
    # Logging
    @property
    def log_level(self) -> str:
        return self.config.get('notifications', 'log_level', fallback='INFO')
    
    @property
    def log_file(self) -> str:
        return self.config.get('notifications', 'log_file', fallback='logs/trading.log')
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as dictionary"""
        return {
            'connection': {
                'host': self.ibkr_host,
                'port': self.ibkr_port,
                'clientId': self.client_id,
            },
            'account': {
                'account_size': self.account_size,
                'currency': self.currency,
                'trading_mode': self.trading_mode,
            },
            'risk_management': {
                'max_risk_percent': self.max_risk_percent,
                'max_position_size': self.max_position_size,
                'max_positions': self.max_positions,
                'use_atr_stops': self.use_atr_stops,
            },
            'predictions': {
                'min_confidence': self.min_confidence,
                'timeframe': self.timeframe,
                'duration': self.duration,
            },
            'trading': {
                'mode': self.auto_trading_mode,
                'order_type': self.order_type,
                'trading_start': self.trading_start,
                'trading_end': self.trading_end,
            },
            'symbols': self.all_symbols,
            'debug': {
                'debug_mode': self.debug_mode,
                'dry_run_mode': self.dry_run_mode,
            }
        }
    
    def print_summary(self):
        """Print configuration summary"""
        print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    TRADING CONFIGURATION SUMMARY                           ║
╚════════════════════════════════════════════════════════════════════════════╝

🔌 CONNECTION
────────────────────────────────────────────────────────────────────────────
Host:                  {self.ibkr_host}
Port:                  {self.ibkr_port} ({'Paper Trading' if self.ibkr_port == 7497 else 'Live Trading'})
Client ID:             {self.client_id}

💰 ACCOUNT
────────────────────────────────────────────────────────────────────────────
Account Size:          ${self.account_size:,.2f}
Currency:              {self.currency}
Trading Mode:          {self.trading_mode}

⚠️  RISK MANAGEMENT
────────────────────────────────────────────────────────────────────────────
Max Risk Per Trade:    {self.max_risk_percent}% (${self.account_size * self.max_risk_percent / 100:,.2f})
Max Positions:         {self.max_positions}
Use ATR Stops:         {self.use_atr_stops}
Stop Loss Multiple:    {self.stop_loss_atr_multiplier}x ATR
Take Profit Multiple:  {self.take_profit_atr_multiplier}x ATR

🤖 PREDICTIONS
────────────────────────────────────────────────────────────────────────────
Min Confidence:        {self.min_confidence}%
Timeframe:             {self.timeframe}
Data Duration:         {self.duration} minutes
Lookback Period:       {self.lookback_period} candles

📊 TRADING
────────────────────────────────────────────────────────────────────────────
Trading Mode:          {self.auto_trading_mode}
Order Type:            {self.order_type}
Trading Start:         {self.trading_start} ET
Trading End:           {self.trading_end} ET
Skip First Minute:     {self.skip_first_minute}

📈 SYMBOLS ({len(self.all_symbols)})
────────────────────────────────────────────────────────────────────────────
{', '.join(self.all_symbols[:10]) if self.all_symbols else 'None configured'}
{f'... and {len(self.all_symbols) - 10} more' if len(self.all_symbols) > 10 else ''}

🔧 DEBUG
────────────────────────────────────────────────────────────────────────────
Debug Mode:            {self.debug_mode}
Dry Run Mode:          {self.dry_run_mode}
Print Predictions:     {self.print_predictions}

════════════════════════════════════════════════════════════════════════════
""")


def load_config(config_file: str = 'config_paper_trading.ini') -> TradingConfig:
    """Load trading configuration"""
    return TradingConfig(config_file)


if __name__ == '__main__':
    # Demo
    config = load_config()
    config.print_summary()
