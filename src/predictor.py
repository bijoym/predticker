"""Simple share movement predictor and plotter.

Usage: python -m src.predictor --ticker AAPL

This script fetches intraday 1-minute data for the last day, takes the last 20
minutes (or fewer if not available), computes simple features including 20d and
50d SMAs, applies a rule-based prediction, and plots the recent price with
stop-loss and take-profit levels.
"""

import argparse
import sys
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression


def fetch_intraday(ticker: str, minutes: int = 20) -> tuple:
    """Fetch intraday data and return both extended and recent windows."""
    t = yf.Ticker(ticker)
    # Try to get 1m data for today (yfinance offers limited intraday window)
    df = t.history(period="1d", interval="1m", actions=False)
    if df.empty:
        raise RuntimeError("No intraday data available for ticker: %s" % ticker)
    # Ensure index is timezone-naive for plotting convenience
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.tz_convert(None) if df.index.tz is not None else df
    
    # Get last 4 hours + 20 mins for chart display
    extended_window = max(280, len(df))  # 4 hours 20 mins = 260 minutes, plus buffer
    df_extended = df.tail(extended_window)
    
    # Get last 20 minutes for analysis
    df_recent = df.tail(minutes)
    
    # Calculate day's high and low
    day_high = float(df["High"].max())
    day_low = float(df["Low"].min())
    
    return df_recent, df_extended, day_high, day_low


def fetch_4hour(ticker: str, days: int = 5) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    # Get 4-hour data for the last few days
    df = t.history(period=f"{days}d", interval="4h", actions=False)
    if df.empty:
        raise RuntimeError("No 4-hour data available for ticker: %s" % ticker)
    # Ensure index is timezone-naive
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.tz_convert(None) if df.index.tz is not None else df
    return df


def fetch_daily(ticker: str, days: int = 120) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(period=f"{days}d", interval="1d", actions=False)
    if df.empty:
        raise RuntimeError("No daily data available for ticker: %s" % ticker)
    return df


def compute_sma(df_daily: pd.DataFrame):
    close = df_daily["Close"]
    sma20 = close.rolling(window=20).mean().iloc[-1]
    sma50 = close.rolling(window=50).mean().iloc[-1]
    return float(sma20), float(sma50)


def compute_intraday_features(df_min: pd.DataFrame):
    prices = df_min["Close"].values
    times = np.arange(len(prices)).reshape(-1, 1)
    lr = LinearRegression()
    if len(prices) >= 2:
        lr.fit(times, prices)
        slope = float(lr.coef_[0])
    else:
        slope = 0.0
    last_return = (prices[-1] / prices[0] - 1.0) if len(prices) >= 2 else 0.0
    avg_volume = float(df_min["Volume"].mean()) if "Volume" in df_min.columns else 0.0
    return {"slope": slope, "last_return": last_return, "avg_volume": avg_volume}


def compute_4h_features(df_4h: pd.DataFrame):
    """Compute features for 4-hour timeframe analysis."""
    prices = df_4h["Close"].values
    times = np.arange(len(prices)).reshape(-1, 1)
    lr = LinearRegression()
    if len(prices) >= 2:
        lr.fit(times, prices)
        slope = float(lr.coef_[0])
    else:
        slope = 0.0
    last_return = (prices[-1] / prices[0] - 1.0) if len(prices) >= 2 else 0.0
    volatility = float(df_4h["Close"].std())
    avg_volatility = float(df_4h["Close"].rolling(window=2).std().mean())
    return {"slope": slope, "last_return": last_return, "volatility": volatility, "avg_volatility": avg_volatility}


