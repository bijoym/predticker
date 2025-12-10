#!/usr/bin/env python
"""
Live Trading Predictor with IBKR Integration
Fetches real-time data and generates predictions with trade signals
"""

import asyncio
import pandas as pd
from datetime import datetime
from typing import Optional, Dict
from src.ibkr_connector import IBKRConnector
from src.regime_weights import RegimeAdaptiveWeights
from src.enhanced_predictor_adaptive import enhanced_prediction_adaptive, compute_enhanced_features


class IBKRLivePredictor:
    """Real-time prediction engine using IBKR live data"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 7497):
        self.connector = IBKRConnector(host, port)
        self.optimizer = RegimeAdaptiveWeights()
        
        # Load pre-trained weights
        try:
            self.optimizer.load_weights('models/regime_weights_20251210_135927.pkl')
        except Exception as e:
            print(f"Warning: Could not load weights: {e}")
    
    async def predict_live(self, symbol: str, duration: int = 60, 
                          bar_size: str = '1 min') -> Optional[Dict]:
        """
        Generate prediction using live IBKR data
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            duration: Minutes of history to fetch
            bar_size: Bar size ('1 min', '5 mins', '15 mins', '1 hour')
        
        Returns:
            Dictionary with prediction, confidence, and trading levels
        """
        try:
            # Connect to IBKR
            connected = await self.connector.connect()
            if not connected:
                return self._error_response("Failed to connect to IBKR")
            
            # Fetch live data
            contract = self.connector.create_stock(symbol)
            df = await self.connector.get_market_data(contract, duration, bar_size)
            
            if df is None or len(df) < 20:
                self.connector.disconnect()
                return self._error_response(f"Insufficient data (got {len(df) if df is not None else 0} candles)")
            
            # Reset index
            df = df.reset_index(drop=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Get current price
            current_price = df['Close'].iloc[-1]
            
            # Compute features
            features = compute_enhanced_features(df)
            
            # Get prediction
            prediction = enhanced_prediction_adaptive(features, self.optimizer, use_adaptive_weights=True)
            
            # Extract metrics
            direction = prediction.get('direction', 'NEUTRAL').upper()
            confidence = prediction.get('confidence', 0)
            
            # Calculate trading levels
            atr = features['atr']
            rsi = features['rsi']
            adx = features['adx']
            
            entry_price = current_price
            stop_loss = entry_price - atr if direction == 'LONG' else entry_price + atr
            take_profit = entry_price + (atr * 2) if direction == 'LONG' else entry_price - (atr * 2)
            
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'current_price': current_price,
                'direction': direction,
                'confidence': confidence,
                'signal_strength': self._get_signal_strength(confidence),
                
                # Trading Levels
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward_ratio': risk_reward,
                
                # Technical Indicators
                'rsi': rsi,
                'adx': adx,
                'atr': atr,
                'atr_percent': (atr / current_price * 100),
                
                # Recommendation
                'recommendation': self._get_recommendation(direction, confidence, rsi, adx),
                'data_points': len(df),
                'bar_size': bar_size
            }
            
            self.connector.disconnect()
            return result
        
        except Exception as e:
            self.connector.disconnect()
            return self._error_response(f"Prediction error: {str(e)}")
    
    @staticmethod
    def _error_response(message: str) -> Dict:
        """Generate error response"""
        return {
            'error': message,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
    
    @staticmethod
    def _get_signal_strength(confidence: float) -> str:
        """Get signal strength label"""
        if confidence >= 70:
            return "🟢 STRONG"
        elif confidence >= 50:
            return "🟡 MODERATE"
        else:
            return "⚪ WEAK"
    
    @staticmethod
    def _get_recommendation(direction: str, confidence: float, rsi: float, adx: float) -> str:
        """Generate trading recommendation"""
        if confidence < 40:
            return "❌ NO TRADE - Confidence too low"
        
        if direction == 'LONG':
            if rsi > 70:
                return "⚠️  WAIT - RSI overbought, watch for pullback"
            elif rsi < 30:
                return "🟢 BUY SIGNAL - RSI oversold, strong entry"
            else:
                return f"🟢 BUY - {confidence:.0f}% confidence"
        
        elif direction == 'SHORT':
            if rsi < 30:
                return "⚠️  WAIT - RSI oversold, watch for bounce"
            elif rsi > 70:
                return "🔴 SELL SIGNAL - RSI overbought, strong entry"
            else:
                return f"🔴 SELL - {confidence:.0f}% confidence"
        
        else:
            return "⚪ NEUTRAL - Wait for clearer signal"


async def print_prediction(result: Dict):
    """Pretty print prediction result"""
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    IBKR LIVE PREDICTION RESULT                             ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 LIVE MARKET DATA
═══════════════════════════════════════════════════════════════════════════
Ticker:              {result['symbol']}
Current Price:       ${result['current_price']:.4f}
Data Points:         {result['data_points']} candles ({result['bar_size']})
Timestamp:           {result['timestamp']}

🎯 PREDICTION
═══════════════════════════════════════════════════════════════════════════
Direction:           {result['direction']}
Confidence:          {result['confidence']:.1f}%
Signal Strength:     {result['signal_strength']}
Recommendation:      {result['recommendation']}

📈 TECHNICAL INDICATORS
═══════════════════════════════════════════════════════════════════════════
RSI (14):            {result['rsi']:.2f}
ADX (14):            {result['adx']:.2f}
ATR:                 ${result['atr']:.4f} ({result['atr_percent']:.2f}% of price)

💰 TRADING LEVELS
═══════════════════════════════════════════════════════════════════════════
Entry:               ${result['entry']:.4f}
Stop Loss:           ${result['stop_loss']:.4f}
Take Profit:         ${result['take_profit']:.4f}
Risk/Reward Ratio:   1:{result['risk_reward_ratio']:.2f}

═══════════════════════════════════════════════════════════════════════════
""")


async def main():
    """Main demo function"""
    print("Starting IBKR Live Predictor...\n")
    
    predictor = IBKRLivePredictor()
    
    # Example: Predict AAPL
    print("Fetching live AAPL data and generating prediction...")
    result = await predictor.predict_live('AAPL', duration=60, bar_size='1 min')
    
    await print_prediction(result)


if __name__ == '__main__':
    asyncio.run(main())
