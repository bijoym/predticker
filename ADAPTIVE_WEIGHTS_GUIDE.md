# Using Adaptive Weights - Quick Start Guide

## What Are Adaptive Weights?

Adaptive weights automatically adjust indicator importance based on market conditions. Instead of using the same weights (Trend 20%, Momentum 25%, Volatility 20%, Trend Strength 20%, Stochastic 15%) in all markets, the system learns which weights work best for different regimes.

**Results:**
- +0.89% accuracy improvement
- +3.72% return improvement
- Especially strong on volatile stocks like TSLA (+30.72%)

## Quick Start (3 Steps)

### Step 1: Train the Weights

```bash
python train_regime_weights.py --tickers AAPL MSFT GOOGL AMZN --days 90
```

This will:
- Collect 90 days of historical data
- Test 6 different weight combinations
- Save optimal weights to `models/regime_weights_[timestamp].pkl`

### Step 2: Test the Weights

```bash
python backtest_adaptive_weights.py --weights models/regime_weights_20251210_135927.pkl
```

Compare performance of adaptive vs static weights on historical data.

### Step 3: Use in Predictions

```python
from src.regime_weights import RegimeAdaptiveWeights
from src.enhanced_predictor_adaptive import (
    fetch_4hour_data, compute_enhanced_features, enhanced_prediction_adaptive
)

# Load trained weights
optimizer = RegimeAdaptiveWeights()
optimizer.load_weights('models/regime_weights_20251210_135927.pkl')

# Get price data
df = fetch_4hour_data('AAPL', days=30)

# Compute features
features = compute_enhanced_features(df)

# Get prediction WITH adaptive weights
result = enhanced_prediction_adaptive(features, optimizer, use_adaptive_weights=True)

print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.1f}%")
print(f"Weights used: {result['weights']}")
```

## Files & Tools

### Core Modules
- **src/regime_weights.py** - Adaptive weight optimizer
- **src/enhanced_predictor_adaptive.py** - Prediction engine with adaptive support

### Training & Testing
- **train_regime_weights.py** - Train new weights
- **backtest_adaptive_weights.py** - Compare performance
- **test_adaptive_weights.py** - Live testing

### Pre-Trained Weights
- **models/regime_weights_20251210_135927.pkl** - Ready to use (trained on 90-day data)

## How It Works

### Market Regime Detection
The system detects market conditions:
- **Trending Strong:** High ADX (>30) - Use momentum-heavy weights
- **Trending Weak:** Moderate ADX (20-30) - Use balanced weights
- **Ranging Low Vol:** Low ADX + Low ATR - Use standard weights
- **Ranging High Vol:** Low ADX + High ATR - Use volatility-aware weights

### Weight Combinations Tested

| Name | Trend | Momentum | Volatility | TrendStrength | Stochastic | Result |
|------|-------|----------|-----------|---------------|------------|--------|
| standard | 20% | 25% | 20% | 20% | 15% | 53.42% |
| momentum_heavy | 15% | 40% | 15% | 20% | 10% | 53.42% |
| trend_heavy | 35% | 15% | 20% | 25% | 5% | 51.14% |
| **volatility_aware** | **20%** | **25%** | **35%** | **15%** | **15%** | **54.94%** ✓ |
| adx_focused | 15% | 20% | 15% | 40% | 10% | 52.41% |
| balanced | 20% | 30% | 25% | 15% | 10% | 53.80% |

The system picks the best weights for each regime.

## Advanced Usage

### Compare Static vs Adaptive on New Tickers

```bash
# Train on these tickers
python train_regime_weights.py --tickers NVDA AMD INTC --days 120

# Test new weights
python backtest_adaptive_weights.py --tickers NVDA AMD INTC --weights models/regime_weights_new.pkl
```

### Live Prediction with Adaptive Weights

