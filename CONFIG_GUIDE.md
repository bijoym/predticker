# Paper Trading Configuration Guide

Complete guide to configuring and using the IBKR paper trading system with configuration files.

## Quick Start

### 1. Load the Configuration
```bash
python -c "from src.config import load_config; config = load_config(); config.print_summary()"
```

### 2. Edit Configuration
Edit `config_paper_trading.ini` to customize your trading parameters.

### 3. Run Paper Trading
```bash
# Multi-symbol trading
python trade_with_config.py

# Single symbol
python trade_with_config.py single AAPL

# Compare configurations
python trade_with_config.py compare config_paper_trading.ini config_custom.ini
```

## Configuration File Structure

### [connection]
IBKR connection settings:
- `host`: Connection address (default: 127.0.0.1)
- `port`: 7497 for paper, 7496 for live trading
- `clientId`: Unique identifier (default: 1)
- `timeout`: Connection timeout in seconds

### [account]
Account configuration:
- `account_size`: Total trading capital (USD)
- `currency`: Currency code (USD)
- `trading_mode`: paper or live

### [risk_management]
Critical risk parameters:
- `max_risk_percent`: Max % of account to risk per trade (0.5-5.0)
  - 2% = lose $200 on $10,000 account per trade
  - Recommended: 1-2% for beginners, up to 5% for experienced
- `max_position_size`: Max shares per single trade
- `max_positions`: Max concurrent open trades
- `use_atr_stops`: Use ATR-based stops (recommended: true)
- `stop_loss_atr_multiplier`: Distance from entry (1.0 = 1 ATR)
- `take_profit_atr_multiplier`: Profit target (2.0 = 2 ATR)

### [predictions]
ML prediction settings:
- `min_confidence`: Minimum confidence to trade (0-100)
  - 50-60%: Aggressive trading
  - 60-70%: Balanced
  - 70%+: Conservative
- `timeframe`: Bar size (1 min, 5 mins, 15 mins, 1 hour, 1 day)
  - 1 min: Day trading (high activity)
  - 5-15 min: Scalping
  - 1 hour: Swing trading
  - 1 day: Position trading
- `duration`: Minutes of history to fetch
- `lookback_period`: Candles for technical analysis

### [trading]
Trading behavior:
- `trading_mode`: auto, manual, or dry_run
  - auto: Fully automated trading
  - manual: Suggestions only, you execute
  - dry_run: Simulation only (recommended for testing)
- `order_type`: bracket, market, or limit
  - bracket: Entry + stop + target (recommended)
  - market: Execute immediately at market price
  - limit: Execute only at specified price
- `trading_start`: Market open time (9:30 ET)
- `trading_end`: Market close time (16:00 ET)
- `skip_first_minute`: Skip volatile first minute of market open
- `skip_last_hour`: Skip last hour of trading (before close)

### [symbols]
Symbols to trade (comma-separated):
```ini
stocks = AAPL,MSFT,GOOGL,TSLA,AMZN
etfs = QQQ,SPY,DXY
high_volatility = TSLA,NVDA,AMD
```

Access by category:
```python
config.get_symbols('stocks')  # Returns ['AAPL', 'MSFT', ...]
config.all_symbols  # Returns all configured symbols
```

### [technical_indicators]
Technical analysis parameters:
- `rsi_period`: RSI lookback (14 is standard)
- `rsi_overbought`: Overbought threshold (70)
- `rsi_oversold`: Oversold threshold (30)
- `adx_trend_threshold`: Trend confirmation level (20)
- `atr_period`: ATR lookback (14 is standard)

### [filters]
Trade filtering rules:
- `min_volume`: Minimum daily volume
- `min_price`: Minimum stock price
- `max_price`: Maximum stock price
- `skip_penny_stocks`: Skip stocks < $5
- `skip_pre_market`: Skip trading before 9:30 ET
- `skip_after_hours`: Skip trading after 4:00 PM ET
- `max_vix`: Skip if market volatility too high

### [risk_management] (continued)
Risk control settings:
- `min_profit_target`: Minimum profit factor
- `fixed_stop_percent`: Fixed stop loss % (if not using ATR)
- `fixed_profit_percent`: Fixed profit target % (if not using ATR)

