# IBKR Live Trading Integration Guide

Complete integration with Interactive Brokers (IBKR) for live market data, predictions, and trade execution.

## Overview

The IBKR integration allows you to:
- **Fetch live market data** directly from Interactive Brokers
- **Generate real-time predictions** using adaptive ML weights
- **Execute trades** with automated risk management
- **Monitor positions** and manage your portfolio

## Prerequisites

### 1. Interactive Brokers Account
- Create account at https://www.interactivebrokers.com
- Can use either:
  - **Paper trading** (simulated, no real money)
  - **Live trading** (real money)

### 2. Download TWS or IBGateway
- **TWS (Trader Workstation)**: Full-featured desktop application
  - Download: https://www.interactivebrokers.com/en/trading/tws.php
  - More resource-heavy
  - Better for active traders

- **IBGateway**: Lightweight API gateway
  - Download: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
  - Minimal interface, API-focused
  - Recommended for automated trading

### 3. Enable API Connections
1. Start TWS/IBGateway
2. Go to: **File > Global Configuration**
3. Navigate to: **API > Settings**
4. Check: **"Enable ActiveX and Socket Clients"**
5. Note the port number (typically 7497 for paper, 7496 for live)

## Installation

### Install ib-insync package
```bash
python -m pip install ib-insync
```

The system automatically installs:
- `ib-insync`: IB API wrapper
- `eventkit`: Event handling
- `nest-asyncio`: Async event loop support

## Modules Overview

### 1. `src/ibkr_connector.py` - Data Fetching
Connects to IBKR and retrieves market data.

**Key Classes:**
- `IBKRConnector`: Low-level IBKR connection management
- `IBKRDataFetcher`: High-level data fetching interface

**Usage:**
```python
from src.ibkr_connector import IBKRDataFetcher
import asyncio

fetcher = IBKRDataFetcher()
df = asyncio.run(fetcher.fetch_stock_data('AAPL', duration=60, bar_size='1 min'))
print(df.head())  # Returns DataFrame with OHLCV data
```

**Methods:**
- `fetch_stock_data(symbol, duration, bar_size)` - Get stock data
- `fetch_forex_data(pair, duration, bar_size)` - Get forex data
- `get_market_data(contract, duration, bar_size)` - Generic market data
- `get_live_price(contract)` - Get current price
- `get_account_info()` - Account details
- `get_positions()` - Current holdings

### 2. `src/ibkr_executor.py` - Trade Execution
Execute orders and manage trades with risk management.

**Key Classes:**
- `IBKRTradeExecutor`: Execute trades on IBKR
- `RiskManager`: Position sizing and risk control

**Usage:**
```python
from src.ibkr_executor import IBKRTradeExecutor, RiskManager
import asyncio

executor = IBKRTradeExecutor()
rm = RiskManager(account_size=10000, max_risk_percent=2.0)

# Calculate position size
position_size = rm.calculate_position_size(entry=150, stop_loss=148)

# Place bracket order (entry + stop + target)
result = asyncio.run(executor.place_bracket_order(
    symbol='AAPL',
    action='BUY',
    quantity=position_size,
    entry_price=150.00,
    stop_loss=148.00,
    take_profit=155.00
))
```

**Methods:**
- `place_bracket_order(...)` - Entry + Stop + Target orders
- `place_market_order(...)` - Market order
- `get_positions()` - Current positions
- `get_open_orders()` - Pending orders
- `cancel_order(order_id)` - Cancel order

### 3. `predict_ibkr_live.py` - Live Predictions
Generate predictions using IBKR live data.

**Usage:**
```bash
# Run live prediction for AAPL
python predict_ibkr_live.py
```

**Output:**
```
╔════════════════════════════════════════════════════════════════════════════╗
║                    IBKR LIVE PREDICTION RESULT                             ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 LIVE MARKET DATA
───────────────────────────────────────────────────────────────────────────
Ticker:              AAPL
Current Price:       $150.25
Data Points:         60 candles (1 min)

🎯 PREDICTION
───────────────────────────────────────────────────────────────────────────
Direction:           LONG
Confidence:          72.5%
Recommendation:      🟢 BUY - 72% confidence

📈 TECHNICAL INDICATORS
───────────────────────────────────────────────────────────────────────────
RSI (14):            62.30
ADX (14):            25.50
ATR:                 $0.85 (0.57% of price)

💰 TRADING LEVELS
───────────────────────────────────────────────────────────────────────────
Entry:               $150.25
Stop Loss:           $149.40
Take Profit:         $152.00
Risk/Reward Ratio:   1:2.05
```

### 4. `trade_with_ibkr.py` - Complete Trading Workflow
Automated workflow: Analyze → Predict → Execute

**Usage:**
```bash
# Dry run (no real trades)
python trade_with_ibkr.py

# Execute real trades (CAREFUL!)
python trade_with_ibkr.py --live
```

**Features:**
- Connects to IBKR
- Fetches live data
- Generates prediction
- Calculates position size
- Places bracket order (if confidence > threshold)
- Monitors execution

## Configuration

### Connection Settings

**Paper Trading (Recommended for Testing):**
```python
from src.ibkr_connector import IBKRConnector

connector = IBKRConnector(
    host='127.0.0.1',
    port=7497,      # Paper trading port
    clientId=1
)
```

**Live Trading:**
```python
connector = IBKRConnector(
    host='127.0.0.1',
    port=7496,      # Live trading port
    clientId=1
)
```

### Risk Management Settings