def rule_based_prediction(features: dict, sma20: float, sma50: float, current_price: float):
    score = 0
    reasons = []
    if sma20 > sma50:
        score += 1
        reasons.append("20d SMA > 50d SMA (bullish)")
    else:
        reasons.append("20d SMA <= 50d SMA (bearish)")
    if features["last_return"] > 0:
        score += 1
        reasons.append("positive last 20-min return")
    else:
        reasons.append("non-positive last 20-min return")
    if features["slope"] > 0:
        score += 1
        reasons.append("upward intraday slope")
    else:
        reasons.append("non-positive intraday slope")

    prediction = "Up" if score >= 2 else "Down"

    stop_loss = current_price * (1 - 0.05)
    take_profit = current_price * (1 + 0.10)

    return {"prediction": prediction, "score": score, "reasons": reasons, "stop_loss": stop_loss, "take_profit": take_profit}


def rule_based_prediction_4h(features_4h: dict, current_price: float):
    """Generate prediction based on 4-hour timeframe analysis."""
    score = 0
    reasons = []
    if features_4h["slope"] > 0:
        score += 1
        reasons.append("upward 4h slope (bullish)")
    else:
        reasons.append("non-positive 4h slope (bearish)")
    if features_4h["last_return"] > 0:
        score += 1
        reasons.append("positive 4h return")
    else:
        reasons.append("non-positive 4h return")
    if features_4h["volatility"] < features_4h["avg_volatility"]:
        score += 1
        reasons.append("low volatility (consolidation)")
    else:
        reasons.append("high volatility (breakout risk)")

    prediction = "Up" if score >= 2 else "Down"

    # Day trading strategy: 
    # For Up (Long): 2% stop-loss below, 4% take-profit above
    # For Down (Short): 5% stop-loss above, 5% take-profit below
    if prediction == "Up":
        stop_loss_4h = current_price * (1 - 0.02)
        take_profit_4h = current_price * (1 + 0.04)
    else:
        stop_loss_4h = current_price * (1 + 0.05)  # Above price for short (-5%)
        take_profit_4h = current_price * (1 - 0.05)  # Below price for short (+5%)

    return {"prediction": prediction, "score": score, "reasons": reasons, "stop_loss": stop_loss_4h, "take_profit": take_profit_4h}


def plot_intraday(df_min: pd.DataFrame, df_extended: pd.DataFrame, ticker: str, stop: float, take: float, prediction: str, day_high: float, day_low: float):
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.grid(True, alpha=0.3)
    
    # Plot full extended price (last 4 hours 20 mins)
    ax.plot(df_extended.index, df_extended["Close"], label="Price (Last 4h 20m)", color="tab:blue", linewidth=2, marker="o", markersize=3, alpha=0.7)
    
    # Highlight recent 20 minutes in bold
    ax.plot(df_min.index, df_min["Close"], label="Price (Last 20m - Analysis)", color="darkblue", linewidth=3, marker="o", markersize=5)
    
    # Calculate trend for next 10 minutes
    prices = df_min["Close"].values
    times = np.arange(len(prices)).reshape(-1, 1)
    lr = LinearRegression()
    lr.fit(times, prices)
    
    # Project next 10 candles
    future_times = np.arange(len(prices), len(prices) + 10).reshape(-1, 1)
    future_prices = lr.predict(future_times)
    
    # Create future index (assuming 1-minute intervals)
    last_time = df_min.index[-1]
    future_index = pd.date_range(start=last_time + pd.Timedelta(minutes=1), periods=10, freq='1min')
    
    # Plot projection with color based on prediction
    projection_color = (0.2, 0.8, 0.2) if prediction == "Up" else (0.8, 0.2, 0.2)
    ax.plot(future_index, future_prices, label="10-min Projection", color=projection_color, linewidth=2.5, linestyle="--", marker="s", markersize=6, alpha=0.8)
    
    # Mark current price
    ax.scatter(df_min.index[-1], df_min["Close"].iloc[-1], color="darkblue", s=150, zorder=5, label="Current Price", edgecolors="black", linewidth=2)
    
    # Mark projected endpoint
    ax.scatter(future_index[-1], future_prices[-1], color=projection_color, s=200, marker="*", zorder=6, label=f"Projected 10-min ({prediction})", edgecolors="black", linewidth=1.5)
    
    # Add day's high and low lines
    ax.axhline(day_high, color="green", linestyle=":", linewidth=2, label=f"Day High: ${day_high:.2f}", alpha=0.7)
    ax.axhline(day_low, color="red", linestyle=":", linewidth=2, label=f"Day Low: ${day_low:.2f}", alpha=0.7)
    
    # Add stop-loss and take-profit lines
    ax.axhline(stop, color="darkred", linestyle="--", linewidth=1.5, label=f"Stop-loss (5%): ${stop:.2f}")
    ax.axhline(take, color="darkgreen", linestyle="--", linewidth=1.5, label=f"Take-profit (10%): ${take:.2f}")
    
    # Add shaded regions for buy/sell zones
    if prediction == "Up":
        ax.fill_between(df_extended.index, df_extended["Close"].min() - 10, df_extended["Close"].max() + 10, alpha=0.02, color="green")
    else:
        ax.fill_between(df_extended.index, df_extended["Close"].min() - 10, df_extended["Close"].max() + 10, alpha=0.02, color="red")
    
    ax.set_title(f"{ticker} — Last 4h 20m + 10-min Projection — Prediction: {prediction}", fontsize=15, fontweight="bold")
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Price ($)", fontsize=12)
    ax.legend(loc="best", fontsize=9, ncol=2)
    
    # Format x-axis nicely
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    plt.tight_layout()
    out_path = f"{ticker}_intraday.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved detailed chart to {out_path}")
    plt.show()