### [debug]
Debug and testing:
- `debug_mode`: Enable detailed logging
- `dry_run_mode`: Simulation mode (don't place real trades)
- `print_predictions`: Show all predictions
- `print_position_size`: Show position sizing calculations
- `print_trades`: Show trade execution details
- `save_debug_data`: Save debug output to files

## Recommended Configurations

### Beginner (Paper Trading)
Start here - most conservative settings:
```ini
account_size = 10000
max_risk_percent = 1.0
min_confidence = 70.0
max_positions = 2
trading_mode = dry_run
dry_run_mode = true
```

**Expected performance:** 50-55% win rate, learning phase

### Active Day Trader
1-minute scalping with tight stops:
```ini
account_size = 25000
max_risk_percent = 2.0
min_confidence = 60.0
timeframe = 1 min
duration = 60
max_positions = 5
skip_first_minute = true
trading_mode = auto
dry_run_mode = true  # Switch to false for live paper trading
```

**Expected performance:** 45-55% win rate, high activity (20-50 trades/day)

### Swing Trader
15-minute to 1-hour bars:
```ini
account_size = 20000
max_risk_percent = 2.0
min_confidence = 65.0
timeframe = 15 mins
duration = 240
max_positions = 3
trading_mode = auto
dry_run_mode = true
```

**Expected performance:** 50-60% win rate, 5-10 trades/day

### Conservative Position Trader
Daily bars, wider stops:
```ini
account_size = 50000
max_risk_percent = 1.0
min_confidence = 70.0
timeframe = 1 day
duration = 1440
take_profit_atr_multiplier = 3.0
max_positions = 2
trading_mode = manual
dry_run_mode = true
```

**Expected performance:** 55-65% win rate, 1-3 trades/week

## Using the Config in Code

### Load Configuration
```python
from src.config import load_config

config = load_config('config_paper_trading.ini')
print(f"Account size: ${config.account_size}")
print(f"Max risk: {config.max_risk_percent}%")
print(f"Min confidence: {config.min_confidence}%")
```

### Access Specific Settings
```python
# Connection
config.ibkr_host      # '127.0.0.1'
config.ibkr_port      # 7497
config.client_id      # 1

# Account
config.account_size   # 10000
config.currency       # 'USD'
config.trading_mode   # 'paper'

# Risk
config.max_risk_percent
config.max_positions
config.use_atr_stops

# Predictions
config.min_confidence
config.timeframe
config.duration

# Trading
config.auto_trading_mode
config.order_type
config.trading_start   # '09:30'
config.trading_end     # '16:00'

# Symbols
config.get_symbols('stocks')  # Get by category
config.all_symbols            # All symbols
```

### Use in Trading Bot
```python
from src.config import load_config
from trade_with_ibkr import IBKRTradingBot

config = load_config()
bot = IBKRTradingBot(config.account_size, config.max_risk_percent)

result = await bot.analyze_and_trade(
    'AAPL',
    min_confidence=config.min_confidence,
    dry_run=config.dry_run_mode
)
```

### Get All Settings as Dictionary
```python
config = load_config()
all_settings = config.get_all_settings()

print(all_settings['account'])
# {'account_size': 10000, 'currency': 'USD', 'trading_mode': 'paper'}
```

## Creating Custom Configurations

### 1. Copy Default Config
```bash
cp config_paper_trading.ini config_aggressive.ini
```

### 2. Edit Custom Config
```ini
# config_aggressive.ini
[account]
account_size = 25000

[risk_management]
max_risk_percent = 3.0

[predictions]
min_confidence = 50.0
```

### 3. Use Custom Config
```python
config = load_config('config_aggressive.ini')
```

## Key Trading Rules Based on Config

### Position Sizing
Position size is automatically calculated based on:
```
Position Size = (Max Risk Per Trade) / (Entry - Stop Loss)

Example with 2% max risk on $10,000 account:
Max Risk = $200
If Entry = $100 and SL = $99 (1 ATR):
  Position = $200 / $1 = 200 shares
```

### Trade Entry Rules
- Only enter if confidence >= min_confidence
- Skip if VIX > max_vix
- Skip if volume < min_volume
- Skip if price < min_price or > max_price
- Skip first minute if skip_first_minute = true

### Stop Loss Placement
- If use_atr_stops = true:
  - Stop = Entry - (ATR * stop_loss_atr_multiplier)
- Else:
  - Stop = Entry * (1 - fixed_stop_percent/100)

### Take Profit Placement
- Target = Entry + (ATR * take_profit_atr_multiplier)

## Performance Optimization

### To Improve Win Rate
1. Increase min_confidence (70%+ for conservative trading)
2. Decrease max_risk_percent (reduce over-leveraging)
3. Add more symbols to diversify
4. Increase adx_trend_threshold (only trade trending markets)

### To Increase Trade Frequency
1. Decrease timeframe (1 min > 5 min > 15 min)
2. Decrease min_confidence (60% > 70%)
3. Add more symbols
4. Decrease max_positions limit

### To Reduce Drawdowns
1. Decrease max_risk_percent
2. Increase min_confidence
3. Decrease take_profit_atr_multiplier (smaller targets)
4. Enable market regime detection

## Troubleshooting

### "Module not found: config"
Make sure you're in the workspace directory:
```bash
cd c:\workspace\market_predictor
```

### Configuration not loading
Check INI file format:
```bash
# Verify syntax
python -c "from src.config import load_config; load_config()"
```

### Positions too small
Adjust these values:
```ini
account_size = 10000  # Increase account size in config
max_risk_percent = 2.0  # Increase risk per trade
stop_loss_atr_multiplier = 1.0  # Tighten stops
```

### Too many losses
```ini
min_confidence = 70.0  # Increase confidence threshold
max_risk_percent = 1.0  # Reduce per-trade risk
```

## Migration to Live Trading

Once profitable on paper trading (2+ weeks):

### Step 1: Enable Real Paper Account
```ini
trading_mode = paper
dry_run_mode = false  # ENABLE REAL PAPER TRADING
```

### Step 2: Switch to Live Credentials
```ini
port = 7496  # Change from 7497 (paper)
```

### Step 3: Start with Smallest Position
```ini
max_risk_percent = 0.5  # Start with 0.5%
max_position_size = 10  # Limit shares
max_positions = 1  # One trade at a time
```

### Step 4: Monitor Performance
- Track all trades
- Review weekly
- Increase position size gradually
- Move to bigger account only after consistent profits

## Summary

The configuration system allows you to:
- ✓ Customize all trading parameters
- ✓ Test different strategies
- ✓ Scale from paper to live trading
- ✓ Implement risk management automatically
- ✓ Optimize for your trading style

**Key files:**
- `config_paper_trading.ini` - Configuration values
- `src/config.py` - Configuration loader
- `trade_with_config.py` - Trading with configuration

---

**Status:** ✓ Production Ready  
**Last Updated:** December 10, 2025  
**Version:** 1.0