```python
from src.ibkr_executor import RiskManager

# Max 2% risk per trade on $10,000 account = $200 max loss
rm = RiskManager(
    account_size=10000,
    max_risk_percent=2.0
)

# Calculate how many shares to buy
position_size = rm.calculate_position_size(
    entry=150.00,
    stop_loss=148.00  # $2 risk per share
)
# Result: position_size = 100 shares ($200 max loss)
```

## Quick Start

### Step 1: Setup IBKR
```bash
python setup_ibkr.py
```

### Step 2: Test Connection
```bash
python -m src.ibkr_connector
```

### Step 3: Get Live Predictions
```bash
python predict_ibkr_live.py
```

### Step 4: Execute Trades (Dry Run First!)
```bash
# Dry run - won't place actual orders
python trade_with_ibkr.py
```

## Real-Time Trading Example

```python
import asyncio
from predict_ibkr_live import IBKRLivePredictor
from src.ibkr_executor import IBKRTradeExecutor, RiskManager

async def automate_trading():
    # Initialize components
    predictor = IBKRLivePredictor()
    executor = IBKRTradeExecutor()
    rm = RiskManager(account_size=10000, max_risk_percent=2.0)
    
    # Generate prediction
    result = await predictor.predict_live('AAPL', duration=60, bar_size='1 min')
    
    # Check if signal is strong enough
    if result['confidence'] >= 60:
        # Calculate position size
        quantity = rm.calculate_position_size(
            result['entry'],
            result['stop_loss']
        )
        
        # Execute trade
        await executor.connect()
        trade = await executor.place_bracket_order(
            symbol=result['symbol'],
            action='BUY' if result['direction'] == 'LONG' else 'SELL',
            quantity=quantity,
            entry_price=result['entry'],
            stop_loss=result['stop_loss'],
            take_profit=result['take_profit']
        )
        await executor.disconnect()
        
        print(f"Trade executed: {trade}")

# Run automation
asyncio.run(automate_trading())
```

## Supported Bar Sizes

- `'1 min'` - 1-minute bars
- `'5 mins'` - 5-minute bars
- `'15 mins'` - 15-minute bars
- `'1 hour'` - Hourly bars
- `'1 day'` - Daily bars

## Troubleshooting

### Connection Issues

**Error: "There is no current event loop"**
- Solution: Make sure ib-insync is imported correctly
- The system uses `nest_asyncio` to handle this

**Error: "Connection refused"**
- Make sure TWS/IBGateway is running
- Check port number (7497 for paper, 7496 for live)
- Verify "Allow connections" is enabled in settings

**Error: "No data received"**
- Market may be closed
- Check if ticker symbol is valid
- Try a different bar size

### Trading Issues

**Orders not executing:**
1. Check account has sufficient buying power
2. Verify market hours (9:30 AM - 4:00 PM ET)
3. Check order price is reasonable (not too far from last price)

**Position sizing too small:**
- Increase account size in RiskManager
- Decrease max_risk_percent (currently 2%)
- Decrease stop loss distance (reduce risk per share)

## Performance Monitoring

### Check Positions
```python
executor = IBKRTradeExecutor()
positions = executor.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']} @ {pos['avg_cost']}")
```

### Monitor Orders
```python
orders = executor.get_open_orders()
for order in orders:
    print(f"{order['symbol']}: {order['status']} {order['remaining']} remaining")
```

### Check Account
```python
account_info = await connector.get_account_info()
print(f"Cash: ${account_info['cash']}")
print(f"Equity: ${account_info['equity']}")
print(f"Buying Power: ${account_info['buying_power']}")
```

## Best Practices

1. **Always use paper trading first**
   - Test strategies before risking real money
   - Verify connections and order flow

2. **Start with dry runs**
   - Use `dry_run=True` parameter
   - Verify predictions before execution

3. **Use appropriate position sizes**
   - Risk no more than 1-2% per trade
   - Calculate using stop loss distance
   - Use RiskManager for automation

4. **Monitor in real-time**
   - Check positions frequently
   - Set alerts for significant P&L swings
   - Be ready to exit manually if needed

5. **Use bracket orders**
   - Automatically sets stops and targets
   - Reduces emotional decision-making
   - Ensures disciplined risk management

## API Documentation

### IBKRConnector
```python
class IBKRConnector:
    async def connect() -> bool
    def disconnect()
    async def get_market_data(contract, duration, bar_size) -> DataFrame
    async def get_live_price(contract) -> float
    async def get_account_info() -> Dict
    def get_positions() -> List[Dict]
```

### IBKRTradeExecutor
```python
class IBKRTradeExecutor:
    async def connect() -> bool
    def disconnect()
    async def place_bracket_order(...) -> Dict
    async def place_market_order(...) -> Dict
    def get_positions() -> List[Dict]
    def get_open_orders() -> List[Dict]
    async def cancel_order(order_id) -> Dict
```

### RiskManager
```python
class RiskManager:
    def calculate_position_size(entry, stop_loss) -> int
    def get_trading_limits() -> Dict
```

## Support

For issues or questions:
1. Check IBKR documentation: https://www.interactivebrokers.com/en/software/am/am/concepts/about_api.htm
2. Review ib_insync docs: https://ib-insync.readthedocs.io/
3. Check GitHub repository: https://github.com/bijoym/predticker

## Disclaimer

**IMPORTANT:**
- This system is for educational purposes
- Past performance does not guarantee future results
- Always use stop losses and risk management
- Start with paper trading and small positions
- Do not risk more than you can afford to lose
- Consult with a financial advisor before live trading

---

**Status:** ✓ Ready for live trading with IBKR  
**Last Updated:** December 10, 2025  
**Version:** 1.0
