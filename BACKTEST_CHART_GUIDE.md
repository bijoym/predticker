# Understanding the Backtest Results Chart

## Overview
The backtest results chart (`backtest_results.png`) contains 4 key visualization panels that help you understand how the market predictor performed across different tickers over a 60-day period with $10,000 initial capital.

---

## Panel 1: Total Return by Ticker (%)
**Top-Left Chart - Bar Chart**

### What It Shows:
- **Green bars** = Profitable trades (positive return)
- **Red bars** = Losing trades (negative return)
- **Height of bar** = Percentage gain or loss

### How to Read It:
```
GOOGL:  +0.65% (Green) ✓ Made money
AMZN:   +0.03% (Green) ✓ Barely profitable
MSFT:   -0.13% (Red)   ✗ Small loss
AAPL:   -0.54% (Red)   ✗ Loss
TSLA:   -1.08% (Red)   ✗ Worst performer
```

### What It Means:
- This is your **bottom line** - Did the strategy make or lose money?
- GOOGL was the only strong performer
- AMZN broke even
- MSFT, AAPL, TSLA lost money
- **Average return: -0.21%** (not profitable on average)

### How to Use This:
- Look for **green bars** → Strategy works for that ticker
- **Red bars below -1%** → Strategy struggles with that stock
- For day trading, you want to see **consistent green bars**

---

## Panel 2: Win Rate by Ticker (%)
**Top-Right Chart - Bar Chart**

### What It Shows:
- **Height of bar** = Percentage of trades that made money
- **Orange dashed line at 50%** = Random chance baseline
- Bars above 50% = Better than random
- Bars below 50% = Worse than random

### How to Read It:
```
GOOGL:  71.43% (Above line) ✓ Strong
MSFT:   40.00% (Below line) ✗ Weak
AMZN:   50.00% (On line)    = Random
AAPL:   25.00% (Below line) ✗ Very weak
TSLA:   26.32% (Below line) ✗ Very weak
```

### What It Means:
- **Win Rate = Winning Trades / Total Trades**
- GOOGL wins ~7 out of 10 trades
- AAPL & TSLA win only 1-2 out of 10 trades
- A 50% win rate would mean coin-flip luck
- **50%+ is good, 70%+ is excellent**

### How to Use This:
- **Above 50%** → Prediction is working better than luck
- **Below 50%** → Need to improve the prediction logic
- **Below 30%** → Strategy is counterproductive for that ticker

---

## Panel 3: Profit Factor by Ticker
**Bottom-Left Chart - Bar Chart**

### What It Shows:
- **Profit Factor = Total Wins / Total Losses**
- Bars higher = More profitable per trade
- **Orange dashed line at 1.0** = Break-even
- Bars above 1.0 = More profit than loss
- Bars below 1.0 = More loss than profit

### How to Read It:
```
GOOGL:  5.07 (Far above)    ✓ Excellent: Wins are 5x bigger than losses
AMZN:   1.08 (Slightly above) = Marginal: Wins slightly bigger than losses
MSFT:   0.80 (Below)         ✗ Negative: Losses larger than wins
AAPL:   0.20 (Far below)     ✗ Poor: Wins only 20% of loss size
TSLA:   0.55 (Below)         ✗ Bad: Wins only 55% of loss size
```

### What It Means:
- GOOGL: For every $1 lost, it makes $5.07
- AAPL: For every $1 lost, it only makes $0.20
- **Profit Factor > 2.0** = Excellent strategy
- **Profit Factor > 1.0** = Profitable
- **Profit Factor < 1.0** = Unprofitable

### How to Use This:
- This is the **most important metric** for strategy quality
- Shows quality of wins vs losses, not just frequency
- **Aim for > 1.5** for consistent profitability

---

## Panel 4: Number of Trades by Ticker
**Bottom-Right Chart - Bar Chart**

### What It Shows:
- **Height of bar** = How many trades were executed
- Higher bars = More trading opportunities
- Lower bars = Fewer trading opportunities

### How to Read It:
```
TSLA:   19 trades (Most active)
AAPL:   8 trades
GOOGL:  7 trades
AMZN:   8 trades
MSFT:   5 trades (Least active)
```

### What It Means:
- TSLA had many trading signals (high volatility = more opportunities)
- MSFT had fewer signals (less clear patterns)
- More trades = more statistical significance (but also more commissions)
- Fewer trades = less data to judge strategy quality

