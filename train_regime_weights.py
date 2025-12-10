"""Train regime-adaptive weights on historical backtest data.

This approach tests different weight combinations to find the best ones
for different market conditions, without ML overfitting issues.
"""

import sys
import os
from typing import Dict, List, Tuple
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from regime_weights import RegimeAdaptiveWeights
from enhanced_predictor_adaptive import (
    fetch_4hour_data, compute_enhanced_features, 
    enhanced_prediction_adaptive
)


def collect_training_data(tickers: List[str], 
                         days: int = 90,
                         lookback: int = 20) -> Tuple[List[Dict], List[Dict]]:
    """Collect features and predictions from multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        days: Days of historical data
        lookback: Lookback period for features
    
    Returns:
        Tuple of (features_list, predictions_list)
    """
    all_features = []
    all_predictions = []
    
    for ticker in tickers:
        print(f"\nCollecting data for {ticker}...")
        
        try:
            df = fetch_4hour_data(ticker, days=days)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
        
        if len(df) < lookback + 1:
            print(f"Not enough data for {ticker}")
            continue
        
        ticker_features = []
        ticker_predictions = []
        
        for i in range(lookback, len(df) - 1):
            historical_df = df.iloc[max(0, i-lookback):i].copy()
            
            if len(historical_df) < 5:
                continue
            
            try:
                # Compute features
                features = compute_enhanced_features(historical_df)
                ticker_features.append(features)
                
                # Get next candle's actual direction
                actual_close_next = df['Close'].iloc[i + 1]
                actual_close_curr = df['Close'].iloc[i]
                price_change = actual_close_next - actual_close_curr
                actual_direction = 1 if price_change > 0 else 0
                
                # Get static prediction
                pred = enhanced_prediction_adaptive(features, optimizer=None, use_adaptive_weights=False)
                predicted_direction = 1 if pred['prediction'] == 'LONG' else 0
                
                ticker_predictions.append({
                    'predicted': predicted_direction,
                    'actual': actual_direction,
                    'correct': 1 if predicted_direction == actual_direction else 0,
                    'price_change': price_change,
                    'confidence': pred['confidence']
                })
                
            except Exception as e:
                continue
        
        print(f"Collected {len(ticker_features)} records for {ticker}")
        if ticker_predictions:
            accuracy = np.mean([p['correct'] for p in ticker_predictions]) * 100
            print(f"  Baseline accuracy: {accuracy:.2f}%")
        
        all_features.extend(ticker_features)
        all_predictions.extend(ticker_predictions)
    
    print(f"\nTotal training samples: {len(all_features)}")
    if all_predictions:
        baseline_accuracy = np.mean([p['correct'] for p in all_predictions]) * 100
        print(f"Overall baseline accuracy: {baseline_accuracy:.2f}%")
    
    return all_features, all_predictions


def main():
    parser = argparse.ArgumentParser(
        description="Train regime-adaptive weights on historical data"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "AMZN"],
        help="Tickers to train on"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Days of historical data"
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Path to save trained weights"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("REGIME-ADAPTIVE WEIGHTS - TRAINING PIPELINE")
    print("="*70)
    print(f"Tickers: {', '.join(args.tickers)}")
    print(f"Historical Period: {args.days} days")
    print("="*70)
    
    # Collect training data
    print("\nPHASE 1: DATA COLLECTION")
    print("-"*70)
    features_list, predictions_list = collect_training_data(
        args.tickers, 
        days=args.days,
        lookback=20
    )
    
    if not features_list or not predictions_list:
        print("\nNo training data collected. Exiting.")
        return
    
    # Train optimizer
    print("\nPHASE 2: WEIGHT OPTIMIZATION")
    print("-"*70)
    optimizer = RegimeAdaptiveWeights()
    optimizer.train(features_list, predictions_list)
    
    # Save weights
    if args.save:
        save_path = args.save
    else:
        os.makedirs('models', exist_ok=True)
        save_path = os.path.join(
            'models',
            f"regime_weights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        )
    
    optimizer.save_weights(save_path)
    print(f"\nWeights saved to: {save_path}")
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print("\nTo use the trained weights in predictions:")
    print("  1. Load weights: optimizer.load_weights('weights_file.pkl')")
    print("  2. Get weights: weights = optimizer.get_adaptive_weights(features)")
    print("  3. Use in prediction: enhanced_prediction_adaptive(features, optimizer, True)")


if __name__ == "__main__":
    main()
