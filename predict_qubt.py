#!/usr/bin/env python
"""QUBT prediction - Hourly analysis (1-min data unavailable)"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.regime_weights import RegimeAdaptiveWeights
from src.enhanced_predictor_adaptive import enhanced_prediction_adaptive, compute_enhanced_features

def predict_qubt():
    ticker = 'QUBT'
    
    try:
        # Fetch hourly data (1-minute not available right now)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        df = yf.download(ticker, start=start_time, end=end_time, interval='1h', progress=False)
        
        if len(df) < 20:
            print(f'\n❌ Insufficient data for {ticker}')
            return None
        
        # Reset index to avoid issues with timestamp index
        df = df.reset_index(drop=True)
        
        # Handle multi-index columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten multi-index by taking first level (OHLCV names)
            df.columns = df.columns.get_level_values(0)
        
        # Load adaptive weights
        optimizer = RegimeAdaptiveWeights()
        optimizer.load_weights('models/regime_weights_20251210_135927.pkl')
        
        # Compute features
        features = compute_enhanced_features(df)
        
        # Generate prediction
        prediction = enhanced_prediction_adaptive(features, optimizer, use_adaptive_weights=True)
        
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0
        
        rsi = features['rsi']
        macd = features['macd']
        macd_signal = features['macd_signal']
        atr = features['atr']
        adx = features['adx']
        momentum = features['slope']  # Using slope as momentum proxy
        
        direction = prediction.get('direction', 'NEUTRAL').upper()
        confidence = prediction.get('confidence', 0)
        
        # Calculate next move targets
        if direction == 'LONG':
            target_up = current_price + (atr * 2)
            target_down = current_price - atr
            action_emoji = '🟢 BUY (BULLISH)'
        elif direction == 'SHORT':
            target_up = current_price + atr
            target_down = current_price - (atr * 2)
            action_emoji = '🔴 SELL (BEARISH)'
        else:
            target_up = current_price + atr
            target_down = current_price - atr
            action_emoji = '⚪ NEUTRAL'
        
        print(f'''
╔════════════════════════════════════════════════════════════════════════════╗
║                      QUBT DIRECTION PREDICTION                             ║
║                                                                            ║
║  Will QUBT go UP or DOWN next?                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 QUBT MARKET SNAPSHOT
═══════════════════════════════════════════════════════════════════════════
Ticker:              QUBT (Quantum Computing)
Current Price:       ${current_price:.4f}
Last Hour Change:    {change_pct:+.3f}%
Data Points:         {len(df)} hourly candles (last 30 days)
Time:                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 PREDICTION RESULT
═══════════════════════════════════════════════════════════════════════════
Next Move:           {direction}
Confidence:          {confidence:.1f}%
Signal Type:         {action_emoji}

{'✓ HIGH CONFIDENCE' if confidence >= 70 else '⚠ MODERATE CONFIDENCE' if confidence >= 50 else '❌ LOW CONFIDENCE - AVOID'}

📈 TECHNICAL INDICATORS
═══════════════════════════════════════════════════════════════════════════
RSI (14):            {rsi:.2f}
  Status:            {'Overbought (>70)' if rsi > 70 else 'Oversold (<30)' if rsi < 30 else 'Neutral (30-70)'}

MACD:                {'🔺 BULLISH (above signal)' if macd > macd_signal else '🔻 BEARISH (below signal)'}
  Line: {macd:.6f}, Signal: {macd_signal:.6f}

ADX (Trend Strength): {adx:.2f}
  Interpretation:    {'Weak trend' if adx < 20 else 'Moderate trend' if adx < 40 else 'Strong trend'}

ATR (Volatility):    ${atr:.4f} per hour

Momentum:            {momentum:+.4f}
  Direction:         {'Positive (bullish)' if momentum > 0 else 'Negative (bearish)'}

📊 PRICE TARGETS
═══════════════════════════════════════════════════════════════════════════
Entry Price:         ${current_price:.4f}
Upside Target:       ${target_up:.4f} (+{((target_up/current_price - 1)*100):.2f}%)
Downside Target:     ${target_down:.4f} ({((target_down/current_price - 1)*100):.2f}%)

Stop Loss:           ${current_price - atr:.4f} (1 ATR below entry)
Take Profit:         ${current_price + atr*2:.4f} (2 ATR above entry)

Risk/Reward:         1:2.0 (excellent ratio)

💡 TRADING ACTION
═══════════════════════════════════════════════════════════════════════════
Expected Direction:  {direction}
Signal Strength:     {confidence:.1f}%

IF BULLISH ({direction == 'LONG'}):
  • BUY if RSI < 70
  • Set stop at ${current_price - atr:.4f}
  • Target profit at ${current_price + atr*2:.4f}
  • Position size: {'NORMAL (50%)' if confidence >= 60 else 'SMALL (25%)'}

IF BEARISH ({direction == 'SHORT'}):
  • SELL if RSI > 30
  • Set stop at ${current_price + atr:.4f}
  • Target profit at ${current_price - atr*2:.4f}
  • Position size: {'NORMAL (50%)' if confidence >= 60 else 'SMALL (25%)'}

IF NEUTRAL:
  • WAIT for clearer signal
  • Monitor ADX for trend confirmation
  • Consider breakout strategy

⚠️  RISK DISCLAIMER
═══════════════════════════════════════════════════════════════════════════
• This is hourly analysis (not 10-minute) due to data limitations
• ML predictions are probabilistic, not guaranteed
• Always use stops and proper position sizing
• Only risk what you can afford to lose
• Past performance does not guarantee future results
• Paper trading recommended for new strategies

═══════════════════════════════════════════════════════════════════════════
                 📌 QUBT DIRECTION PREDICTION COMPLETE
             Next move: {direction} | Confidence: {confidence:.1f}%
═══════════════════════════════════════════════════════════════════════════
''')
        
        return {
            'ticker': ticker,
            'price': current_price,
            'direction': direction,
            'confidence': confidence,
            'rsi': rsi,
            'adx': adx,
            'atr': atr,
            'target_up': target_up,
            'target_down': target_down
        }
    
    except Exception as e:
        print(f'\n❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    predict_qubt()