### How to Use This:
- **5-10 trades** = Good sample size for evaluation
- **> 20 trades** = Plenty of data (but may be overfitting or too noisy)
- **< 5 trades** = Too few to judge (could be luck)

---

## How to Interpret Overall Performance

### The Complete Picture:

**GOOGL (Best Case):**
- ✓ Return: +0.65%
- ✓ Win Rate: 71.43% (above 50%)
- ✓ Profit Factor: 5.07 (excellent)
- ✓ Trades: 7 (good sample)
- **Verdict: Strategy works well for this ticker**

**TSLA (Worst Case):**
- ✗ Return: -1.08%
- ✗ Win Rate: 26.32% (well below 50%)
- ✗ Profit Factor: 0.55 (unprofitable)
- ✗ Trades: 19 (many losses accumulated)
- **Verdict: Strategy struggles with high volatility stocks**

---

## What This Tells You About the Strategy

### Strengths:
1. **Works for stable stocks** - GOOGL, AMZN perform decently
2. **Better than random on some tickers** - GOOGL shows 71% accuracy
3. **Controlled risk** - Stop-loss limits downside

### Weaknesses:
1. **Struggles with volatility** - TSLA loses money despite many trades
2. **Low accuracy on some stocks** - AAPL (47%), TSLA (43%) below 50%
3. **Not consistently profitable** - Average return is negative
4. **Average win < Average loss on bad tickers** - Low profit factors

---

## How to Improve Based on These Results

### 1. **Stock Selection**
- Only trade GOOGL-type stocks (stable, trending)
- Avoid TSLA-type stocks (highly volatile, choppy)

### 2. **Add Filters**
- Combine with RSI or MACD for better entries
- Skip trades when volatility is too high
- Only trade during liquid market hours

### 3. **Adjust Stop-Loss/Take-Profit**
- TSLA: Make stop-loss tighter (1% vs 2%)
- TSLA: Make take-profit closer (2% vs 4%)
- Use volatility-adjusted levels

### 4. **Risk Management**
- Position sizing based on volatility
- Max 2-3% risk per trade
- Daily/weekly drawdown limits

### 5. **Refine Prediction Logic**
- Add more indicators (volume, RSI, MACD)
- Combine multiple timeframes
- Use machine learning to weight factors

---

## Key Metrics Summary

| Metric | Good | Excellent | What It Means |
|--------|------|-----------|----------------|
| **Total Return** | > 0% | > 5% | Overall profitability |
| **Win Rate** | > 50% | > 65% | Prediction accuracy |
| **Profit Factor** | > 1.0 | > 2.0 | Quality of wins vs losses |
| **Prediction Accuracy** | > 50% | > 55% | Direction prediction correctness |
| **Avg Win vs Avg Loss** | 2:1 | 3:1 or higher | Risk/reward ratio |

---

## Example: How to Read GOOGL's Results

```
GOOGL Backtest Results:
├── Return: +0.65% ........................ Made $65 on $10,000 ✓
├── Trades: 7 ............................ Executed 7 trades
├── Win Rate: 71.43% ..................... 5 wins, 2 losses ✓
├── Profit Factor: 5.07 .................. Wins are 5x losses ✓
├── Prediction Accuracy: 55.75% .......... Correct 63/113 times ✓
└── Avg Win: $16.11 / Avg Loss: $-7.94 .. 2:1 win/loss ratio ✓
    
INTERPRETATION: 
The strategy correctly predicted GOOGL's direction 55.75% of the time.
This led to 7 trades with a 71% win rate, making $65 profit.
For every $1 lost, the strategy made $5.07.
This is the ideal scenario for a trading strategy.
```

---

## Questions to Ask Yourself

1. **Is the strategy profitable?** (Check Total Return)
2. **Is it better than random?** (Check Win Rate > 50%)
3. **Are wins bigger than losses?** (Check Profit Factor > 1.0)
4. **Is the prediction accurate?** (Check Prediction Accuracy)
5. **Is there enough data?** (Check Trade Count)
6. **Why does it work for some stocks but not others?** (Compare charts)

---

## Next Steps

### If Results Are Good (Like GOOGL):
✓ Trade this strategy on that stock  
✓ Focus on stocks with similar characteristics  
✓ Optimize position sizing and risk management  

### If Results Are Bad (Like TSLA):
✗ Don't trade this strategy on this stock  
✗ Identify what makes this stock different  
✗ Add filters to avoid similar stocks  
✗ Refine prediction logic for high-volatility assets  

---

Generated: December 10, 2025
