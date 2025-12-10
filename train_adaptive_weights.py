"""Train adaptive weight optimizer on historical backtest data.

This script collects prediction history from multiple backtests, trains an ML model
to learn optimal indicator weights, and evaluates the model performance.
"""

import sys
import os
from typing import Dict, List, Tuple
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adaptive_weights import AdaptiveWeightOptimizer
from enhanced_predictor_adaptive import (
    fetch_4hour_data, compute_enhanced_features, 
    enhanced_prediction_adaptive, generate_trading_levels
)


def collect_backtest_data(ticker: str, 
                         days: int = 90,
                         lookback: int = 20) -> Tuple[pd.DataFrame, List[Dict]]:
    """Collect features and predictions over a period.
    
    Args:
        ticker: Stock ticker
        days: Days of historical data to use
        lookback: Number of days to lookback for training
    
    Returns:
        Tuple of (predictions_df, features_list)
    """
    print(f"\nCollecting training data for {ticker}...")
    
    try:
        df = fetch_4hour_data(ticker, days=days)
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None
    
    if len(df) < lookback + 1:
        print(f"Not enough data for {ticker} (need {lookback+1}, have {len(df)})")
        return None, None
    
    predictions_list = []
    features_list = []
    
    # Iterate through historical data
    for i in range(lookback, len(df) - 1):  # -1 to have next candle for target
        # Get historical window
        historical_df = df.iloc[max(0, i-lookback):i].copy()
        
        if len(historical_df) < 5:
            continue
        
        # Compute features
        try:
            features = compute_enhanced_features(historical_df)
            
            # Normalize features to 0-1 range for better ML performance
            features_normalized = {
                'slope_norm': (features['slope'] + 1) / 2 if features['slope'] != 0 else 0.5,
                'rsi_norm': features['rsi'] / 100,
                'adx_norm': min(features['adx'] / 50, 1.0),
                'bb_position': features['bb_position'],
                'atr_percent_norm': min(features['atr_percent'] / 5, 1.0),
                'volatility_norm': min(features['volatility'] / 10, 1.0),
                'k_stoch_norm': features['k_stoch'] / 100,
                'd_stoch_norm': features['d_stoch'] / 100,
                'macd_histogram_norm': np.tanh(features['macd_histogram']),  # Bounded [-1,1]
                'last_return_norm': np.tanh(features['last_return'] * 10),  # Bounded [-1,1]
            }
            features_list.append(features_normalized)
            
            # Get next candle's actual close for target
            actual_close_next = df['Close'].iloc[i + 1]
            actual_close_curr = df['Close'].iloc[i]
            
            # Determine actual direction
            price_change = actual_close_next - actual_close_curr
            actual_direction = 1 if price_change > 0 else 0  # 1=up, 0=down
            
            # Get prediction
            pred = enhanced_prediction_adaptive(features, optimizer=None, use_adaptive_weights=False)
            predicted_direction = 1 if pred['prediction'] == 'LONG' else 0
            
            # Check if correct
            correct = 1 if predicted_direction == actual_direction else 0
            
            predictions_list.append({
                'predicted': predicted_direction,
                'actual': actual_direction,
                'correct': correct,
                'price_change': price_change,
                'confidence': pred['confidence']
            })
            
        except Exception as e:
            continue
    
    predictions_df = pd.DataFrame(predictions_list)
    
    print(f"Collected {len(predictions_df)} prediction records for {ticker}")
    if len(predictions_df) > 0:
        accuracy = predictions_df['correct'].mean() * 100
        print(f"Baseline accuracy (static weights): {accuracy:.2f}%")
    
    return predictions_df, features_list


def train_optimizer(predictions_df: pd.DataFrame, 
                   features_list: List[Dict]) -> AdaptiveWeightOptimizer:
    """Train the adaptive weight optimizer.
    
    Args:
        predictions_df: DataFrame with prediction results
        features_list: List of feature dictionaries
    
    Returns:
        Trained AdaptiveWeightOptimizer
    """
    if len(features_list) == 0 or len(predictions_df) == 0:
        print("No data to train on")
        return None
    
    # Convert features to DataFrame
    features_df = pd.DataFrame(features_list)
    
    # Align lengths
    min_len = min(len(predictions_df), len(features_df))
    predictions_df = predictions_df.iloc[:min_len].reset_index(drop=True)
    features_df = features_df.iloc[:min_len].reset_index(drop=True)
    
    # Create optimizer
    optimizer = AdaptiveWeightOptimizer(model_type='random_forest')
    
    # Prepare training data
    X = features_df.copy()
    y = predictions_df['correct'].astype(int).values
    
    # Train
    print(f"\nTraining model on {len(X)} samples...")
    print(f"Target accuracy rate: {y.mean()*100:.2f}%")
    train_score, test_score = optimizer.train(X, y, test_size=0.25)
    
    print(f"Train R² Score: {train_score:.4f}")
    print(f"Test R² Score: {test_score:.4f}")
    
    return optimizer


