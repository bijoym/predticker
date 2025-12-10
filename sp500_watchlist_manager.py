#!/usr/bin/env python3
"""
S&P 500 Growth Watchlist Manager
Quickly access today's top opportunities and set up trading alerts
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

def load_latest_results():
    """Load the most recent S&P 500 growth analysis"""
    csv_files = list(Path('.').glob('sp500_growth_*.csv'))
    if not csv_files:
        print("❌ No results found. Run 'python find_sp500_growth.py' first.")
        return None
    
    latest = max(csv_files, key=lambda p: p.stat().st_mtime)
    return pd.read_csv(latest), str(latest)

def display_top_stocks(df, limit=20):
    """Display top performing stocks"""
    top = df.nlargest(limit, 'Growth_Probability_%')
    
    print("\n" + "="*100)
    print("🏆 TOP OPPORTUNITIES FOR TODAY")
    print("="*100)
    print()
    
    for idx, (_, row) in enumerate(top.iterrows(), 1):
        confidence_bar = "█" * int(row['Growth_Probability_%'] / 5) + "░" * (20 - int(row['Growth_Probability_%'] / 5))
        print(f"{idx:2d}. {row['Ticker']:<6} {confidence_bar} {row['Growth_Probability_%']:>6.1f}%  |  "
              f"Price: ${row['Current_Price']:>8.2f}  RSI: {row['RSI']:>5.1f}  Momentum: {row['Momentum_5d_%']:>6.2f}%")
    
    print()

def filter_by_confidence(df, threshold=80):
    """Filter stocks by confidence threshold"""
    filtered = df[df['Growth_Probability_%'] >= threshold]
    return filtered.sort_values('Growth_Probability_%', ascending=False)

def show_momentum_leaders(df, limit=10):
    """Show stocks with best 5-day momentum"""
    print("\n" + "="*100)
    print("🚀 MOMENTUM LEADERS (5-Day)")
    print("="*100)
    print()
    
    top_momentum = df.nlargest(limit, 'Momentum_5d_%')
    for idx, (_, row) in enumerate(top_momentum.iterrows(), 1):
        print(f"{idx:2d}. {row['Ticker']:<6} Momentum: {row['Momentum_5d_%']:>7.2f}%  |  "
              f"Price: ${row['Current_Price']:>8.2f}  Confidence: {row['Growth_Probability_%']:.0f}%")
    print()

def show_technical_summary(df, ticker):
    """Show detailed technical summary for a stock"""
    stock = df[df['Ticker'] == ticker.upper()]
    
    if stock.empty:
        print(f"❌ {ticker} not found in results")
        return
    
    row = stock.iloc[0]
    
    print("\n" + "="*100)
    print(f"📊 TECHNICAL SUMMARY: {row['Ticker']}")
    print("="*100)
    print()
    print(f"  Current Price:        ${row['Current_Price']:.2f}")
    print(f"  Previous Close:       ${row['Prev_Close']:.2f}")
    print(f"  Daily Change:         {row['Change_%']:+.2f}%")
    print()
    print(f"  Growth Probability:   {row['Growth_Probability_%']:.1f}%  {'✓' if row['Growth_Probability_%'] >= 75 else '⚠'}")
    print(f"  5-Day Momentum:       {row['Momentum_5d_%']:+.2f}%")
    print(f"  RSI (14):             {row['RSI']:.1f}  ", end="")
    
    if row['RSI'] > 70:
        print("⚠️  OVERBOUGHT")
    elif row['RSI'] < 30:
        print("⚠️  OVERSOLD")
    elif 40 < row['RSI'] < 60:
        print("✓ NEUTRAL")
    else:
        print("✓ BALANCED")
    
    print(f"  vs SMA20:             {row['vs_SMA20_%']:+.2f}%  ", end="")
    
    if row['vs_SMA20_%'] > 3:
        print("📈 STRONG UPTREND")
    elif row['vs_SMA20_%'] > 0:
        print("📈 UPTREND")
    elif row['vs_SMA20_%'] > -1:
        print("➡️  NEUTRAL")
    else:
        print("📉 DOWNTREND")
    
    print(f"  Volatility:           {row['Volatility_%']:.2f}%")
    print()

def export_trading_list(df, confidence_threshold=75, filename=None):
    """Export trading watchlist"""
    if filename is None:
        filename = f"watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    filtered = filter_by_confidence(df, confidence_threshold)
    filtered = filtered[['Ticker', 'Current_Price', 'Growth_Probability_%', 'RSI', 'Momentum_5d_%']].copy()
    filtered.to_csv(filename, index=False)
    
    print(f"✓ Exported {len(filtered)} stocks to {filename}")
    return filename

def show_menu():
    """Display interactive menu"""
    df, csv_path = load_latest_results()
    
    if df is None:
        return
    
    print(f"\n✓ Loaded {len(df)} stocks from {Path(csv_path).name}")
    
    while True:
        print("\n" + "="*100)
        print("📊 S&P 500 GROWTH WATCHLIST MANAGER")
        print("="*100)
        print("\n1. Show top 20 opportunities")
        print("2. Show momentum leaders (5-day)")
        print("3. Filter by confidence level (80%+, 90%+, etc.)")
        print("4. Get technical summary for a stock")
        print("5. Export trading watchlist")
        print("6. Show statistics")
        print("7. Exit")
        print()
        
        choice = input("Select option (1-7): ").strip()
        
        if choice == '1':
            display_top_stocks(df, 20)
        elif choice == '2':
            show_momentum_leaders(df, 10)
        elif choice == '3':
            threshold = float(input("Enter confidence threshold (0-100): "))
            filtered = filter_by_confidence(df, threshold)
            print(f"\n✓ Found {len(filtered)} stocks with ≥{threshold}% confidence")
            print("\nTop 10:")
            for idx, (_, row) in enumerate(filtered.head(10).iterrows(), 1):
                print(f"  {idx:2d}. {row['Ticker']:<6} {row['Growth_Probability_%']:>6.1f}%")
        elif choice == '4':
            ticker = input("Enter ticker symbol: ").strip()
            show_technical_summary(df, ticker)
        elif choice == '5':
            threshold = float(input("Export stocks with ≥ confidence (default 75): ") or "75")
            export_trading_list(df, threshold)
        elif choice == '6':
            print("\n" + "="*100)
            print("📈 STATISTICS")
            print("="*100)
            print()
            print(f"  Total Stocks Analyzed: {len(df)}")
            print(f"  Average Confidence:    {df['Growth_Probability_%'].mean():.1f}%")
            print(f"  Highest Confidence:    {df['Growth_Probability_%'].max():.1f}%")
            print(f"  Lowest Confidence:     {df['Growth_Probability_%'].min():.1f}%")
            print()
            print(f"  Stocks ≥ 100%: {len(df[df['Growth_Probability_%'] == 100.0])}")
            print(f"  Stocks ≥ 90%:  {len(df[df['Growth_Probability_%'] >= 90])}")
            print(f"  Stocks ≥ 80%:  {len(df[df['Growth_Probability_%'] >= 80])}")
            print(f"  Stocks ≥ 70%:  {len(df[df['Growth_Probability_%'] >= 70])}")
            print(f"  Stocks ≥ 60%:  {len(df[df['Growth_Probability_%'] >= 60])}")
            print()
            print(f"  Avg 5-Day Momentum:    {df['Momentum_5d_%'].mean():+.2f}%")
            print(f"  Avg RSI:               {df['RSI'].mean():.1f}")
            print()
        elif choice == '7':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()
        df, csv_path = load_latest_results()
        
        if df is None:
            sys.exit(1)
        
        if command == 'top':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            display_top_stocks(df, limit)
        elif command == 'momentum':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_momentum_leaders(df, limit)
        elif command == 'filter':
            threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 80
            filtered = filter_by_confidence(df, threshold)
            print(f"\n✓ {len(filtered)} stocks with ≥{threshold}% confidence:")
            for _, row in filtered.iterrows():
                print(f"  {row['Ticker']:<6} {row['Growth_Probability_%']:>6.1f}%")
        elif command == 'summary':
            ticker = sys.argv[2] if len(sys.argv) > 2 else None
            if ticker:
                show_technical_summary(df, ticker)
            else:
                print("Usage: python sp500_watchlist_manager.py summary TICKER")
        elif command == 'export':
            threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 75
            export_trading_list(df, threshold)
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  top [limit]       - Show top stocks (default: 20)")
            print("  momentum [limit]  - Show momentum leaders (default: 10)")
            print("  filter [threshold] - Filter by confidence (default: 80)")
            print("  summary TICKER    - Get technical summary")
            print("  export [threshold] - Export watchlist (default: 75)")
    else:
        # Interactive menu
        show_menu()
