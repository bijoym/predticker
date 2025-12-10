"""Predict BTQ (QQQ) with adaptive weights."""

import sys
sys.path.insert(0, 'src')
from enhanced_predictor_adaptive import (
    fetch_4hour_data, compute_enhanced_features, enhanced_prediction_adaptive,
    generate_trading_levels, detect_volatility_regime
)
from regime_weights import RegimeAdaptiveWeights

# Load weights
optimizer = RegimeAdaptiveWeights()
optimizer.load_weights('models/regime_weights_20251210_135927.pkl')

# Fetch current data
df = fetch_4hour_data('BTQ', days=30)
print(f'\nBTQ - Latest 4-hour Prediction')
print('='*70)
print(f'Data points collected: {len(df)}')

# Get features
features = compute_enhanced_features(df)

# Get predictions
static_pred = enhanced_prediction_adaptive(features, optimizer=None, use_adaptive_weights=False)
adaptive_pred = enhanced_prediction_adaptive(features, optimizer, use_adaptive_weights=True)

# Get trading levels
levels = generate_trading_levels(df['Close'].iloc[-1], features['atr'])

# Detect regime
regime = detect_volatility_regime(features)

print(f'\n📊 MARKET DATA')
print('-'*70)
print(f'Current Price:      ${df["Close"].iloc[-1]:.2f}')
print(f'4h High:            ${df["High"].iloc[-1]:.2f}')
print(f'4h Low:             ${df["Low"].iloc[-1]:.2f}')
print(f'Volume:             {df["Volume"].iloc[-1]:,.0f}')
print(f'ATR (Volatility):   ${features["atr"]:.2f} ({features["atr_percent"]:.2f}%)')

print(f'\n🎯 MARKET REGIME')
print('-'*70)
print(f'Regime:             {regime}')
print(f'ADX (Trend):        {features["adx"]:.1f}')
print(f'RSI:                {features["rsi"]:.1f}')
print(f'MACD:               {"Bullish" if features["macd"] > features["macd_signal"] else "Bearish"}')

print(f'\n📈 PREDICTIONS')
print('-'*70)
print(f'Static Weights:     {static_pred["prediction"]} (Confidence: {static_pred["confidence"]:.1f}%)')
print(f'Adaptive Weights:   {adaptive_pred["prediction"]} (Confidence: {adaptive_pred["confidence"]:.1f}%)')

print(f'\n📍 WEIGHT DISTRIBUTION')
print('-'*70)
print(f'Static Weights:')
for k, v in static_pred['weights'].items():
    print(f'  {k:20s}: {v:6.1%}')

print(f'\nAdaptive Weights:')
for k, v in adaptive_pred['weights'].items():
    print(f'  {k:20s}: {v:6.1%}')

print(f'\n💰 TRADING LEVELS')
print('-'*70)
print(f'If LONG:')
print(f'  Entry:              ${df["Close"].iloc[-1]:.2f}')
print(f'  Stop Loss:          ${levels["long_stop_loss"]:.2f}')
print(f'  Take Profit:        ${levels["long_take_profit"]:.2f}')
print(f'  Risk/Reward:        1:{levels["risk_reward_ratio"]:.1f}')

print(f'\nIf SHORT:')
print(f'  Entry:              ${df["Close"].iloc[-1]:.2f}')
print(f'  Stop Loss:          ${levels["short_stop_loss"]:.2f}')
print(f'  Take Profit:        ${levels["short_take_profit"]:.2f}')
print(f'  Risk/Reward:        1:{levels["risk_reward_ratio"]:.1f}')

print(f'\n🔍 SIGNAL COMPONENTS (Adaptive Weights)')
print('-'*70)
for signal in adaptive_pred['signals'][:10]:
    print(f'  • {signal}')
if len(adaptive_pred['signals']) > 10:
    print(f'  ... and {len(adaptive_pred["signals"])-10} more')

print(f'\n' + '='*70)
