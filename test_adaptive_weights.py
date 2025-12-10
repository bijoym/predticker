"""Test adaptive vs static weight predictions on live data.

This script compares predictions made with adaptive weights to those with
static weights to validate the improvement in real-world scenarios.
"""

import sys
import os
from typing import Dict, List
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from regime_weights import RegimeAdaptiveWeights
from enhanced_predictor_adaptive import (
    fetch_4hour_data, compute_enhanced_features, 
    enhanced_prediction_adaptive, detect_volatility_regime,
    generate_trading_levels
)


def test_ticker_adaptive_vs_static(ticker: str,
                                   optimizer: RegimeAdaptiveWeights,
                                   days: int = 30,
                                   lookback: int = 20) -> Dict:
    """Test adaptive vs static weights on a ticker.
    
    Args:
        ticker: Stock ticker
        optimizer: Trained RegimeAdaptiveWeights optimizer
        days: Days of test data
        lookback: Lookback period
    
    Returns:
        Comparison metrics dictionary
    """
    print(f"\nTesting {ticker} (last {days} days)...")
    
    try:
        df = fetch_4hour_data(ticker, days=days)
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None
    
    if len(df) < lookback + 1:
        print(f"Not enough data for {ticker}")
        return None
    
    adaptive_correct = 0
    static_correct = 0
    regime_counts = {}
    total = 0
    
    for i in range(lookback, len(df) - 1):
        historical_df = df.iloc[max(0, i-lookback):i].copy()
        
        if len(historical_df) < 5:
            continue
        
        try:
            features = compute_enhanced_features(historical_df)
            regime = detect_volatility_regime(features)
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
            
            # Actual direction
            actual_close_next = df['Close'].iloc[i + 1]
            actual_close_curr = df['Close'].iloc[i]
            price_change = actual_close_next - actual_close_curr
            actual_direction = 1 if price_change > 0 else 0
            
            # Adaptive prediction
            adaptive_pred = enhanced_prediction_adaptive(
                features, optimizer, use_adaptive_weights=True
            )
            adaptive_direction = 1 if adaptive_pred['prediction'] == 'LONG' else 0
            if adaptive_direction == actual_direction:
                adaptive_correct += 1
            
            # Static prediction
            static_pred = enhanced_prediction_adaptive(
                features, optimizer=None, use_adaptive_weights=False
            )
            static_direction = 1 if static_pred['prediction'] == 'LONG' else 0
            if static_direction == actual_direction:
                static_correct += 1
            
            total += 1
            
        except Exception:
            continue
    
    if total == 0:
        return None
    
    adaptive_accuracy = (adaptive_correct / total) * 100
    static_accuracy = (static_correct / total) * 100
    improvement = adaptive_accuracy - static_accuracy
    
    print(f"  Static Accuracy:   {static_accuracy:6.2f}% ({static_correct}/{total})")
    print(f"  Adaptive Accuracy: {adaptive_accuracy:6.2f}% ({adaptive_correct}/{total})")
    print(f"  Improvement:       {improvement:+6.2f}%")
    print(f"  Market Regimes:    {', '.join([f'{k}({v})' for k,v in regime_counts.items()])}")
    
    return {
        'ticker': ticker,
        'static_accuracy': static_accuracy,
        'adaptive_accuracy': adaptive_accuracy,
        'improvement': improvement,
        'static_correct': static_correct,
        'adaptive_correct': adaptive_correct,
        'total_samples': total,
        'regime_distribution': regime_counts
    }


def main():
    parser = argparse.ArgumentParser(
        description="Test adaptive vs static weight predictions"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL"],
        help="Tickers to test"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days of test data"
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Path to saved weights file"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("ADAPTIVE vs STATIC WEIGHTS - LIVE TEST")
    print("="*70)
    print(f"Tickers: {', '.join(args.tickers)}")
    print(f"Test Period: {args.days} days")
    print("="*70)
    
    # Load or train optimizer
    optimizer = RegimeAdaptiveWeights()
    
    if args.weights and os.path.exists(args.weights):
        print(f"\nLoading weights from: {args.weights}")
        optimizer.load_weights(args.weights)
    else:
        print("\nNo weights file specified. Using default static weights.")
        print("To train weights, run: python train_regime_weights.py --save <path>")
        # Initialize with default setup
        optimizer.regime_weights = {
            'trending_strong': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.35, 
                               'trend_strength': 0.15, 'stochastic': 0.15, 'name': 'volatility_aware'},
            'trending_weak': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.35,
                             'trend_strength': 0.15, 'stochastic': 0.15, 'name': 'volatility_aware'},
            'ranging': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.20,
                       'trend_strength': 0.20, 'stochastic': 0.15, 'name': 'standard'},
            'ranging_high': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.35,
                            'trend_strength': 0.15, 'stochastic': 0.15, 'name': 'volatility_aware'}
        }
        optimizer.is_trained = True
    
    # Test each ticker
    print("\nPHASE 1: PER-TICKER ANALYSIS")
    print("-"*70)
    
    results = []
    for ticker in args.tickers:
        result = test_ticker_adaptive_vs_static(ticker, optimizer, days=args.days)
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if results:
        summary_df = pd.DataFrame(results)
        
        print("\nPer-Ticker Results:")
        print("-"*70)
        for _, row in summary_df.iterrows():
            print(f"{row['ticker']:6s}  Static: {row['static_accuracy']:6.2f}%  "
                  f"Adaptive: {row['adaptive_accuracy']:6.2f}%  "
                  f"Improvement: {row['improvement']:+6.2f}%")
        
        avg_static = summary_df['static_accuracy'].mean()
        avg_adaptive = summary_df['adaptive_accuracy'].mean()
        avg_improvement = summary_df['improvement'].mean()
        
        print("-"*70)
        print(f"{'AVERAGE':6s}  Static: {avg_static:6.2f}%  "
              f"Adaptive: {avg_adaptive:6.2f}%  "
              f"Improvement: {avg_improvement:+6.2f}%")
        
        # Overall statistics
        total_static = summary_df['static_correct'].sum()
        total_adaptive = summary_df['adaptive_correct'].sum()
        total_samples = summary_df['total_samples'].sum()
        total_static_accuracy = (total_static / total_samples) * 100
        total_adaptive_accuracy = (total_adaptive / total_samples) * 100
        total_improvement = total_adaptive_accuracy - total_static_accuracy
        
        print("\nCumulative Results:")
        print("-"*70)
        print(f"Total Predictions:  {total_samples}")
        print(f"Static Correct:     {total_static}/{total_samples} ({total_static_accuracy:.2f}%)")
        print(f"Adaptive Correct:   {total_adaptive}/{total_samples} ({total_adaptive_accuracy:.2f}%)")
        print(f"Overall Improvement: {total_improvement:+.2f}%")
        
        # Verdict
        print("\n" + "="*70)
        if avg_improvement > 2.0:
            print("✓ SIGNIFICANT IMPROVEMENT CONFIRMED")
            print("  Ready to deploy adaptive weights in production")
        elif avg_improvement > 0:
            print("✓ MODEST IMPROVEMENT CONFIRMED")
            print("  Consider deploying adaptive weights with monitoring")
        else:
            print("✗ NO IMPROVEMENT")
            print("  Continue with static weights or retrain with more data")
    else:
        print("No results to summarize")


if __name__ == "__main__":
    main()
