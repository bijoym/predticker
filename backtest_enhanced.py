"""Backtest the enhanced predictor strategy."""

import pandas as pd
import numpy as np
from src.enhanced_predictor import (
    fetch_4hour_data, compute_enhanced_features, enhanced_prediction,
    generate_trading_levels
)


def backtest_enhanced(ticker: str, days: int = 60, initial_capital: float = 10000):
    """Backtest enhanced predictor."""
    print(f"\n{'='*70}")
    print(f"ENHANCED BACKTEST: {ticker}")
    print(f"{'='*70}")
    
    try:
        df = fetch_4hour_data(ticker, days=days)
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    trades = []
    predictions = []
    equity = initial_capital
    position = None
    entry_price = 0
    
    window_size = 5
    
    for i in range(window_size, len(df)):
        df_window = df.iloc[i-window_size:i]
        features = compute_enhanced_features(df_window)
        result = enhanced_prediction(features)
        
        current_price = df.iloc[i]["Close"]
        current_time = df.index[i]
        
        # Track predictions
        if i + 1 < len(df):
            next_price = df.iloc[i + 1]["Close"]
            actual_direction = "Up" if next_price > current_price else "Down"
            was_correct = result["prediction"] == actual_direction
            
            predictions.append({
                "time": current_time,
                "predicted": result["prediction"],
                "actual": actual_direction,
                "correct": was_correct,
                "confidence": result["confidence"]
            })
        
        # Trading logic
        if position is None and result["confidence"] > 20:  # Lowered confidence filter
            levels = generate_trading_levels(
                current_price, result["prediction"],
                features["atr"], features
            )
            
            if result["prediction"] == "Up":
                position = "LONG"
                entry_price = current_price
                stop_loss = levels["stop_loss"]
                take_profit = levels["take_profit"]
                
            else:
                position = "SHORT"
                entry_price = current_price
                stop_loss = levels["stop_loss"]
                take_profit = levels["take_profit"]
        
        # Check exits
        if position == "LONG":
            if current_price <= stop_loss:
                pnl = current_price - entry_price
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "LONG",
                    "PnL": pnl,
                    "Reason": "Stop Loss"
                })
                position = None
                
            elif current_price >= take_profit:
                pnl = current_price - entry_price
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "LONG",
                    "PnL": pnl,
                    "Reason": "Take Profit"
                })
                position = None
        
        elif position == "SHORT":
            if current_price >= stop_loss:
                pnl = entry_price - current_price
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "SHORT",
                    "PnL": pnl,
                    "Reason": "Stop Loss"
                })
                position = None
                
            elif current_price <= take_profit:
                pnl = entry_price - current_price
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "SHORT",
                    "PnL": pnl,
                    "Reason": "Take Profit"
                })
                position = None
    
    # Calculate metrics
    if len(trades) == 0:
        print(f"No trades for {ticker}")
        return None
    
    total_return = ((equity - initial_capital) / initial_capital) * 100
    wins = len([t for t in trades if t["PnL"] > 0])
    losses = len([t for t in trades if t["PnL"] <= 0])
    win_rate = (wins / len(trades)) * 100 if len(trades) > 0 else 0
    
    if len(predictions) > 0:
        predictions_df = pd.DataFrame(predictions)
        correct = len(predictions_df[predictions_df["correct"] == True])
        pred_accuracy = (correct / len(predictions_df)) * 100
    else:
        pred_accuracy = 0
    
    print(f"\nResults:")
    print(f"  Initial Capital: ${initial_capital:,.2f}")
    print(f"  Final Equity: ${equity:,.2f}")
    print(f"  Total Return: {total_return:+.2f}%")
    print(f"\n  Total Trades: {len(trades)}")
    print(f"  Wins: {wins} | Losses: {losses}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Prediction Accuracy: {pred_accuracy:.1f}%")
    
    return {
        "ticker": ticker,
        "return": total_return,
        "trades": len(trades),
        "win_rate": win_rate,
        "accuracy": pred_accuracy,
        "equity": equity
    }


if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    results = []
    
    print("=" * 70)
    print("ENHANCED PREDICTOR BACKTEST")
    print("=" * 70)
    
    for ticker in tickers:
        result = backtest_enhanced(ticker, days=60, initial_capital=10000)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    
    for r in results:
        status = "✓" if r["return"] > 0 else "✗"
        print(f"{status} {r['ticker']:6} | Return: {r['return']:+7.2f}% | "
              f"Trades: {r['trades']:2} | Win Rate: {r['win_rate']:5.1f}% | "
              f"Accuracy: {r['accuracy']:5.1f}%")
    
    avg_return = np.mean([r["return"] for r in results])
    avg_accuracy = np.mean([r["accuracy"] for r in results])
    print(f"\nAverage Return: {avg_return:+.2f}%")
    print(f"Average Accuracy: {avg_accuracy:.1f}%")
