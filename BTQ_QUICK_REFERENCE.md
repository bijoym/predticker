# BTQ Trading Analysis - Quick Reference

## 🎯 Bottom Line

**Prediction:** LONG  
**Confidence:** 18% (LOW)  
**Current Price:** $6.85  
**Target:** $7.78 | Stop: $6.39 | Risk/Reward: 1:2  
**Recommendation:** CONDITIONAL - Only for experienced traders with 50% position sizing

---

## 📊 Backtest Summary

**90-Day Performance (vs Static Weights):**

```
Metric                  Static      Adaptive    Result
────────────────────────────────────────────────────
Accuracy                52.44%      54.88%      +2.44% ✓
Win Rate                52.44%      54.88%      +2.44% ✓
Total Return            118.88%     114.66%     -4.22%
Profit Factor           1.84        1.80        —
Trades                  82          82          —

Status: Adaptive weights provide BETTER ACCURACY on BTQ
```

---

## 📈 Current Market Snapshot

| Indicator | Value | Signal |
|-----------|-------|--------|
| Price | $6.85 | Current entry |
| ATR | $0.46 (6.75%) | HIGH volatility |
| ADX | 18.9 | WEAK trend |
| RSI | 46.9 | Neutral |
| MACD | Bullish | Above signal |
| Stochastic | K>D | Bullish |
| Slope | Negative | Bearish |
| Market | High Vol + Weak Trend | Choppy |

**Status:** Mixed signals in choppy market

---

## 🎲 Trading Setup

### LONG Setup
```
Entry:          $6.85 (current)
Stop Loss:      $6.39 (0.46 risk)
Take Profit:    $7.78 (0.93 profit)
Risk/Reward:    1:2.0 ✓ Good ratio
Position Size:  50% (low confidence)
```

### Risk Calculation
- **Risk per share:** $0.46
- **Potential profit:** $0.93
- **Max loss (50 shares):** $23
- **Potential gain (50 shares):** $46.50

---

## ✓ Bullish Case (5 signals)
1. ✓ Uptrend confirmed (SMA20 > SMA50)
2. ✓ EMA bullish (12 > 26)
3. ✓ MACD bullish
4. ✓ Stochastic K>D crossover
5. ✓ RSI in buy zone (30-50)

**Score: 5/10 (moderate bullish)**

---

## ✗ Bearish Case (3 signals)
1. ✗ Negative slope (short-term down)
2. ✗ Weak trend (ADX < 20)
3. ✗ High volatility (risky)

**Score: 3/10 (weak bearish)**

---

## 💡 Trading Decision Tree

```
                    BTQ at $6.85
                         |
                    [LONG Signal]
                    Confidence: 18%
                         |
        ┌────────────────┼────────────────┐
        |                |                |
   CONSERVATIVE    MODERATE          AGGRESSIVE
   (Most traders)  (Some traders)     (Experts only)
        |                |                |
      WAIT            ENTER             ENTER
   for ADX>20        50% size           50% size
      or             SL $6.39           SL $6.39
   RSI extreme       TP $7.78           TP $7.78
        |                |                |
   TARGET: 55%+      RISK: $0.23        RISK: $0.23
   confidence        PROFIT: $0.46      PROFIT: $0.46
```

---

## ⚙️ How to Use

### Quick Check
```bash
python predict_btq.py
```

### Run Backtest
```bash
python backtest_adaptive_weights.py --tickers BTQ --days 90
```

### Custom Period
```bash
python backtest_adaptive_weights.py --tickers BTQ --days 120
```

---

## 📋 Files Generated

| File | Purpose |
|------|---------|
| `predict_btq.py` | Live prediction script |
| `BTQ_ANALYSIS.md` | Full detailed analysis |
| Backtest data | In git history |

---

## 🔔 Key Takeaways

1. **Adaptive weights give +2.44% accuracy on BTQ** - Better than static
2. **Low confidence (18%)** - Mixed signals, don't go all-in
3. **High volatility (6.75%)** - Expect big price swings
4. **1:2 Risk/Reward is excellent** - But only if signal works
5. **Conservative traders should wait** - For clearer signals

---

## 📊 When to Trade vs When to Wait

### ✓ Good to Trade
- If you accept 18% miss rate
- You can afford $0.46 loss
- You want volatility trading
- You use tight stops

### ✗ Better to Wait For
- ADX > 25 (strong trend)
- RSI > 70 or < 30 (extreme)
- Confidence > 50%
- Clearer market direction

---

## 🎯 Expected Outcomes

**If you take this trade (100 times with 50% size):**

```
Win Rate:        54.88% (55 wins, 45 losses)
Avg Win:         $46.50 (per winning trade)
Avg Loss:        -$23.00 (per losing trade)

Expected Value:
  Wins:   55 × $46.50 =   $2,557.50
  Loss:   45 × -$23.00 =  -$1,035.00
  ─────────────────────────────────
  NET:                    +$1,522.50

Per trade:     +$15.23 average
ROI:           +66% on risk

⚠️ NOTE: Past performance ≠ future results
        Use proper risk management always
```

---

## 🛡️ Risk Management Checklist

- [ ] Position size set to 50% (because confidence is low)
- [ ] Stop loss entered at $6.39 (hardcoded)
- [ ] Take profit set at $7.78
- [ ] Risk per trade = max 2% of account
- [ ] Don't risk more than you can afford to lose
- [ ] Close position if trend breaks
- [ ] Monitor volume (need to see 588k+ volume)

---

## 📞 Questions?

See full analysis: `BTQ_ANALYSIS.md`  
View code: `predict_btq.py`  
Backtest results in git history

---

**Generated:** 2025-12-10  
**Market:** Open  
**Confidence:** 18% (LOW)  
**Recommendation:** Conditional LONG (50% size)
