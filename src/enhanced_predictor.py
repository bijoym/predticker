"""Enhanced market predictor with multiple technical indicators.

This module provides multi-indicator technical analysis for improved prediction
accuracy using weighted scoring across 7 different technical indicators.
"""

from typing import Dict, Tuple

import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore")


def fetch_4hour_data(ticker: str, days: int = 90) -> pd.DataFrame:
    """Fetch 4-hour OHLCV data.
    
    Args:
        ticker: Ticker symbol
        days: Number of days of historical data (default 90)
    
    Returns:
        DataFrame with 4-hour OHLCV data
    """
    t = yf.Ticker(ticker)
    df = t.history(period=f"{days}d", interval="4h", actions=False)
    if df.empty:
        raise RuntimeError(f"No data for {ticker}")
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.tz_convert(None) if df.index.tz is not None else df
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Calculate MACD and Signal line."""
    ema_fast = df["Close"].ewm(span=fast).mean()
    ema_slow = df["Close"].ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> tuple:
    """Calculate Bollinger Bands."""
    sma = df["Close"].rolling(window=period).mean()
    std = df["Close"].rolling(window=period).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range for volatility measurement.
    
    Args:
        df: DataFrame with OHLCV data
        period: ATR period (default 14)
    
    Returns:
        Series with ATR values
    """
    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift())
    low_close = abs(df["Low"] - df["Close"].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean()
    return atr


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index (trend strength).
    
    Args:
        df: DataFrame with OHLCV data
        period: ADX period (default 14)
    
    Returns:
        Series with ADX values
    """
    high_diff = df["High"].diff()
    low_diff = -df["Low"].diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    tr = calculate_atr(df, period)
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
    
    di_diff = abs(plus_di - minus_di)
    di_sum = plus_di + minus_di
    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(period).mean()
    
    return adx


def calculate_stochastic(df: pd.DataFrame, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator.
    
    Args:
        df: DataFrame with OHLCV data
        period: Stochastic period (default 14)
        smooth_k: K smoothing period (default 3)
        smooth_d: D smoothing period (default 3)
    
    Returns:
        Tuple of (k_percent_smooth, d_percent)
    """
    low_min = df["Low"].rolling(window=period).min()
    high_max = df["High"].rolling(window=period).max()
    
    k_percent = 100 * ((df["Close"] - low_min) / (high_max - low_min))
    k_percent_smooth = k_percent.rolling(window=smooth_k).mean()
    d_percent = k_percent_smooth.rolling(window=smooth_d).mean()
    
    return k_percent_smooth, d_percent


def compute_enhanced_features(df: pd.DataFrame) -> Dict[str, float]:
    """Compute multiple technical indicators for analysis.
    
    Calculates 20 different features including trend, momentum, volatility,
    moving averages, RSI, MACD, Bollinger Bands, ATR, ADX, and Stochastic.
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        Dict with 20 indicator values
    """
    
    # Trend indicators
    prices = df["Close"].values
    times = np.arange(len(prices)).reshape(-1, 1)
    lr = LinearRegression()
    lr.fit(times, prices)
    slope = float(lr.coef_[0])
    
    # Returns
    last_return = (prices[-1] / prices[0] - 1.0) if len(prices) >= 2 else 0.0
    
    # Volatility
    volatility = float(df["Close"].std())
    
    # Moving Averages
    sma_20 = df["Close"].rolling(20).mean().iloc[-1]
    sma_50 = df["Close"].rolling(50).mean().iloc[-1]
    ema_12 = df["Close"].ewm(span=12).mean().iloc[-1]
    ema_26 = df["Close"].ewm(span=26).mean().iloc[-1]
    
    # Price position
    price = df["Close"].iloc[-1]
    current_position = (price - sma_50) / sma_50 if sma_50 != 0 else 0
    
    # RSI
    rsi = calculate_rsi(df, 14).iloc[-1]
    
    # MACD
    macd, signal, histogram = calculate_macd(df)
    macd_value = macd.iloc[-1]
    macd_signal = signal.iloc[-1]
    macd_histogram = histogram.iloc[-1]
    
    # Bollinger Bands
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(df, 20, 2.0)
    bb_position = (price - lower_bb.iloc[-1]) / (upper_bb.iloc[-1] - lower_bb.iloc[-1]) if (upper_bb.iloc[-1] - lower_bb.iloc[-1]) != 0 else 0.5
    
    # ATR and Volatility
    atr = calculate_atr(df, 14).iloc[-1]
    atr_percent = (atr / price * 100) if price != 0 else 0
    
    # ADX
    adx = calculate_adx(df, 14).iloc[-1]
    
    # Stochastic
    k_stoch, d_stoch = calculate_stochastic(df, 14, 3, 3)
    k_value = k_stoch.iloc[-1]
    d_value = d_stoch.iloc[-1]
    
    # Volume
    avg_volume = float(df["Volume"].mean()) if "Volume" in df.columns else 0.0
    
    return {
        "slope": slope,
        "last_return": last_return,
        "volatility": volatility,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "ema_12": ema_12,
        "ema_26": ema_26,
        "price": price,
        "current_position": current_position,
        "rsi": rsi,
        "macd": macd_value,
        "macd_signal": macd_signal,
        "macd_histogram": macd_histogram,
        "bb_position": bb_position,
        "atr": atr,
        "atr_percent": atr_percent,
        "adx": adx,
        "k_stoch": k_value,
        "d_stoch": d_value,
        "avg_volume": avg_volume
    }


def enhanced_prediction(features: Dict) -> Dict:
    """Generate enhanced prediction using multiple indicators.
    
    Uses weighted scoring across 5 categories:
    - Trend (20%): slope, SMA, EMA
    - Momentum (25%): RSI, MACD
    - Volatility (20%): Bollinger Bands, ATR
    - Trend Strength (20%): ADX
    - Stochastic (15%): K/D crossover
    
    Args:
        features: Dict with 20 technical indicators
    
    Returns:
        Dict with prediction, confidence, signals, weights
    """
    
    score = 0
    signals = []
    weights = {}
    
    # 1. Trend Analysis (Weight: 20%)
    trend_score = 0
    if features["slope"] > 0:
        trend_score += 1
        signals.append("Positive slope (bullish)")
    else:
        signals.append("Negative slope (bearish)")
    
    if features["sma_20"] > features["sma_50"]:
        trend_score += 1
        signals.append("SMA20 > SMA50 (uptrend)")
    else:
        signals.append("SMA20 <= SMA50 (downtrend)")
    
    if features["ema_12"] > features["ema_26"]:
        trend_score += 1
        signals.append("EMA12 > EMA26 (bullish)")
    else:
        signals.append("EMA12 <= EMA26 (bearish)")
    
    weights["trend"] = trend_score / 3.0  # 0-1 scale
    
    # 2. Momentum Analysis (Weight: 25%)
    momentum_score = 0
    if features["rsi"] < 30:
        momentum_score += 2  # Oversold - strong buy signal
        signals.append("RSI < 30 (Oversold - Strong Buy)")
    elif features["rsi"] < 50:
        momentum_score += 1
        signals.append("RSI 30-50 (Mild Buy)")
    elif features["rsi"] > 70:
        momentum_score -= 2  # Overbought - strong sell signal
        signals.append("RSI > 70 (Overbought - Strong Sell)")
    else:
        momentum_score += 0
        signals.append("RSI 50-70 (Neutral)")
    
    if features["macd_histogram"] > 0 and features["macd"] > features["macd_signal"]:
        momentum_score += 1
        signals.append("MACD bullish (histogram > 0, MACD > Signal)")
    elif features["macd_histogram"] < 0 and features["macd"] < features["macd_signal"]:
        momentum_score -= 1
        signals.append("MACD bearish (histogram < 0, MACD < Signal)")
    
    weights["momentum"] = max(0, min(1, (momentum_score + 2) / 4.0))  # Normalize to 0-1
    
    # 3. Volatility & Support/Resistance (Weight: 20%)
    volatility_score = 0
    if features["bb_position"] < 0.2:
        volatility_score += 1
        signals.append("Price near lower Bollinger Band (Support)")
    elif features["bb_position"] > 0.8:
        volatility_score -= 1
        signals.append("Price near upper Bollinger Band (Resistance)")
    else:
        signals.append(f"Price at {features['bb_position']*100:.1f}% of BB range")
    
    # Low volatility (consolidation) is good for trending
    if features["atr_percent"] < 1.0:
        volatility_score += 1
        signals.append("Low volatility (good for trending)")
    elif features["atr_percent"] > 3.0:
        volatility_score -= 1
        signals.append("High volatility (risky)")
    
    weights["volatility"] = max(0, min(1, (volatility_score + 1) / 2.0))
    
    # 4. Trend Strength (Weight: 20%)
    adx_score = 0
    if features["adx"] > 25:
        adx_score += 1
        signals.append(f"Strong trend (ADX: {features['adx']:.1f})")
    elif features["adx"] > 20:
        adx_score += 0.5
        signals.append(f"Moderate trend (ADX: {features['adx']:.1f})")
    else:
        signals.append(f"Weak/no trend (ADX: {features['adx']:.1f})")
    
    weights["trend_strength"] = max(0, min(1, features["adx"] / 40.0))
    
    # 5. Stochastic RSI (Weight: 15%)
    stoch_score = 0
    if features["k_stoch"] < 20:
        stoch_score += 1
        signals.append("Stochastic oversold (< 20)")
    elif features["k_stoch"] > 80:
        stoch_score -= 1
        signals.append("Stochastic overbought (> 80)")
    
    if features["k_stoch"] > features["d_stoch"]:
        stoch_score += 0.5
        signals.append("K > D (Bullish crossover)")
    elif features["k_stoch"] < features["d_stoch"]:
        stoch_score -= 0.5
        signals.append("K < D (Bearish crossover)")
    
    weights["stochastic"] = max(0, min(1, (stoch_score + 1) / 2.0))
    
    # Calculate weighted final score
    final_score = (
        weights["trend"] * 0.20 +
        weights["momentum"] * 0.25 +
        weights["volatility"] * 0.20 +
        weights["trend_strength"] * 0.20 +
        weights["stochastic"] * 0.15
    )
    
    # Prediction: > 0.5 = Up, < 0.5 = Down
    prediction = "Up" if final_score > 0.5 else "Down"
    confidence = abs(final_score - 0.5) * 2 * 100  # 0-100 scale
    
    return {
        "prediction": prediction,
        "score": final_score,
        "confidence": confidence,
        "signals": signals,
        "weights": weights,
        "rsi": features["rsi"],
        "adx": features["adx"],
        "macd_histogram": features["macd_histogram"],
        "bb_position": features["bb_position"]
    }


def generate_trading_levels(price: float, prediction: str, atr: float, volatility: Dict) -> Dict:
    """Generate stop-loss and take-profit levels based on volatility.
    
    Uses ATR (Average True Range) to dynamically adjust stop-loss levels
    while maintaining a 1:2 risk/reward ratio.
    
    Args:
        price: Current price
        prediction: "Up" for LONG, "Down" for SHORT
        atr: Average True Range value
        volatility: Dict with ATR percent and other volatility metrics
    
    Returns:
        Dict with stop_loss, take_profit, sl_percent, tp_percent
    """
    
    # Volatility-adjusted levels
    atr_percent = volatility.get("atr_percent", 1.5)
    
    if prediction == "Up":
        # Dynamic stops based on ATR
        sl_percent = min(3.0, max(1.5, atr_percent * 1.5))  # 1.5-3%
        tp_percent = sl_percent * 2  # Risk 1:2 ratio
        
        stop_loss = price * (1 - sl_percent / 100)
        take_profit = price * (1 + tp_percent / 100)
    else:
        # Short strategy
        sl_percent = min(3.0, max(1.5, atr_percent * 1.5))  # 1.5-3%
        tp_percent = sl_percent * 2  # Risk 1:2 ratio
        
        stop_loss = price * (1 + sl_percent / 100)
        take_profit = price * (1 - tp_percent / 100)
    
    return {
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "sl_percent": sl_percent,
        "tp_percent": tp_percent
    }


if __name__ == "__main__":
    # Test the enhanced predictor
    ticker = "GOOGL"
    print(f"Testing Enhanced Predictor on {ticker}")
    print("=" * 70)
    
    try:
        df = fetch_4hour_data(ticker, days=90)
        features = compute_enhanced_features(df)
        result = enhanced_prediction(features)
        
        print(f"\nTicker: {ticker}")
        print(f"Current Price: ${features['price']:.2f}")
        print(f"\nPrediction: {result['prediction']}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Score: {result['score']:.2f}")
        
        print(f"\nKey Indicators:")
        print(f"  RSI: {result['rsi']:.2f} (30-70 range)")
        print(f"  ADX: {result['adx']:.2f} (Trend Strength)")
        print(f"  MACD Histogram: {result['macd_histogram']:.4f}")
        print(f"  BB Position: {result['bb_position']*100:.1f}% (0-100)")
        
        print(f"\nWeights (Importance):")
        for key, value in result['weights'].items():
            print(f"  {key.capitalize()}: {value*100:.1f}%")
        
        print(f"\nSignals:")
        for i, signal in enumerate(result['signals'], 1):
            print(f"  {i}. {signal}")
        
        # Generate trading levels
        levels = generate_trading_levels(
            features['price'],
            result['prediction'],
            features['atr'],
            features
        )
        
        print(f"\nTrading Levels:")
        if result['prediction'] == "Up":
            print(f"  Strategy: LONG")
            print(f"  Entry: ${features['price']:.2f}")
            print(f"  Stop-Loss: ${levels['stop_loss']:.2f} (-{levels['sl_percent']:.2f}%)")
            print(f"  Take-Profit: ${levels['take_profit']:.2f} (+{levels['tp_percent']:.2f}%)")
        else:
            print(f"  Strategy: SHORT")
            print(f"  Entry: ${features['price']:.2f}")
            print(f"  Stop-Loss: ${levels['stop_loss']:.2f} (+{levels['sl_percent']:.2f}%)")
            print(f"  Take-Profit: ${levels['take_profit']:.2f} (-{levels['tp_percent']:.2f}%)")
        
    except Exception as e:
        print(f"Error: {e}")
