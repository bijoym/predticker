#!/usr/bin/env python
"""Quick test of enhanced predictor on multiple tickers."""

from src.enhanced_predictor import fetch_4hour_data, compute_enhanced_features, enhanced_prediction

tickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL']

print("=" * 70)
print("ENHANCED PREDICTOR - MULTI-TICKER TEST")
print("=" * 70)

for ticker in tickers:
    try:
        df = fetch_4hour_data(ticker, days=90)
        features = compute_enhanced_features(df)
        result = enhanced_prediction(features)
        
        print(f"\n{ticker.upper()}")
        print(f"  Price: ${features['price']:.2f}")
        print(f"  Prediction: {result['prediction']} | Confidence: {result['confidence']:.1f}%")
        print(f"  RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}")
        
    except Exception as e:
        print(f"\n{ticker.upper()}: Error - {e}")

print("\n" + "=" * 70)