```python
# Get current market features
current_df = fetch_4hour_data('TSLA', days=30)
features = compute_enhanced_features(current_df)

# Get adaptive prediction
pred = enhanced_prediction_adaptive(features, optimizer, use_adaptive_weights=True)

# Also get components to understand the decision
print("Signals:", pred['signals'])
print("Component Scores:", pred['components'])
print("Weights Applied:", pred['weights'])

# For comparison, also get static prediction
static_pred = enhanced_prediction_adaptive(features, use_adaptive_weights=False)
print(f"\nStatic:  {static_pred['prediction']} (conf: {static_pred['confidence']:.1f}%)")
print(f"Adaptive: {pred['prediction']} (conf: {pred['confidence']:.1f}%)")
```

### Monitor Weight Changes

```python
from src.enhanced_predictor_adaptive import detect_volatility_regime

features = compute_enhanced_features(df)
regime = detect_volatility_regime(features)
weights = optimizer.get_adaptive_weights(features)

print(f"Current regime: {regime}")
print(f"Current weights:")
for category, weight in weights.items():
    print(f"  {category}: {weight:.1%}")
```

## Key Parameters

### Training
- `--days`: Historical data period (default 90)
- `--tickers`: Which stocks to train on (default AAPL MSFT GOOGL)
- `--save`: Path to save weights (default auto-generated)

### Backtesting
- `--days`: Backtest period (default 90)
- `--tickers`: Which stocks to backtest (default AAPL MSFT GOOGL)
- `--weights`: Path to trained weights file

### Features (auto-detected)
- `rsi`: Relative Strength Index (momentum)
- `macd`: Moving Average Convergence Divergence (momentum)
- `adx`: Average Directional Index (trend strength)
- `atr`: Average True Range (volatility)
- `bb_position`: Position within Bollinger Bands (volatility)
- `slope`: Price slope (trend)
- `k_stoch`: Stochastic K (stochastic)

## Performance Expectations

Based on 90-day backtest across 5 tickers:

| Metric | Static | Adaptive | Gain |
|--------|--------|----------|------|
| Average Accuracy | 49.75% | 50.63% | +0.89% |
| Average Return | 10.10% | 13.81% | +3.72% |
| Profit Factor | 1.15 | 1.18 | +0.03 |

**Performance by ticker:**
- TSLA: +30.72% (excellent for volatile stocks)
- AMZN: +5.78% (good for moderate volatility)
- MSFT: +3.61% (good for trending)
- AAPL: -1.46% (slight degradation)
- GOOGL: -20.06% (better with static weights)

## Troubleshooting

### Issue: "No results to summarize" in backtest

**Solution:** Use at least 60 days of data to get enough test signals

```bash
python backtest_adaptive_weights.py --days 60 --tickers AAPL MSFT
```

### Issue: Weights don't exist

**Solution:** Train new weights first

```bash
python train_regime_weights.py --save models/my_weights.pkl
```

### Issue: Want to compare two weight files

**Solution:** Run backtest with each weights file

```bash
python backtest_adaptive_weights.py --weights models/weights_v1.pkl
python backtest_adaptive_weights.py --weights models/weights_v2.pkl
```

## When to Retrain

Retrain weights when:
1. Market conditions change significantly (trend → range, or vice versa)
2. You have 30+ days of new market data
3. You want to optimize for a new set of tickers
4. Performance degrades by >1% on validation

## Backward Compatibility

Existing code continues to work unchanged:

```python
# Old way (static weights) - still works
from src.enhanced_predictor import enhanced_prediction
result = enhanced_prediction(features)  # Uses default static weights

# New way (adaptive weights)
from src.enhanced_predictor_adaptive import enhanced_prediction_adaptive
result = enhanced_prediction_adaptive(features, optimizer, use_adaptive_weights=True)
```

## Next Steps

1. **Try it:** Run `python backtest_adaptive_weights.py` with pre-trained weights
2. **Compare:** See which weight combination wins for your markets
3. **Deploy:** Use adaptive weights in live trading
4. **Monitor:** Track performance and retrain monthly
5. **Optimize:** Consider ticker-specific weight models

---

For detailed information, see `ML_ADAPTIVE_WEIGHTS_REPORT.md`
