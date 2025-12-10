"""Backtesting module for the market predictor.

This module backtests the predictor on historical data to evaluate performance.
It simulates trades based on predictions and calculates key metrics.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


def _normalize_timezone(df: pd.DataFrame) -> pd.DataFrame:
    """Convert timezone-aware index to timezone-naive."""
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df = df.tz_convert(None)
    return df


def _compute_slope(prices: np.ndarray) -> float:
    """Compute linear regression slope of prices."""
    if len(prices) < 2:
        return 0.0
    times = np.arange(len(prices)).reshape(-1, 1)
    lr = LinearRegression()
    lr.fit(times, prices)
    return float(lr.coef_[0])


def fetch_historical_4h(ticker: str, days: int = 60) -> pd.DataFrame:
    """Fetch historical 4-hour data.
    
    Args:
        ticker: Ticker symbol
        days: Number of days of historical data (default 60)
    
    Returns:
        DataFrame with 4-hour OHLCV data
    """
    t = yf.Ticker(ticker)
    df = t.history(period=f"{days}d", interval="4h", actions=False)
    if df.empty:
        raise RuntimeError(f"No data available for {ticker}")
    return _normalize_timezone(df)


def compute_4h_features(df_4h: pd.DataFrame) -> Dict[str, float]:
    """Compute features for 4-hour timeframe analysis.
    
    Args:
        df_4h: DataFrame with 4-hour OHLCV data
    
    Returns:
        Dict with slope, last_return, volatility, avg_volatility
    """
    prices = df_4h["Close"].values
    slope = _compute_slope(prices)
    last_return = (prices[-1] / prices[0] - 1.0) if len(prices) >= 2 else 0.0
    volatility = float(df_4h["Close"].std())
    avg_volatility = float(df_4h["Close"].rolling(window=2).std().mean())
    return {"slope": slope, "last_return": last_return, "volatility": volatility, "avg_volatility": avg_volatility}


def rule_based_prediction_4h(features_4h: Dict) -> Tuple[str, int]:
    """Generate prediction based on 4-hour timeframe analysis.
    
    Args:
        features_4h: Dict with slope, last_return, volatility, avg_volatility
    
    Returns:
        Tuple of (prediction, score)
    """
    score = 0
    if features_4h["slope"] > 0:
        score += 1
    if features_4h["last_return"] > 0:
        score += 1
    if features_4h["volatility"] < features_4h["avg_volatility"]:
        score += 1

    prediction = "Up" if score >= 2 else "Down"
    return prediction, score


def backtest_ticker(ticker: str, days: int = 60, initial_capital: float = 10000):
    """Backtest the predictor on historical data for a ticker."""
    print(f"\n{'='*70}")
    print(f"BACKTESTING {ticker}")
    print(f"{'='*70}")
    
    try:
        df = fetch_historical_4h(ticker, days=days)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    
    trades = []
    equity = initial_capital
    position = None
    entry_price = 0
    predictions = []  # Track all predictions and their outcomes
    
    # Backtest on rolling window
    window_size = 5  # Use last 5 periods for prediction
    
    for i in range(window_size, len(df)):
        # Get features from last window_size periods
        df_window = df.iloc[i-window_size:i]
        features = compute_4h_features(df_window)
        prediction, score = rule_based_prediction_4h(features)
        
        current_price = df.iloc[i]["Close"]
        current_time = df.index[i]
        
        # Calculate actual next candle movement for accuracy check
        if i + 1 < len(df):
            next_price = df.iloc[i + 1]["Close"]
            actual_direction = "Up" if next_price > current_price else "Down"
            price_change = ((next_price - current_price) / current_price) * 100
            was_correct = prediction == actual_direction
            
            predictions.append({
                "time": current_time,
                "predicted": prediction,
                "actual": actual_direction,
                "correct": was_correct,
                "price_change": price_change
            })
        
        # Generate entry signals
        if position is None and prediction == "Up":
            # Open LONG position
            position = "LONG"
            entry_price = current_price
            stop_loss = current_price * 0.98  # -2%
            take_profit = current_price * 1.04  # +4%
            
        elif position is None and prediction == "Down":
            # Open SHORT position
            position = "SHORT"
            entry_price = current_price
            stop_loss = current_price * 1.05  # +5%
            take_profit = current_price * 0.95  # -5%
        
        # Check for exit conditions
        if position == "LONG":
            if current_price <= stop_loss:
                # Stop loss hit
                pnl = current_price - entry_price
                pnl_pct = (pnl / entry_price) * 100
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "LONG",
                    "PnL": pnl,
                    "PnL%": pnl_pct,
                    "Reason": "Stop Loss",
                    "Date": current_time
                })
                position = None
                
            elif current_price >= take_profit:
                # Take profit hit
                pnl = current_price - entry_price
                pnl_pct = (pnl / entry_price) * 100
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "LONG",
                    "PnL": pnl,
                    "PnL%": pnl_pct,
                    "Reason": "Take Profit",
                    "Date": current_time
                })
                position = None
        
        elif position == "SHORT":
            if current_price >= stop_loss:
                # Stop loss hit
                pnl = entry_price - current_price
                pnl_pct = (pnl / entry_price) * 100
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "SHORT",
                    "PnL": pnl,
                    "PnL%": pnl_pct,
                    "Reason": "Stop Loss",
                    "Date": current_time
                })
                position = None
                
            elif current_price <= take_profit:
                # Take profit hit
                pnl = entry_price - current_price
                pnl_pct = (pnl / entry_price) * 100
                equity += pnl
                trades.append({
                    "Entry": entry_price,
                    "Exit": current_price,
                    "Type": "SHORT",
                    "PnL": pnl,
                    "PnL%": pnl_pct,
                    "Reason": "Take Profit",
                    "Date": current_time
                })
                position = None
    
    # Close any open position at end
    if position is not None:
        final_price = df.iloc[-1]["Close"]
        if position == "LONG":
            pnl = final_price - entry_price
        else:
            pnl = entry_price - final_price
        pnl_pct = (pnl / entry_price) * 100
        equity += pnl
        trades.append({
            "Entry": entry_price,
            "Exit": final_price,
            "Type": position,
            "PnL": pnl,
            "PnL%": pnl_pct,
            "Reason": "End of Period",
            "Date": df.index[-1]
        })
    
    # Calculate metrics
    if len(trades) == 0:
        print(f"No trades executed for {ticker}")
        return None
    
    trades_df = pd.DataFrame(trades)
    
    total_return = ((equity - initial_capital) / initial_capital) * 100
    winning_trades = len(trades_df[trades_df["PnL"] > 0])
    losing_trades = len(trades_df[trades_df["PnL"] <= 0])
    win_rate = (winning_trades / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    
    avg_win = trades_df[trades_df["PnL"] > 0]["PnL"].mean() if winning_trades > 0 else 0
    avg_loss = trades_df[trades_df["PnL"] <= 0]["PnL"].mean() if losing_trades > 0 else 0
    
    profit_factor = abs(trades_df[trades_df["PnL"] > 0]["PnL"].sum()) / abs(trades_df[trades_df["PnL"] <= 0]["PnL"].sum()) if losing_trades > 0 else float('inf')
    
    # Calculate prediction accuracy
    if len(predictions) > 0:
        predictions_df = pd.DataFrame(predictions)
        correct_predictions = len(predictions_df[predictions_df["correct"] == True])
        prediction_accuracy = (correct_predictions / len(predictions_df)) * 100
        avg_move = predictions_df["price_change"].abs().mean()
        correct_move = predictions_df[predictions_df["correct"] == True]["price_change"].mean()
    else:
        prediction_accuracy = 0
        avg_move = 0
        correct_move = 0
    
    print(f"\nTicker: {ticker}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Final Equity: ${equity:,.2f}")
    print(f"Total Return: {total_return:,.2f}%")
    print(f"\nPrediction Accuracy:")
    print(f"Prediction Accuracy: {prediction_accuracy:.2f}%")
    print(f"Correct Predictions: {correct_predictions}/{len(predictions_df)}")
    print(f"Average Price Move: {avg_move:.4f}%")
    print(f"Avg Move on Correct Predictions: {correct_move:.4f}%")
    print(f"\nTrade Statistics:")
    print(f"Total Trades: {len(trades_df)}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Losing Trades: {losing_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Average Win: ${avg_win:,.2f}")
    print(f"Average Loss: ${avg_loss:,.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"\nTrades:")
    print(trades_df.to_string(index=False))
    
    return {
        "ticker": ticker,
        "initial_capital": initial_capital,
        "final_equity": equity,
        "total_return": total_return,
        "trades": len(trades_df),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "prediction_accuracy": prediction_accuracy,
        "correct_predictions": correct_predictions,
        "total_predictions": len(predictions_df) if len(predictions) > 0 else 0,
        "trades_df": trades_df,
        "predictions_df": predictions_df if len(predictions) > 0 else None
    }


def backtest_multiple_tickers(tickers: list, days: int = 60, initial_capital: float = 10000):
    """Backtest multiple tickers and compare results."""
    results = []
    
    print(f"\n{'='*70}")
    print(f"BACKTESTING MULTIPLE TICKERS")
    print(f"{'='*70}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Period: {days} days")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    
    for ticker in tickers:
        result = backtest_ticker(ticker, days=days, initial_capital=initial_capital)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print("BACKTEST SUMMARY")
    print(f"{'='*70}")
    
    summary_data = []
    for r in results:
        summary_data.append({
            "Ticker": r["ticker"],
            "Pred Acc %": f"{r['prediction_accuracy']:.2f}%",
            "Return %": f"{r['total_return']:.2f}%",
            "Trades": r["trades"],
            "Win Rate %": f"{r['win_rate']:.2f}%",
            "Profit Factor": f"{r['profit_factor']:.2f}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    # Plot results
    if len(results) > 0:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Return by ticker
        tickers_list = [r["ticker"] for r in results]
        returns = [r["total_return"] for r in results]
        colors = ["green" if x > 0 else "red" for x in returns]
        axes[0, 0].bar(tickers_list, returns, color=colors, alpha=0.7)
        axes[0, 0].set_title("Total Return by Ticker (%)", fontweight="bold")
        axes[0, 0].set_ylabel("Return %")
        axes[0, 0].axhline(0, color="black", linestyle="-", linewidth=0.5)
        axes[0, 0].grid(True, alpha=0.3)
        
        # Win rate by ticker
        win_rates = [r["win_rate"] for r in results]
        axes[0, 1].bar(tickers_list, win_rates, color="skyblue", alpha=0.7)
        axes[0, 1].set_title("Win Rate by Ticker (%)", fontweight="bold")
        axes[0, 1].set_ylabel("Win Rate %")
        axes[0, 1].axhline(50, color="orange", linestyle="--", linewidth=1)
        axes[0, 1].grid(True, alpha=0.3)
        
        # Profit factor by ticker
        profit_factors = [min(r["profit_factor"], 5) for r in results]  # Cap at 5 for display
        axes[1, 0].bar(tickers_list, profit_factors, color="purple", alpha=0.7)
        axes[1, 0].set_title("Profit Factor by Ticker", fontweight="bold")
        axes[1, 0].set_ylabel("Profit Factor")
        axes[1, 0].axhline(1, color="orange", linestyle="--", linewidth=1)
        axes[1, 0].grid(True, alpha=0.3)
        
        # Number of trades by ticker
        num_trades = [r["trades"] for r in results]
        axes[1, 1].bar(tickers_list, num_trades, color="teal", alpha=0.7)
        axes[1, 1].set_title("Number of Trades by Ticker", fontweight="bold")
        axes[1, 1].set_ylabel("Trades")
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig("backtest_results.png", dpi=150)
        print(f"\nBacktest chart saved to backtest_results.png")
        plt.show()
    
    return results


if __name__ == "__main__":
    # Test tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    # Run backtest
    results = backtest_multiple_tickers(tickers, days=60, initial_capital=10000)
