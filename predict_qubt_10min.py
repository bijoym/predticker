#!/usr/bin/env python
"""Quick 10-minute QUBT prediction using adaptive weights"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.regime_weights import RegimeAdaptiveWeights
from src.enhanced_predictor_adaptive import enhanced_prediction_adaptive, compute_enhanced_features

def predict_qubt_10min():
    ticker = 'QUBT'
    
    try:
        # Fetch 1-minute data for the last 60 minutes
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=75)
        
        df = yf.download(ticker, start=start_time, end=end_time, interval='1m', progress=False)
        
        if len(df) < 20:
            print(f'\n❌ INSUFFICIENT DATA')
            print(f'Got {len(df)} 1-minute candles, need at least 20')
            print(f'\nℹ️  Note: 1-minute data is only available during market hours (9:30 AM - 4:00 PM ET)')
            print(f'Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'\nAlternative: Try hourly prediction instead')
            return None
        
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
        
        rsi = features['rsi'].iloc[-1]
        macd_line = features['macd_line'].iloc[-1]
        macd_signal = features['macd_signal'].iloc[-1]
        atr = features['atr'].iloc[-1]
        adx = features['adx'].iloc[-1]
        momentum = features['momentum'].iloc[-1]
        
        direction = prediction.get('direction', 'NEUTRAL').upper()
        confidence = prediction.get('confidence', 0)
        
        # Determine signal strength
        if confidence >= 70:
            signal_strength = "🟢 STRONG"
        elif confidence >= 50:
            signal_strength = "🟡 MODERATE"
        else:
            signal_strength = "⚪ WEAK"
        
        print(f'''
╔════════════════════════════════════════════════════════════════════════════╗
║                      10-MINUTE QUBT PREDICTION                             ║
║                                                                            ║
║  Will {ticker} go UP or DOWN in the next 10 minutes?                      ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 MARKET DATA
═══════════════════════════════════════════════════════════════════════════
Ticker:              {ticker}
Current Price:       ${current_price:.4f}
Last Candle Δ:       {change_pct:+.3f}%
Time:                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Candles Analyzed:    {len(df)} (1-minute)

🎯 PREDICTION FOR NEXT 10 MINUTES
═══════════════════════════════════════════════════════════════════════════
Direction:           {direction}
Signal Strength:     {signal_strength} ({confidence:.1f}% confidence)
Recommendation:      {'🚀 BUY (expect UP)' if direction == 'LONG' else '📉 SELL (expect DOWN)' if direction == 'SHORT' else '⚪ NO CLEAR SIGNAL'}

📈 TECHNICAL ANALYSIS
═══════════════════════════════════════════════════════════════════════════
RSI (14):            {rsi:.2f}  {'(Overbought)' if rsi > 70 else '(Oversold)' if rsi < 30 else '(Neutral)'}
MACD:                {'🔺 BULLISH' if macd_line > macd_signal else '🔻 BEARISH'}
ADX:                 {adx:.2f}  {'(Weak trend)' if adx < 20 else '(Moderate trend)' if adx < 40 else '(Strong trend)'}
ATR (Volatility):    {atr:.4f}
Momentum:            {momentum:+.4f}

💰 NEXT 10 MINUTES ACTION
═══════════════════════════════════════════════════════════════════════════
Expected Direction:  {direction}
Risk Level:          {'HIGH' if confidence < 40 else 'MEDIUM' if confidence < 60 else 'MODERATE'}
Action:              
   ✓ Direction: {direction}
   ✓ Confidence: {confidence:.1f}%
   ✓ Stop: Use tight stop (1 ATR = {atr*100:.2f}% of price)
   ✓ Target: 2-3 ATR ({atr*2*100:.2f}% - {atr*3*100:.2f}%)

⚠️  IMPORTANT DISCLAIMERS
═══════════════════════════════════════════════════════════════════════════
• 1-minute predictions are HIGH RISK and HIGHLY VOLATILE
• Should only be used for scalping with TIGHT STOPS
• Requires ACTIVE MARKET HOURS (9:30 AM - 4:00 PM ET)
• Confidence < 40% = DO NOT TRADE
• Machine learning models are probabilistic, not guaranteed
• Always use risk management and position sizing
• Demo/paper trading recommended for testing

═══════════════════════════════════════════════════════════════════════════
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════════════════════════════════════════
''')
        
        return {
            'ticker': ticker,
            'price': current_price,
            'direction': direction,
            'confidence': confidence,
            'rsi': rsi,
            'adx': adx,
            'atr': atr
        }
    
    except Exception as e:
        print(f'\n❌ ERROR: {str(e)}')
        print(f'\nPossible causes:')
        print(f'  1. Market is closed (only works during 9:30 AM - 4:00 PM ET)')
        print(f'  2. QUBT ticker data not available')
        print(f'  3. Network connectivity issue')
        return None

if __name__ == '__main__':
    predict_qubt_10min()
