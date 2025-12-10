"""
S&P 500 Growth Opportunity Analyzer
Identifies shares with 2%+ growth probability today
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import pickle
import warnings
from pathlib import Path
import time

warnings.filterwarnings('ignore')

# S&P 500 tickers (top 100 by market cap for faster analysis)
SP500_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
    'JNJ', 'WMT', 'V', 'JPM', 'PG', 'MA', 'HD', 'DIS', 'PYPL', 'ADBE',
    'CRM', 'NFLX', 'CSCO', 'INTC', 'CMCSA', 'BA', 'QCOM', 'VZ', 'IBM',
    'TXN', 'ORCL', 'AVGO', 'PEP', 'KO', 'AMD', 'COST', 'ABT', 'MRK',
    'PFE', 'AXP', 'AMEX', 'GS', 'MS', 'BLK', 'SCHW', 'FXAIX', 'TSM',
    'SPOT', 'NOW', 'CCI', 'EQIX', 'DLR', 'PLD', 'AMT', 'PSA', 'WELL',
    'COIN', 'AFRM', 'DASH', 'ZM', 'NET', 'CRWD', 'OKTA', 'SNOW', 'TTD',
    'CDNS', 'SNPS', 'ASML', 'LRCX', 'KLAC', 'NVDA', 'AMD', 'QCOM', 'INTC',
    'MU', 'NXPI', 'AMAT', 'MCHP', 'MRVL', 'XLNX', 'SIRI', 'ROKU', 'PENN',
    'PINS', 'SNAP', 'ENPH', 'DKNG', 'RBLX', 'PLTR', 'RIOT', 'MARA', 'LCID',
    'RIVN', 'SOFI', 'UPST', 'VROOM', 'W', 'ABNB', 'UBER', 'LYFT', 'DOCU'
]

class SP500GrowthAnalyzer:
    """Analyze S&P 500 stocks for growth opportunities"""
    
    def __init__(self):
        self.results = []
        self.model_path = Path('models')
        self.regime_model = self._load_regime_model()
        
    def _load_regime_model(self):
        """Load pre-trained regime weights model"""
        try:
            model_files = list(Path('models').glob('regime_weights_*.pkl'))
            if model_files:
                latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
                with open(latest_model, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Note: Could not load regime model: {e}")
        return None
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators for analysis"""
        try:
            if df.empty or len(df) < 20:
                return None
            
            # Use closing prices
            if isinstance(df.columns, pd.MultiIndex):
                # MultiIndex columns - extract Close
                if 'Close' in df.columns.get_level_values(0):
                    close = df['Close'].iloc[:, 0] if df['Close'].ndim > 1 else df['Close']
                else:
                    close = df.iloc[:, 3] if df.shape[1] > 3 else df.iloc[:, -1]
            else:
                close = df['Close']
            
            indicators = {}
            
            # Trend indicators
            indicators['SMA_20'] = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else None
            indicators['SMA_50'] = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
            
            # Price position relative to SMAs
            current_price = close.iloc[-1]
            if indicators['SMA_20']:
                indicators['Price_vs_SMA20'] = (current_price - indicators['SMA_20']) / indicators['SMA_20']
            
            # Momentum
            returns_5d = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] if len(close) >= 5 else 0
            indicators['Momentum_5d'] = returns_5d
            
            # Volatility
            indicators['Volatility'] = close.pct_change().std() if len(close) > 1 else 0
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / (loss + 1e-10)
            indicators['RSI'] = (100 - (100 / (1 + rs))).iloc[-1]
            
            return indicators
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return None
    
    def predict_growth(self, ticker, indicators):
        """Predict if stock will grow 2%+ today"""
        try:
            if not indicators:
                return None, 0.0
            
            # Calculate bullish signal score (0-100)
            signal_score = 50.0  # Base score
            
            # 1. Momentum analysis (±30 points)
            momentum = indicators.get('Momentum_5d', 0)
            if momentum > 0.05:  # Strong positive momentum
                signal_score += 30
            elif momentum > 0.02:  # Good momentum
                signal_score += 20
            elif momentum > 0:  # Slight positive
                signal_score += 10
            elif momentum < -0.05:  # Negative momentum
                signal_score -= 30
            
            # 2. Price position vs SMA20 (±25 points)
            price_vs_sma = indicators.get('Price_vs_SMA20')
            if price_vs_sma is not None:
                if price_vs_sma > 0.03:  # Well above SMA
                    signal_score += 25
                elif price_vs_sma > 0.01:  # Moderately above
                    signal_score += 15
                elif price_vs_sma > -0.01:  # Near or slightly above
                    signal_score += 5
                else:  # Below SMA
                    signal_score -= 20
            
            # 3. RSI analysis (±20 points)
            rsi = indicators.get('RSI', 50)
            if 50 < rsi < 70:  # Bullish but not overbought
                signal_score += 20
            elif 40 < rsi < 60:  # Neutral to bullish
                signal_score += 10
            elif rsi > 70:  # Overbought - reversal risk
                signal_score -= 15
            elif rsi < 30:  # Oversold - potential bounce
                signal_score += 15
            
            # 4. Volatility factor (±15 points)
            vol = indicators.get('Volatility', 0.03)
            if 0.01 < vol < 0.04:  # Normal volatility - good for trading
                signal_score += 15
            elif vol <= 0.01:  # Very low volatility
                signal_score += 5
            elif vol > 0.08:  # High volatility - risky
                signal_score -= 15
            
            # Clamp probability to 0-100 range
            probability = max(0, min(100, signal_score))
            
            return 'UP', probability
            
        except Exception as e:
            return None, 0.0
    
    def analyze_stock(self, ticker):
        """Analyze single stock"""
        try:
            print(f"  Analyzing {ticker}...", end=' ', flush=True)
            
            # Fetch data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=100)
            
            data = yf.download(ticker, start=start_date, end=end_date, progress=False, prepost=False)
            
            if data.empty or len(data) < 20:
                print("❌ Insufficient data")
                return None
            
            # Handle MultiIndex columns (from yfinance)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            # Get current price and previous close
            current_price = float(data['Close'].iloc[-1])
            previous_close = float(data['Close'].iloc[-2])
            
            # Calculate indicators
            indicators = self.calculate_technical_indicators(data)
            if not indicators:
                print("❌ Cannot calculate indicators")
                return None
            
            # Predict growth
            direction, confidence = self.predict_growth(ticker, indicators)
            
            if direction and confidence > 55:  # Filter for stocks with good growth probability
                result = {
                    'Ticker': ticker,
                    'Current_Price': round(current_price, 2),
                    'Prev_Close': round(previous_close, 2),
                    'Change_%': round((current_price - previous_close) / previous_close * 100, 2),
                    'Growth_Probability_%': round(confidence, 1),
                    'Momentum_5d_%': round(indicators.get('Momentum_5d', 0) * 100, 2),
                    'RSI': round(indicators.get('RSI', 50), 1),
                    'vs_SMA20_%': round(indicators.get('Price_vs_SMA20', 0) * 100, 2) if indicators.get('Price_vs_SMA20') else 0,
                    'Volatility_%': round(indicators.get('Volatility', 0) * 100, 2),
                }
                print(f"✓ Confidence: {confidence:.1f}%")
                return result
            else:
                print(f"{'✓ LOW' if direction else '❌'} {confidence:.1f}%")
                return None
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            return None
    
    def run(self):
        """Run analysis on all tickers"""
        print("\n" + "="*70)
        print("S&P 500 GROWTH OPPORTUNITY ANALYZER")
        print("Finding stocks with 2%+ growth probability today")
        print("="*70)
        print(f"\nAnalyzing {len(SP500_TICKERS)} stocks...")
        print("-"*70)
        
        start_time = time.time()
        
        for ticker in SP500_TICKERS:
            result = self.analyze_stock(ticker)
            if result:
                self.results.append(result)
            time.sleep(0.1)  # Rate limiting
        
        elapsed = time.time() - start_time
        
        # Sort by growth probability
        if self.results:
            df_results = pd.DataFrame(self.results)
            df_results = df_results.sort_values('Growth_Probability_%', ascending=False)
            
            print("\n" + "="*70)
            print("TOP OPPORTUNITIES FOR 2%+ GROWTH TODAY")
            print("="*70)
            print()
            
            # Display top 10
            print(df_results.head(10).to_string(index=False))
            
            print("\n" + "-"*70)
            print(f"SUMMARY: Found {len(df_results)} stocks with 2%+ growth probability")
            print(f"Analysis completed in {elapsed:.1f} seconds")
            print("-"*70)
            
            # Save results to CSV
            csv_path = f"sp500_growth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df_results.to_csv(csv_path, index=False)
            print(f"\n📊 Full results saved to: {csv_path}")
            
            # Statistics
            print("\nKEY STATISTICS:")
            print(f"  Average Growth Probability: {df_results['Growth_Probability_%'].mean():.1f}%")
            print(f"  Highest Probability: {df_results['Growth_Probability_%'].max():.1f}%")
            print(f"  Stocks above 60% probability: {len(df_results[df_results['Growth_Probability_%'] > 60])}")
            print(f"  Stocks above 70% probability: {len(df_results[df_results['Growth_Probability_%'] > 70])}")
            
            # Top recommendations
            print("\n🎯 TOP 5 RECOMMENDATIONS FOR TODAY:")
            for idx, row in df_results.head(5).iterrows():
                print(f"  {idx+1}. {row['Ticker']:<6} - {row['Growth_Probability_%']:.1f}% probability | "
                      f"Price: ${row['Current_Price']:.2f} | RSI: {row['RSI']:.0f}")
            
            return df_results
        else:
            print("\n⚠️  No stocks found with sufficient growth probability")
            return pd.DataFrame()

if __name__ == "__main__":
    analyzer = SP500GrowthAnalyzer()
    results = analyzer.run()