def plot_4h(df_4h: pd.DataFrame, ticker: str, prediction: str):
    """Plot 4-hour price data with prediction and trend projection."""
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.grid(True, alpha=0.3)
    
    # Plot historical price
    ax.plot(df_4h.index, df_4h["Close"], label="Close Price", color="tab:purple", linewidth=2, marker="o", markersize=6)
    
    # Calculate trend for next 2 periods (extrapolate ~8 hours)
    prices_4h = df_4h["Close"].values
    times_4h = np.arange(len(prices_4h)).reshape(-1, 1)
    lr_4h = LinearRegression()
    lr_4h.fit(times_4h, prices_4h)
    
    # Project next 2 candles
    future_times_4h = np.arange(len(prices_4h), len(prices_4h) + 2).reshape(-1, 1)
    future_prices_4h = lr_4h.predict(future_times_4h)
    
    # Create future index (assuming 4-hour intervals)
    last_time_4h = df_4h.index[-1]
    future_index_4h = pd.date_range(start=last_time_4h + pd.Timedelta(hours=4), periods=2, freq='4h')
    
    # Plot projection with color based on prediction
    projection_color = (0.2, 0.8, 0.2) if prediction == "Up" else (0.8, 0.2, 0.2)
    ax.plot(future_index_4h, future_prices_4h, label="Trend Projection", color=projection_color, linewidth=2.5, linestyle="--", marker="s", markersize=8, alpha=0.8)
    
    # Mark current price
    ax.scatter(df_4h.index[-1], df_4h["Close"].iloc[-1], color="purple", s=150, zorder=5, label="Current Price")
    
    # Mark projected endpoint
    ax.scatter(future_index_4h[-1], future_prices_4h[-1], color=projection_color, s=200, marker="*", zorder=6, label=f"Projected Trend ({prediction})")
    
    # Add shaded regions
    if prediction == "Up":
        ax.fill_between(df_4h.index, df_4h["Close"].min() - 20, df_4h["Close"].max() + 20, alpha=0.05, color="green", label="Bullish Zone")
    else:
        ax.fill_between(df_4h.index, df_4h["Close"].min() - 20, df_4h["Close"].max() + 20, alpha=0.05, color="red", label="Bearish Zone")
    
    ax.set_title(f"{ticker} — 4-Hour Timeframe + Trend Projection — Prediction: {prediction}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Price ($)", fontsize=12)
    ax.legend(loc="best", fontsize=10)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    plt.tight_layout()
    out_path = f"{ticker}_4h.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved 4-hour chart to {out_path}")
    plt.show()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simple share up/down predictor (demo)")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--minutes", type=int, default=20, help="How many minutes of recent intraday to use (default 20)")
    args = parser.parse_args(argv)

    ticker = args.ticker.upper()
    print(f"Fetching data for {ticker}...")

    try:
        df_min, df_extended, day_high, day_low = fetch_intraday(ticker, minutes=args.minutes)
        df_daily = fetch_daily(ticker)
        df_4h = fetch_4hour(ticker)
    except Exception as e:
        print("Error fetching data:", e)
        sys.exit(1)

    sma20, sma50 = compute_sma(df_daily)
    features = compute_intraday_features(df_min)
    features_4h = compute_4h_features(df_4h)
    current_price = float(df_min["Close"].iloc[-1])
    result = rule_based_prediction(features, sma20, sma50, current_price)
    result_4h = rule_based_prediction_4h(features_4h, current_price)

    print("\n" + "="*60)
    print("20-MINUTE TIMEFRAME PREDICTION")
    print("="*60)
    print(f"Ticker: {ticker}")
    print(f"Current price: {current_price:.4f}")
    print(f"Day High: {day_high:.4f} | Day Low: {day_low:.4f}")
    print(f"20d SMA: {sma20:.4f}, 50d SMA: {sma50:.4f}")
    print(f"Intraday last-return (over window): {features['last_return']:.6f}")
    print(f"Intraday slope: {features['slope']:.6f}")
    print(f"Prediction: {result['prediction']} (score {result['score']})")
    print("Reasons:")
    for r in result["reasons"]:
        print(" -", r)
    print(f"Suggested stop-loss (5%): {result['stop_loss']:.4f}")
    print(f"Suggested take-profit (10%): {result['take_profit']:.4f}")

    print("\n" + "="*60)
    print("4-HOUR TIMEFRAME PREDICTION (DAY TRADING STRATEGY)")
    print("="*60)
    print(f"Ticker: {ticker}")
    print(f"Current price: {current_price:.4f}")
    print(f"4-hour slope: {features_4h['slope']:.6f}")
    print(f"4-hour last-return: {features_4h['last_return']:.6f}")
    print(f"Volatility: {features_4h['volatility']:.6f}")
    print(f"Avg Volatility: {features_4h['avg_volatility']:.6f}")
    print(f"Prediction: {result_4h['prediction']} (score {result_4h['score']})")
    print("Reasons:")
    for r in result_4h["reasons"]:
        print(" -", r)
    print("\nDAY TRADING LEVELS:")
    if result_4h['prediction'] == "Up":
        print(f"Strategy: LONG (Buy)")
        print(f"Entry: {current_price:.4f}")
        print(f"Stop-loss (-2%): {result_4h['stop_loss']:.4f}")
        print(f"Take-profit (+4%): {result_4h['take_profit']:.4f}")
        print(f"Risk/Reward Ratio: 1:{(result_4h['take_profit'] - current_price) / (current_price - result_4h['stop_loss']):.2f}")
    else:
        print(f"Strategy: SHORT (Sell)")
        print(f"Entry: {current_price:.4f}")
        print(f"Stop-loss (+5%): {result_4h['stop_loss']:.4f}")
        print(f"Take-profit (-5%): {result_4h['take_profit']:.4f}")
        print(f"Risk/Reward Ratio: 1:{(current_price - result_4h['take_profit']) / (result_4h['stop_loss'] - current_price):.2f}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"20-min prediction: {result['prediction']} | 4-hour prediction: {result_4h['prediction']}")

    plot_intraday(df_min, df_extended, ticker, result["stop_loss"], result["take_profit"], result["prediction"], day_high, day_low)
    plot_4h(df_4h, ticker, result_4h["prediction"])


if __name__ == "__main__":
    main()
