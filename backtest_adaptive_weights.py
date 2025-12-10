"""Comprehensive backtest comparing adaptive vs static weights strategy performance.

This script runs a full backtest on historical data using both adaptive and
static weights to quantify the improvement in returns and win rate.
"""

import sys
import os
from typing import Dict, List, Tuple
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from regime_weights import RegimeAdaptiveWeights
from enhanced_predictor_adaptive import (
    fetch_4hour_data, compute_enhanced_features, 
    enhanced_prediction_adaptive, generate_trading_levels
)


def backtest_strategy(ticker: str,
                      optimizer: RegimeAdaptiveWeights = None,
                      use_adaptive: bool = False,
                      days: int = 90,
                      lookback: int = 20) -> Dict:
    """Run backtest on a ticker.
    
    Args:
        ticker: Stock ticker
        optimizer: RegimeAdaptiveWeights optimizer (for adaptive)
        use_adaptive: Whether to use adaptive weights
        days: Days of data
        lookback: Lookback period
    
    Returns:
        Backtest results dictionary
    """
    try:
        df = fetch_4hour_data(ticker, days=days)
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None
    
    if len(df) < lookback + 1:
        return None
    
    # Backtest metrics
    trades = []
    correct = 0
    incorrect = 0
    total_return = 0
    entry_price = None
    position = None  # 'long', 'short', or None
    
    for i in range(lookback, len(df) - 1):
        historical_df = df.iloc[max(0, i-lookback):i].copy()
        
        if len(historical_df) < 5:
            continue
        
        try:
            features = compute_enhanced_features(historical_df)
            current_price = df['Close'].iloc[i]
            
            # Get prediction
            pred = enhanced_prediction_adaptive(
                features, optimizer, use_adaptive_weights=use_adaptive
            )
            
            predicted_signal = pred['prediction']
            confidence = pred['confidence']
            
            # Simple trading logic
            atr = features.get('atr', current_price * 0.01)
            levels = generate_trading_levels(current_price, atr)
            
            # Next price
            next_price = df['Close'].iloc[i + 1]
            actual_direction = 'LONG' if next_price > current_price else 'SHORT'
            
            # Check if prediction was correct
            if predicted_signal == actual_direction:
                correct += 1
            else:
                incorrect += 1
            
            # Calculate return if we took the trade
            if predicted_signal == 'LONG':
                entry = current_price
                exit_price = next_price
                trade_return = (exit_price - entry) / entry
            else:
                entry = current_price
                exit_price = next_price
                trade_return = (entry - exit_price) / entry
            
            trades.append({
                'entry': entry if predicted_signal == 'LONG' else current_price,
                'exit': exit_price,
                'signal': predicted_signal,
                'actual': actual_direction,
                'correct': predicted_signal == actual_direction,
                'return': trade_return,
                'confidence': confidence
            })
            
            total_return += trade_return
            
        except Exception:
            continue
    
    if not trades:
        return None
    
    # Calculate metrics
    df_trades = pd.DataFrame(trades)
    
    accuracy = correct / (correct + incorrect) * 100 if (correct + incorrect) > 0 else 0
    win_count = len(df_trades[df_trades['correct'] == True])
    win_rate = (win_count / len(trades)) * 100 if len(trades) > 0 else 0
    
    profitable_trades = df_trades[df_trades['return'] > 0]
    losing_trades = df_trades[df_trades['return'] <= 0]
    
    avg_win = profitable_trades['return'].mean() * 100 if len(profitable_trades) > 0 else 0
    avg_loss = losing_trades['return'].mean() * 100 if len(losing_trades) > 0 else 0
    
    profit_factor = (profitable_trades['return'].sum() / abs(losing_trades['return'].sum())) if len(losing_trades) > 0 and losing_trades['return'].sum() != 0 else 0
    
    return {
        'ticker': ticker,
        'accuracy': accuracy,
        'win_rate': win_rate,
        'total_return': total_return * 100,
        'num_trades': len(trades),
        'winning_trades': win_count,
        'losing_trades': len(trades) - win_count,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'trades_df': df_trades
    }


