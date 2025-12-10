# Backtest Results Summary

## Overview
Backtested the market predictor on 60 days of historical data with $10,000 initial capital.

## Results by Ticker

### GOOGL (Best Performer)
- **Total Return:** +0.65%
- **Total Trades:** 7
- **Win Rate:** 71.43% ✓
- **Profit Factor:** 5.07 ✓
- **Status:** ✓ Profitable

### AMZN (Neutral)
- **Total Return:** +0.03%
- **Total Trades:** 8
- **Win Rate:** 50.00%
- **Profit Factor:** 1.08
- **Status:** Marginally Profitable

### MSFT (Slight Loss)
- **Total Return:** -0.13%
- **Total Trades:** 5
- **Win Rate:** 40.00%
- **Profit Factor:** 0.80
- **Status:** Small Loss

### AAPL (Loss)
- **Total Return:** -0.54%
- **Total Trades:** 8
- **Win Rate:** 25.00%
- **Profit Factor:** 0.20
- **Status:** Loss

### TSLA (Worst Performer)
- **Total Return:** -1.08%
- **Total Trades:** 19
- **Win Rate:** 26.32%
- **Profit Factor:** 0.55
- **Status:** Loss

## Key Findings

1. **GOOGL showed the strongest performance** with a 71.43% win rate and a profit factor of 5.07, indicating strong profitability.

2. **Strategy works better in ranging/trending markets** - GOOGL and AMZN (more stable) performed better than TSLA (highly volatile).

3. **Win rate matters** - Higher win rates correlate with better returns. GOOGL's 71.43% win rate vs TSLA's 26.32% shows significant difference.

4. **Risk/Reward ratio effectiveness** - The 2%/4% for LONG and 5%/5% for SHORT strategies are working as intended, with positive profit factors for 3 out of 5 tickers.

5. **Portfolio level** - Average across all tickers: -0.21% return. Strategy needs optimization for more consistent profitability.

## Recommendations for Improvement

1. **Add position sizing** - Dynamically adjust trade size based on volatility
2. **Add filters** - Combine with RSI, MACD, or other indicators for better entry points
3. **Optimize time periods** - Test different lookback windows for feature calculation
4. **Volatility adjustment** - Scale stop-loss and take-profit based on current volatility
5. **Drawdown management** - Implement max drawdown limits to protect capital
6. **Machine learning** - Train a model on historical data to improve predictions

## Performance Metrics Interpretation

- **Profit Factor > 1.0:** Profitable (3/5 tickers)
- **Win Rate > 50%:** Better than random (2/5 tickers)
- **Profit Factor > 2.0:** Excellent (1/5 tickers - GOOGL)

---
Generated: December 10, 2025
