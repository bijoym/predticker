"""Enhanced market predictor with adaptive ML-based weights.

This module combines the original enhanced_predictor functionality with the
adaptive weight optimizer to learn optimal indicator weights from market data.
"""

from typing import Dict, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings

from adaptive_weights import AdaptiveWeightOptimizer

warnings.filterwarnings("ignore")


def fetch_4hour_data(ticker: str, days: int = 90) -> pd.DataFrame:
    """Fetch 4-hour OHLCV data."""
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
    """Calculate Average True Range for volatility measurement."""
    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift())
    low_close = abs(df["Low"] - df["Close"].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean()
    return atr


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index (trend strength)."""
    high_diff = df["High"].diff()
    low_diff = -df["Low"].diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    tr1 = df["High"] - df["Low"]
    tr2 = abs(df["High"] - df["Close"].shift())
    tr3 = abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    plus_dm_smooth = plus_dm.ewm(span=period).mean()
    minus_dm_smooth = minus_dm.ewm(span=period).mean()
    tr_smooth = tr.ewm(span=period).mean()
    
    plus_di = 100 * plus_dm_smooth / tr_smooth
    minus_di = 100 * minus_dm_smooth / tr_smooth
    
    di_sum = plus_di + minus_di
    di_diff = (plus_di - minus_di).abs()
    dx = 100 * di_diff / di_sum
    
    adx = dx.ewm(span=period).mean()
    return adx


def calculate_stochastic(df: pd.DataFrame, k: int = 14, k_smooth: int = 3, d_smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator K and D lines."""
    low_min = df["Low"].rolling(window=k).min()
    high_max = df["High"].rolling(window=k).max()
    
    k_percent = 100 * (df["Close"] - low_min) / (high_max - low_min)
    k_line = k_percent.rolling(window=k_smooth).mean()
    d_line = k_line.rolling(window=d_smooth).mean()
    
    return k_line, d_line


def compute_enhanced_features(df: pd.DataFrame) -> Dict[str, float]:
    """Compute 20 technical indicators for enhanced analysis."""
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
    # Handle NaN safely
    if pd.isna(sma_50) or sma_50 == 0:
        current_position = 0
    else:
        current_position = (price - sma_50) / sma_50
    
    # RSI
    rsi = calculate_rsi(df, 14).iloc[-1]
    
    # MACD
    macd, signal, histogram = calculate_macd(df)
    macd_value = macd.iloc[-1]
    macd_signal = signal.iloc[-1]
    macd_histogram = histogram.iloc[-1]
    
    # Bollinger Bands
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(df, 20, 2.0)
    upper_val = upper_bb.iloc[-1]
    lower_val = lower_bb.iloc[-1]
    bb_range = upper_val - lower_val
    if pd.isna(bb_range) or bb_range == 0:
        bb_position = 0.5
    else:
        bb_position = (price - lower_val) / bb_range
    
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


def detect_volatility_regime(features: Dict[str, float]) -> str:
    """Detect market volatility regime.
    
    Args:
        features: Technical indicator values
    
    Returns:
        'low', 'normal', or 'high'
    """
    atr_percent = features.get('atr_percent', 1.5)
    volatility = features.get('volatility', 1.0)
    
    if atr_percent < 1.0:
        return 'low'
    elif atr_percent > 2.5:
        return 'high'
    else:
        return 'normal'


def enhanced_prediction_adaptive(features: Dict, 
                                optimizer: AdaptiveWeightOptimizer = None,
                                use_adaptive_weights: bool = False) -> Dict:
    """Generate enhanced prediction with optional adaptive weights.
    
    Uses weighted scoring across 5 categories with either:
    - Static weights: Trend(20%), Momentum(25%), Volatility(20%), TrendStrength(20%), Stochastic(15%)
    - Adaptive weights: Learned from market data via ML model
    
    Args:
        features: Dict with 20 technical indicators
        optimizer: AdaptiveWeightOptimizer instance (optional)
        use_adaptive_weights: Whether to use adaptive weights (requires optimizer)
    
    Returns:
        Dict with prediction, confidence, signals, weights
    """
    
    score = 0
    signals = []
    weights = {}
    
    # Get weights (adaptive or static)
    if use_adaptive_weights and optimizer is not None:
        regime = detect_volatility_regime(features)
        weights = optimizer.get_adaptive_weights(features)
        signals.append(f"Using adaptive weights (regime: {regime})")
    else:
        # Default static weights
        weights = {
            "trend": 0.0,
            "momentum": 0.0,
            "volatility": 0.0,
            "trend_strength": 0.0,
            "stochastic": 0.0
        }
    
    # 1. Trend Analysis
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
    
    trend_normalized = trend_score / 3.0
    
    # 2. Momentum Analysis
    momentum_score = 0
    if features["rsi"] < 30:
        momentum_score += 2
        signals.append("RSI < 30 (Oversold - Strong Buy)")
    elif features["rsi"] < 50:
        momentum_score += 1
        signals.append("RSI 30-50 (Mild Buy)")
    elif features["rsi"] > 70:
        momentum_score -= 2
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
    
    momentum_normalized = max(0, min(1, (momentum_score + 2) / 4.0))
    
    # 3. Volatility & Support/Resistance
    volatility_score = 0
    if features["bb_position"] < 0.2:
        volatility_score += 1
        signals.append("Price near lower Bollinger Band (Support)")
    elif features["bb_position"] > 0.8:
        volatility_score -= 1
        signals.append("Price near upper Bollinger Band (Resistance)")
    else:
        signals.append(f"Price at {features['bb_position']*100:.1f}% of BB range")
    
    if features["atr_percent"] < 1.0:
        volatility_score += 1
        signals.append("Low volatility (good for trending)")
    elif features["atr_percent"] > 3.0:
        volatility_score -= 1
        signals.append("High volatility (risky)")
    
    volatility_normalized = max(0, min(1, (volatility_score + 1) / 2.0))
    
    # 4. Trend Strength
    adx_score = 0
    if features["adx"] > 25:
        adx_score += 1
        signals.append(f"Strong trend (ADX: {features['adx']:.1f})")
    elif features["adx"] > 20:
        adx_score += 0.5
        signals.append(f"Moderate trend (ADX: {features['adx']:.1f})")
    else:
        signals.append(f"Weak/no trend (ADX: {features['adx']:.1f})")
    
    trend_strength_normalized = max(0, min(1, features["adx"] / 40.0))
    
    # 5. Stochastic RSI
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
    
    stoch_normalized = max(0, min(1, (stoch_score + 1) / 2.0))
    
    # Calculate weighted final score
    if use_adaptive_weights and optimizer is not None and weights:
        # Use adaptive weights
        final_score = (
            trend_normalized * weights.get("trend", 0.20) +
            momentum_normalized * weights.get("momentum", 0.25) +
            volatility_normalized * weights.get("volatility", 0.20) +
            trend_strength_normalized * weights.get("trend_strength", 0.20) +
            stoch_normalized * weights.get("stochastic", 0.15)
        )
    else:
        # Use default static weights
        final_score = (
            trend_normalized * 0.20 +
            momentum_normalized * 0.25 +
            volatility_normalized * 0.20 +
            trend_strength_normalized * 0.20 +
            stoch_normalized * 0.15
        )
    
    # Confidence calculation
    confidence = abs(final_score - 0.5) * 200  # 0-100%
    
    # Prediction: > 0.5 = Long, < 0.5 = Short
    prediction = "LONG" if final_score > 0.5 else "SHORT"
    
    return {
        "prediction": prediction,
        "score": final_score,
        "confidence": confidence,
        "signals": signals,
        "weights": {
            "trend": weights.get("trend", 0.20),
            "momentum": weights.get("momentum", 0.25),
            "volatility": weights.get("volatility", 0.20),
            "trend_strength": weights.get("trend_strength", 0.20),
            "stochastic": weights.get("stochastic", 0.15)
        },
        "components": {
            "trend": trend_normalized,
            "momentum": momentum_normalized,
            "volatility": volatility_normalized,
            "trend_strength": trend_strength_normalized,
            "stochastic": stoch_normalized
        }
    }


def generate_trading_levels(price: float, atr: float) -> Dict[str, float]:
    """Generate dynamic trading levels based on price and ATR.
    
    Args:
        price: Current price
        atr: Average True Range (volatility measure)
    
    Returns:
        Dict with stop-loss and take-profit levels
    """
    # Long positions
    long_stop_loss = price - (atr * 1.0)
    long_take_profit = price + (atr * 2.0)
    
    # Short positions
    short_stop_loss = price + (atr * 1.0)
    short_take_profit = price - (atr * 2.0)
    
    return {
        "long_stop_loss": long_stop_loss,
        "long_take_profit": long_take_profit,
        "short_stop_loss": short_stop_loss,
        "short_take_profit": short_take_profit,
        "risk_reward_ratio": 2.0
    }


if __name__ == "__main__":
    print("Enhanced Adaptive Predictor Module")
    print("Usage: from src.enhanced_predictor_adaptive import enhanced_prediction_adaptive, compute_enhanced_features")
    print("\nExample:")
    print("  features = compute_enhanced_features(df)")
    print("  optimizer = AdaptiveWeightOptimizer()")
    print("  result = enhanced_prediction_adaptive(features, optimizer, use_adaptive_weights=True)")