def evaluate_adaptive_weights(ticker: str, 
                             optimizer: AdaptiveWeightOptimizer,
                             days: int = 30) -> Dict:
    """Evaluate adaptive weights on new data.
    
    Args:
        ticker: Stock ticker
        optimizer: Trained optimizer
        days: Days of test data
    
    Returns:
        Evaluation metrics
    """
    print(f"\nEvaluating adaptive weights on {ticker}...")
    
    try:
        df = fetch_4hour_data(ticker, days=days)
    except Exception as e:
        print(f"Error fetching test data: {e}")
        return None
    
    adaptive_correct = 0
    static_correct = 0
    total = 0
    
    lookback = 20
    
    for i in range(lookback, len(df)):
        historical_df = df.iloc[max(0, i-lookback):i].copy()
        
        if len(historical_df) < 5:
            continue
        
        try:
            features = compute_enhanced_features(historical_df)
            
            # Actual direction
            actual_close_next = df['Close'].iloc[i]
            actual_close_curr = df['Close'].iloc[i-1]
            price_change = actual_close_next - actual_close_curr
            actual_direction = 1 if price_change > 0 else 0
            
            # Adaptive prediction
            adaptive_pred = enhanced_prediction_adaptive(
                features, optimizer, use_adaptive_weights=True
            )
            adaptive_direction = 1 if adaptive_pred['prediction'] == 'LONG' else 0
            adaptive_correct += (1 if adaptive_direction == actual_direction else 0)
            
            # Static prediction
            static_pred = enhanced_prediction_adaptive(
                features, optimizer=None, use_adaptive_weights=False
            )
            static_direction = 1 if static_pred['prediction'] == 'LONG' else 0
            static_correct += (1 if static_direction == actual_direction else 0)
            
            total += 1
            
        except Exception as e:
            continue
    
    if total == 0:
        return None
    
    adaptive_accuracy = (adaptive_correct / total) * 100
    static_accuracy = (static_correct / total) * 100
    improvement = adaptive_accuracy - static_accuracy
    
    return {
        'ticker': ticker,
        'adaptive_accuracy': adaptive_accuracy,
        'static_accuracy': static_accuracy,
        'improvement': improvement,
        'test_samples': total
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train adaptive weight optimizer on historical data"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL"],
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
        help="Path to save trained model"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("ADAPTIVE WEIGHT OPTIMIZER - TRAINING")
    print("="*70)
    print(f"Tickers: {args.tickers}")
    print(f"Historical Data: {args.days} days")
    print("="*70)
    
    # Collect training data from all tickers
    all_predictions = []
    all_features = []
    
    for ticker in args.tickers:
        predictions_df, features_list = collect_backtest_data(ticker, days=args.days)
        
        if predictions_df is not None and len(predictions_df) > 0:
            all_predictions.append(predictions_df)
            all_features.extend(features_list)
    
    if not all_predictions:
        print("\nNo training data collected. Exiting.")
        return
    
    # Combine all data
    combined_predictions = pd.concat(all_predictions, ignore_index=True)
    
    print(f"\nTotal training samples: {len(combined_predictions)}")
    print(f"Overall baseline accuracy: {combined_predictions['correct'].mean()*100:.2f}%")
    
    # Train optimizer
    optimizer = train_optimizer(combined_predictions, all_features)
    
    if optimizer is None:
        print("Failed to train optimizer")
        return
    
    # Evaluate on new data
    print("\n" + "="*70)
    print("EVALUATION ON TEST DATA")
    print("="*70)
    
    results = []
    for ticker in args.tickers:
        result = evaluate_adaptive_weights(ticker, optimizer, days=30)
        if result:
            results.append(result)
            print(f"\n{ticker}:")
            print(f"  Static Accuracy:   {result['static_accuracy']:.2f}%")
            print(f"  Adaptive Accuracy: {result['adaptive_accuracy']:.2f}%")
            print(f"  Improvement:       {result['improvement']:+.2f}%")
            print(f"  Test Samples:      {result['test_samples']}")
    
    # Summary
    if results:
        avg_improvement = np.mean([r['improvement'] for r in results])
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Average Improvement: {avg_improvement:+.2f}%")
        
        # Determine if improvement is significant
        if avg_improvement > 2.0:
            print("✓ SIGNIFICANT IMPROVEMENT - Ready to deploy adaptive weights")
        elif avg_improvement > 0:
            print("✓ MODEST IMPROVEMENT - Consider deploying with monitoring")
        else:
            print("✗ NO IMPROVEMENT - May need more training data or parameter tuning")
    
    # Save model
    if args.save:
        optimizer.save_model(args.save)
        print(f"\nModel saved to: {args.save}")
    else:
        # Default save location
        default_path = os.path.join(
            os.path.dirname(__file__),
            'models',
            f"adaptive_weights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        )
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        optimizer.save_model(default_path)
        print(f"\nModel saved to: {default_path}")


if __name__ == "__main__":
    main()
