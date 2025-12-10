#!/usr/bin/env python
"""
Complete IBKR Trading Workflow
Predict → Execute → Monitor
"""

import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from src.ibkr_connector import IBKRConnector
from src.ibkr_executor import IBKRTradeExecutor, RiskManager
from src.regime_weights import RegimeAdaptiveWeights
from src.enhanced_predictor_adaptive import enhanced_prediction_adaptive, compute_enhanced_features


class IBKRTradingBot:
    """Automated trading bot using IBKR and adaptive predictions"""
    
    def __init__(self, account_size: float = 10000, max_risk_percent: float = 2.0):
        self.predictor_connector = IBKRConnector()
        self.executor = IBKRTradeExecutor()
        self.risk_manager = RiskManager(account_size, max_risk_percent)
        
        # Load weights
        self.optimizer = RegimeAdaptiveWeights()
        try:
            self.optimizer.load_weights('models/regime_weights_20251210_135927.pkl')
        except:
            print("Warning: Could not load pre-trained weights")
    
    async def analyze_and_trade(self, symbol: str, min_confidence: float = 60.0,
                               dry_run: bool = True) -> Dict:
        """
        Complete workflow: Analyze → Predict → Execute
        
        Args:
            symbol: Stock ticker
            min_confidence: Minimum confidence to execute trade (default: 60%)
            dry_run: If True, don't actually execute trades
        
        Returns:
            Trading result
        """
        print(f"\n{'='*80}")
        print(f"Trading Analysis for {symbol}")
        print(f"{'='*80}\n")
        
        try:
            # Step 1: Connect and predict
            print(f"📊 Step 1: Connecting to IBKR and fetching data...")
            connected = await self.predictor_connector.connect()
            if not connected:
                return {'success': False, 'message': 'IBKR connection failed'}
            
            # Fetch data
            contract = self.predictor_connector.create_stock(symbol)
            df = await self.predictor_connector.get_market_data(contract, duration=60, bar_size='1 min')
            
            if df is None or len(df) < 20:
                self.predictor_connector.disconnect()
                return {'success': False, 'message': 'Insufficient data'}
            
            # Reset index
            df = df.reset_index(drop=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            current_price = df['Close'].iloc[-1]
            
            # Step 2: Generate prediction
            print(f"🔮 Step 2: Generating prediction...")
            features = compute_enhanced_features(df)
            prediction = enhanced_prediction_adaptive(features, self.optimizer, use_adaptive_weights=True)
            
            direction = prediction.get('direction', 'NEUTRAL').upper()
            confidence = prediction.get('confidence', 0)
            
            print(f"  Direction: {direction}")
            print(f"  Confidence: {confidence:.1f}%")
            
            # Check confidence threshold
            if confidence < min_confidence:
                print(f"\n⚠️  Confidence {confidence:.1f}% below threshold {min_confidence}%")
                print("   Skipping trade")
                self.predictor_connector.disconnect()
                return {
                    'success': False,
                    'message': f'Confidence {confidence:.1f}% below threshold',
                    'symbol': symbol,
                    'confidence': confidence
                }
            
            # Step 3: Calculate trading levels
            print(f"\n💰 Step 3: Calculating trading levels...")
            atr = features['atr']
            rsi = features['rsi']
            
            entry = current_price
            stop_loss = entry - atr if direction == 'LONG' else entry + atr
            take_profit = entry + (atr * 2) if direction == 'LONG' else entry - (atr * 2)
            
            # Calculate position size
            quantity = self.risk_manager.calculate_position_size(entry, stop_loss)
            
            print(f"  Entry: ${entry:.2f}")
            print(f"  Stop Loss: ${stop_loss:.2f}")
            print(f"  Take Profit: ${take_profit:.2f}")
            print(f"  Position Size: {quantity} shares")
            
            # Step 4: Execute trade
            print(f"\n🚀 Step 4: Executing trade...")
            
            if dry_run:
                print(f"  [DRY RUN] Would place order:")
                print(f"    Action: {direction}")
                print(f"    Quantity: {quantity}")
                print(f"    Entry: ${entry:.2f}")
                print(f"    SL: ${stop_loss:.2f}")
                print(f"    TP: ${take_profit:.2f}")
                trade_result = {
                    'success': True,
                    'dry_run': True,
                    'message': 'Dry run - order not placed'
                }
            else:
                # Execute actual trade
                await self.executor.connect()
                trade_result = await self.executor.place_bracket_order(
                    symbol=symbol,
                    action='BUY' if direction == 'LONG' else 'SELL',
                    quantity=quantity,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                self.executor.disconnect()
            
            # Step 5: Summary
            print(f"\n✓ Trading Analysis Complete")
            print(f"{'='*80}\n")
            
            result = {
                'success': True,
                'symbol': symbol,
                'direction': direction,
                'confidence': confidence,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'quantity': quantity,
                'rsi': rsi,
                'atr': atr,
                'trade_result': trade_result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.predictor_connector.disconnect()
            return result
        
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            self.predictor_connector.disconnect()
            return {'success': False, 'message': str(e)}
    
    async def monitor_positions(self) -> Dict:
        """Monitor current positions"""
        try:
            await self.executor.connect()
            
            positions = self.executor.get_positions()
            orders = self.executor.get_orders()
            
            result = {
                'positions': positions,
                'orders': orders,
                'timestamp': datetime.now().isoformat()
            }
            
            self.executor.disconnect()
            return result
        
        except Exception as e:
            return {'success': False, 'message': str(e)}


async def main():
    """Main trading bot demo"""
    
    # Initialize bot with $10,000 account, max 2% risk per trade
    bot = IBKRTradingBot(account_size=10000, max_risk_percent=2.0)
    
    # Example: Analyze and trade AAPL (dry run)
    result = await bot.analyze_and_trade('AAPL', min_confidence=60.0, dry_run=True)
    
    if result['success']:
        print(f"""
✓ Trading Analysis Summary
{'='*80}
Symbol:        {result['symbol']}
Direction:     {result['direction']}
Confidence:    {result['confidence']:.1f}%
Entry:         ${result['entry']:.2f}
Stop Loss:     ${result['stop_loss']:.2f}
Take Profit:   ${result['take_profit']:.2f}
Quantity:      {result['quantity']} shares
RSI:           {result['rsi']:.2f}
ATR:           ${result['atr']:.4f}
{'='*80}
""")
    else:
        print(f"✗ Analysis failed: {result['message']}")


if __name__ == '__main__':
    asyncio.run(main())
