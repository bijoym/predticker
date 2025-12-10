"""
IBKR Trade Execution with Risk Management
Execute trades with predefined risk parameters and stop losses
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from ib_insync import IB, Stock, LimitOrder, StopOrder, Order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IBKRTradeExecutor:
    """Execute trades on IBKR with risk management"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 7497):
        self.ib = IB()
        self.host = host
        self.port = port
        self.connected = False
        self.order_id_counter = 0
    
    async def connect(self) -> bool:
        """Connect to IBKR"""
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=1)
            self.connected = True
            logger.info("✓ Connected to IBKR for trading")
            return True
        except Exception as e:
            logger.error(f"✗ Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
    
    async def place_bracket_order(self, symbol: str, action: str, quantity: int,
                                  entry_price: float, stop_loss: float, 
                                  take_profit: float) -> Dict:
        """
        Place a bracket order (entry + stop + target)
        
        Args:
            symbol: Stock ticker
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            Order execution result
        """
        try:
            if not self.connected:
                return {
                    'success': False,
                    'message': 'Not connected to IBKR',
                    'timestamp': datetime.now().isoformat()
                }
            
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Create primary order (entry)
            primary_order = Order()
            primary_order.action = action
            primary_order.orderType = 'LMT'
            primary_order.totalQuantity = quantity
            primary_order.lmtPrice = entry_price
            primary_order.transmit = False
            
            # Create stop loss order
            stop_order = Order()
            stop_order.action = 'SELL' if action == 'BUY' else 'BUY'
            stop_order.orderType = 'STP'
            stop_order.totalQuantity = quantity
            stop_order.auxPrice = stop_loss
            stop_order.transmit = False
            stop_order.parentId = 0  # Will be set by TWS
            
            # Create take profit order
            tp_order = Order()
            tp_order.action = 'SELL' if action == 'BUY' else 'BUY'
            tp_order.orderType = 'LMT'
            tp_order.totalQuantity = quantity
            tp_order.lmtPrice = take_profit
            tp_order.transmit = False
            tp_order.parentId = 0  # Will be set by TWS
            
            # Place orders
            trade = self.ib.placeOrder(contract, primary_order)
            await asyncio.sleep(1)
            
            result = {
                'success': True,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_per_share': abs(entry_price - stop_loss),
                'max_loss': abs(entry_price - stop_loss) * quantity,
                'max_gain': abs(take_profit - entry_price) * quantity,
                'order_id': trade.order.orderId if trade else None,
                'timestamp': datetime.now().isoformat(),
                'message': 'Bracket order placed successfully'
            }
            
            logger.info(f"✓ Order placed: {action} {quantity} {symbol} @ ${entry_price}")
            return result
        
        except Exception as e:
            logger.error(f"Order placement failed: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def place_market_order(self, symbol: str, action: str, 
                                quantity: int) -> Dict:
        """Place a market order"""
        try:
            if not self.connected:
                return {'success': False, 'message': 'Not connected'}
            
            contract = Stock(symbol, 'SMART', 'USD')
            order = Order()
            order.action = action
            order.orderType = 'MKT'
            order.totalQuantity = quantity
            
            trade = self.ib.placeOrder(contract, order)
            await asyncio.sleep(1)
            
            result = {
                'success': True,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'order_type': 'MARKET',
                'order_id': trade.order.orderId if trade else None,
                'timestamp': datetime.now().isoformat(),
                'message': 'Market order placed'
            }
            
            logger.info(f"✓ Market order placed: {action} {quantity} {symbol}")
            return result
        
        except Exception as e:
            logger.error(f"Market order failed: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def get_open_orders(self) -> List[Dict]:
        """Get all open orders"""
        try:
            orders = []
            for trade in self.ib.openTrades():
                orders.append({
                    'symbol': trade.contract.symbol,
                    'action': trade.order.action,
                    'quantity': trade.order.totalQuantity,
                    'type': trade.order.orderType,
                    'status': trade.orderStatus.status,
                    'filled': trade.orderStatus.filled,
                    'remaining': trade.orderStatus.remaining
                })
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            positions = []
            for pos in self.ib.positions():
                positions.append({
                    'symbol': pos.contract.symbol,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_price': pos.marketPrice,
                    'market_value': pos.marketValue,
                    'unrealized_pnl': pos.unrealizedPNL,
                    'pnl_percent': (pos.unrealizedPNL / pos.marketValue * 100) if pos.marketValue else 0
                })
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    async def cancel_order(self, order_id: int) -> Dict:
        """Cancel an open order"""
        try:
            if not self.connected:
                return {'success': False, 'message': 'Not connected'}
            
            # Find and cancel the order
            for trade in self.ib.openTrades():
                if trade.order.orderId == order_id:
                    self.ib.cancelOrder(trade.order)
                    await asyncio.sleep(1)
                    
                    return {
                        'success': True,
                        'order_id': order_id,
                        'message': 'Order cancelled',
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {'success': False, 'message': f'Order {order_id} not found'}
        
        except Exception as e:
            logger.error(f"Cancel order failed: {str(e)}")
            return {'success': False, 'message': str(e)}


class RiskManager:
    """Manage trading risk and position sizing"""
    
    def __init__(self, account_size: float, max_risk_percent: float = 2.0):
        """
        Initialize risk manager
        
        Args:
            account_size: Total account size
            max_risk_percent: Max % of account to risk per trade (default: 2%)
        """
        self.account_size = account_size
        self.max_risk_percent = max_risk_percent
        self.max_risk_per_trade = (account_size * max_risk_percent) / 100
    
    def calculate_position_size(self, entry: float, stop_loss: float) -> int:
        """Calculate safe position size based on risk"""
        risk_per_share = abs(entry - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        shares = int(self.max_risk_per_trade / risk_per_share)
        return max(1, shares)  # At least 1 share
    
    def get_trading_limits(self) -> Dict:
        """Get current trading limits"""
        return {
            'account_size': self.account_size,
            'max_risk_percent': self.max_risk_percent,
            'max_risk_per_trade': self.max_risk_per_trade,
            'timestamp': datetime.now().isoformat()
        }


async def demo_trading():
    """Demo trading functionality"""
    executor = IBKRTradeExecutor()
    
    connected = await executor.connect()
    if not connected:
        print("Could not connect to IBKR. Make sure TWS/IBGateway is running.")
        return
    
    # Example: Place a bracket order
    print("\nExample: Placing bracket order...")
    result = await executor.place_bracket_order(
        symbol='AAPL',
        action='BUY',
        quantity=10,
        entry_price=150.00,
        stop_loss=148.00,
        take_profit=155.00
    )
    print(result)
    
    # Check open orders
    print("\nOpen Orders:")
    orders = executor.get_open_orders()
    for order in orders:
        print(f"  {order['symbol']}: {order['action']} {order['quantity']} @ {order['status']}")
    
    # Check positions
    print("\nCurrent Positions:")
    positions = executor.get_positions()
    for pos in positions:
        print(f"  {pos['symbol']}: {pos['quantity']} shares, PnL: {pos['pnl_percent']:.2f}%")
    
    executor.disconnect()


if __name__ == '__main__':
    asyncio.run(demo_trading())