def main():
    parser = argparse.ArgumentParser(
        description="Backtest adaptive vs static weights"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL"],
        help="Tickers to backtest"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Days of backtest data"
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Path to saved weights"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("ADAPTIVE vs STATIC WEIGHTS - COMPREHENSIVE BACKTEST")
    print("="*80)
    print(f"Tickers: {', '.join(args.tickers)}")
    print(f"Period: {args.days} days")
    print("="*80)
    
    # Load optimizer
    optimizer = RegimeAdaptiveWeights()
    if args.weights and os.path.exists(args.weights):
        print(f"Loading weights: {args.weights}\n")
        optimizer.load_weights(args.weights)
    else:
        print("Using default adaptive weights\n")
        optimizer.regime_weights = {
            'trending_strong': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.35, 
                               'trend_strength': 0.15, 'stochastic': 0.15},
            'trending_weak': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.35,
                             'trend_strength': 0.15, 'stochastic': 0.15},
            'ranging': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.20,
                       'trend_strength': 0.20, 'stochastic': 0.15},
            'ranging_high': {'trend': 0.20, 'momentum': 0.25, 'volatility': 0.35,
                            'trend_strength': 0.15, 'stochastic': 0.15}
        }
        optimizer.is_trained = True
    
    # Run backtests
    static_results = []
    adaptive_results = []
    
    print("Running backtests...")
    print("-"*80)
    
    for ticker in args.tickers:
        static = backtest_strategy(ticker, optimizer=None, use_adaptive=False, days=args.days)
        adaptive = backtest_strategy(ticker, optimizer=optimizer, use_adaptive=True, days=args.days)
        
        if static and adaptive:
            static_results.append(static)
            adaptive_results.append(adaptive)
            
            print(f"\n{ticker}:")
            print(f"  {'Metric':<20} {'Static':<15} {'Adaptive':<15} {'Improvement':<15}")
            print(f"  {'-'*65}")
            print(f"  {'Accuracy':<20} {static['accuracy']:>6.2f}%        {adaptive['accuracy']:>6.2f}%        {adaptive['accuracy']-static['accuracy']:>+6.2f}%")
            print(f"  {'Win Rate':<20} {static['win_rate']:>6.2f}%        {adaptive['win_rate']:>6.2f}%        {adaptive['win_rate']-static['win_rate']:>+6.2f}%")
            print(f"  {'Total Return':<20} {static['total_return']:>6.2f}%        {adaptive['total_return']:>6.2f}%        {adaptive['total_return']-static['total_return']:>+6.2f}%")
            print(f"  {'Trades':<20} {static['num_trades']:>6d}          {adaptive['num_trades']:>6d}          {adaptive['num_trades']-static['num_trades']:>+6d}")
            print(f"  {'Profit Factor':<20} {static['profit_factor']:>6.2f}          {adaptive['profit_factor']:>6.2f}          {adaptive['profit_factor']-static['profit_factor']:>+6.2f}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if static_results and adaptive_results:
        static_df = pd.DataFrame(static_results)
        adaptive_df = pd.DataFrame(adaptive_results)
        
        print("\nAverage Metrics Across All Tickers:")
        print("-"*80)
        print(f"  {'Metric':<20} {'Static':<15} {'Adaptive':<15} {'Improvement':<15}")
        print(f"  {'-'*65}")
        
        avg_static_acc = static_df['accuracy'].mean()
        avg_adaptive_acc = adaptive_df['accuracy'].mean()
        print(f"  {'Accuracy':<20} {avg_static_acc:>6.2f}%        {avg_adaptive_acc:>6.2f}%        {avg_adaptive_acc-avg_static_acc:>+6.2f}%")
        
        avg_static_wr = static_df['win_rate'].mean()
        avg_adaptive_wr = adaptive_df['win_rate'].mean()
        print(f"  {'Win Rate':<20} {avg_static_wr:>6.2f}%        {avg_adaptive_wr:>6.2f}%        {avg_adaptive_wr-avg_static_wr:>+6.2f}%")
        
        avg_static_ret = static_df['total_return'].mean()
        avg_adaptive_ret = adaptive_df['total_return'].mean()
        print(f"  {'Total Return':<20} {avg_static_ret:>6.2f}%        {avg_adaptive_ret:>6.2f}%        {avg_adaptive_ret-avg_static_ret:>+6.2f}%")
        
        avg_static_pf = static_df['profit_factor'].mean()
        avg_adaptive_pf = adaptive_df['profit_factor'].mean()
        print(f"  {'Profit Factor':<20} {avg_static_pf:>6.2f}          {avg_adaptive_pf:>6.2f}          {avg_adaptive_pf-avg_static_pf:>+6.2f}")
        
        # Recommendation
        print("\n" + "="*80)
        if avg_adaptive_acc > avg_static_acc and avg_adaptive_ret > avg_static_ret:
            print("✓ ADAPTIVE WEIGHTS OUTPERFORM - RECOMMENDED FOR DEPLOYMENT")
            print(f"  - Accuracy improvement: {avg_adaptive_acc-avg_static_acc:+.2f}%")
            print(f"  - Return improvement: {avg_adaptive_ret-avg_static_ret:+.2f}%")
        elif avg_adaptive_acc > avg_static_acc:
            print("⚠ MIXED RESULTS - MODEST IMPROVEMENT IN ACCURACY")
            print(f"  - Accuracy: {avg_adaptive_acc-avg_static_acc:+.2f}%")
            print(f"  - Returns: {avg_adaptive_ret-avg_static_ret:+.2f}%")
        else:
            print("✗ NO CLEAR ADVANTAGE - CONTINUE WITH STATIC WEIGHTS")


if __name__ == "__main__":
    main()
