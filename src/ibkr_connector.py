"""
Interactive Brokers (IBKR) Live Data Connector
Fetches real-time market data for prediction and trading
"""

# Import and apply nest_asyncio FIRST before ib_insync
import nest_asyncio
try:
    nest_asyncio.apply()
except RuntimeError:
    pass

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from ib_insync import IB, Stock, Forex, Index, Future, Contract
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IBKRConnector:
    """Connect to Interactive Brokers and fetch live market data"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 7497, clientId: int = 1):
        """
        Initialize IBKR connector
        
        Args:
            host: TWS/IBGateway host (default: localhost)
            port: TWS/IBGateway port (7497 for paper, 7496 for live)
            clientId: Client ID for connection
        """
        self.host = host
        self.port = port
        self.clientId = clientId
        self.ib = IB()
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to IBKR TWS/Gateway"""
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=self.clientId)
            self.connected = True
            logger.info(f"✓ Connected to IBKR at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to IBKR: {str(e)}")
            logger.info("Make sure TWS or IBGateway is running and accepting connections")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def create_stock(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD') -> Stock:
        """Create a Stock contract"""
        return Stock(symbol, exchange, currency)
    
    def create_forex(self, pair: str) -> Forex:
        """Create a Forex contract (e.g., 'EURUSD')"""
        base, quote = pair[:3], pair[3:]
        return Forex(base, quote)
    
    async def get_market_data(self, contract: Contract, duration: int = 30, 
                              bar_size: str = '1 min') -> Optional[pd.DataFrame]:
        """
        Fetch historical and live market data
        
        Args:
            contract: IB Contract object
            duration: Duration in minutes (for 1-min bars) or days (for larger bars)
            bar_size: Bar size ('1 min', '5 mins', '15 mins', '1 hour', '1 day')
        
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            if not self.connected:
                logger.error("Not connected to IBKR")
                return None
            
            # Request historical data
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr=f'{duration} {"mins" if "min" in bar_size else "D"}',
                barSizeSetting=bar_size,
                whatToShow='MIDPOINT',
                useRTH=False,
                formatDate=1
            )
            
            if not bars:
                logger.warning(f"No data received for {contract.symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame({
                'DateTime': [bar.date for bar in bars],
                'Open': [bar.open for bar in bars],
                'High': [bar.high for bar in bars],
                'Low': [bar.low for bar in bars],
                'Close': [bar.close for bar in bars],
                'Volume': [bar.volume for bar in bars]
            })
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None
    
    async def get_live_price(self, contract: Contract) -> Optional[float]:
        """Get current live price"""
        try:
            if not self.connected:
                return None
            
            ticker = self.ib.reqMktData(contract, '', False, False)
            await asyncio.sleep(1)  # Wait for data
            
            price = ticker.last if ticker.last else ticker.close
            return price
        
        except Exception as e:
            logger.error(f"Error fetching live price: {str(e)}")
            return None
    
    async def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        try:
            if not self.connected:
                return None
            
            acctSummary = self.ib.accountSummary()
            
            info = {
                'account_id': next((v.value for v in acctSummary if v.tag == 'AccountId'), None),
                'cash': float(next((v.value for v in acctSummary if v.tag == 'TotalCashValue'), 0)),
                'equity': float(next((v.value for v in acctSummary if v.tag == 'TotalAccountValue'), 0)),
                'buying_power': float(next((v.value for v in acctSummary if v.tag == 'BuyingPower'), 0)),
                'positions': len(self.ib.positions())
            }
            
            return info
        
        except Exception as e:
            logger.error(f"Error fetching account info: {str(e)}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            positions = []
            for pos in self.ib.positions():
                positions.append({
                    'symbol': pos.contract.symbol,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost
                })
            return positions
        
        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            return []


class IBKRDataFetcher:
    """Fetch live data from IBKR for predictions"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 7497):
        self.connector = IBKRConnector(host, port)
    
    async def fetch_stock_data(self, symbol: str, duration: int = 30, 
                               bar_size: str = '1 min') -> Optional[pd.DataFrame]:
        """Fetch live stock data from IBKR"""
        try:
            connected = await self.connector.connect()
            if not connected:
                return None
            
            contract = self.connector.create_stock(symbol)
            df = await self.connector.get_market_data(contract, duration, bar_size)
            
            self.connector.disconnect()
            return df
        
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            return None
    
    async def fetch_forex_data(self, pair: str, duration: int = 30,
                               bar_size: str = '1 min') -> Optional[pd.DataFrame]:
        """Fetch live forex data from IBKR"""
        try:
            connected = await self.connector.connect()
            if not connected:
                return None
            
            contract = self.connector.create_forex(pair)
            df = await self.connector.get_market_data(contract, duration, bar_size)
            
            self.connector.disconnect()
            return df
        
        except Exception as e:
            logger.error(f"Error fetching forex data: {str(e)}")
            return None


async def demo_ibkr_connection():
    """Demo function to test IBKR connection"""
    connector = IBKRConnector()
    
    # Try to connect
    connected = await connector.connect()
    
    if connected:
        print("\n✓ Successfully connected to IBKR!")
        
        # Try to get account info
        account_info = await connector.get_account_info()
        if account_info:
            print("\n📊 Account Information:")
            for key, value in account_info.items():
                print(f"  {key}: {value}")
        
        # Try to get positions
        positions = connector.get_positions()
        if positions:
            print("\n📈 Current Positions:")
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['quantity']} @ {pos['avg_cost']}")
        
        # Try to fetch stock data
        print("\n📊 Fetching AAPL data...")
        contract = connector.create_stock('AAPL')
        df = await connector.get_market_data(contract, duration=30, bar_size='1 min')
        
        if df is not None:
            print(f"\n✓ Retrieved {len(df)} candles for AAPL")
            print(df.tail())
        else:
            print("✗ Failed to retrieve data")
        
        connector.disconnect()
    else:
        print("\n✗ Failed to connect to IBKR")
        print("\nTo use IBKR integration:")
        print("1. Download TWS or IBGateway from Interactive Brokers")
        print("2. Start TWS/IBGateway")
        print("3. Enable 'Allow connections' in settings")
        print("4. Run this script again")


if __name__ == '__main__':
    # Run demo
    asyncio.run(demo_ibkr_connection())
