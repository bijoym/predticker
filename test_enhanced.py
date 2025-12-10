#!/usr/bin/env python
"""Enhanced predictor multi-ticker analysis with comprehensive metrics and export."""

import csv
import sys
import argparse
from datetime import datetime
from src.enhanced_predictor import (
    fetch_4hour_data,
    compute_enhanced_features,
    enhanced_prediction,
    generate_trading_levels
)

def main(tickers=None, export_csv=True):
    """Run enhanced predictor analysis on multiple tickers.
    
    Args:
        tickers: List of ticker symbols (uses defaults if None)
        export_csv: Whether to export results to CSV file
    """
    if tickers is None:
        tickers = ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL']
    
    results = []

    print("=" * 100)
    print("ENHANCED PREDICTOR - MULTI-TICKER ANALYSIS")
    print("=" * 100)

    for ticker in tickers:
        try:
            df = fetch_4hour_data(ticker, days=90)
            features = compute_enhanced_features(df)
            result = enhanced_prediction(features)
            
            # Generate trading levels
            levels = generate_trading_levels(
                features['price'],
                result['prediction'],
                features['atr'],
                features
            )
            
            # Store results for summary table and export
            results.append({
                'ticker': ticker,
                'price': features['price'],
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'rsi': result['rsi'],
                'adx': result['adx'],
                'macd_histogram': result['macd_histogram'],
                'bb_position': result['bb_position'],
                'sl': levels['stop_loss'],
                'tp': levels['take_profit'],
                'sl_pct': levels['sl_percent'],
                'tp_pct': levels['tp_percent']
            })
            
            print(f"\n{ticker.upper()}")
            print(f"  {'─' * 96}")
            print(f"  Price: ${features['price']:.2f}")
            print(f"  Prediction: {result['prediction']:6s} | Confidence: {result['confidence']:5.1f}%")
            
            print(f"\n  Key Indicators:")
            print(f"    RSI:           {result['rsi']:6.1f} (30-70 normal range)")
            print(f"    ADX:           {result['adx']:6.1f} (Trend strength)")
            print(f"    MACD Histogram:{result['macd_histogram']:7.4f} (Momentum)")
            print(f"    BB Position:   {result['bb_position']*100:5.1f}% (0-100 within bands)")
            
            print(f"\n  Trading Levels ({result['prediction']}):")
            if result['prediction'] == 'Up':
                print(f"    Strategy:      LONG (Buy)")
                print(f"    Stop-Loss:     ${levels['stop_loss']:.2f} (-{levels['sl_percent']:.2f}%)")
                print(f"    Take-Profit:   ${levels['take_profit']:.2f} (+{levels['tp_percent']:.2f}%)")
            else:
                print(f"    Strategy:      SHORT (Sell)")
                print(f"    Stop-Loss:     ${levels['stop_loss']:.2f} (+{levels['sl_percent']:.2f}%)")
                print(f"    Take-Profit:   ${levels['take_profit']:.2f} (-{levels['tp_percent']:.2f}%)")
            
            print(f"\n  Signal Weights:")
            for key, value in result['weights'].items():
                print(f"    {key.replace('_', ' ').title():20s}: {value*100:5.1f}%")
            
        except Exception as e:
            print(f"\n{ticker.upper()}: ERROR - {str(e)}")
            results.append({
                'ticker': ticker,
                'price': None,
                'prediction': 'ERROR',
                'confidence': 0,
                'rsi': None,
                'adx': None,
                'macd_histogram': None,
                'bb_position': None,
                'sl': None,
                'tp': None,
                'sl_pct': None,
                'tp_pct': None
            })

    # Summary comparison table
    print("\n" + "=" * 100)
    print("SUMMARY COMPARISON TABLE")
    print("=" * 100)
    print(f"{'Ticker':<8} {'Price':<10} {'Pred':<6} {'Conf%':<8} {'RSI':<7} {'ADX':<7} {'MACD':<10} {'BB%':<7} {'SL':<10} {'TP':<10}")
    print("─" * 100)

    for r in results:
        if r['prediction'] != 'ERROR':
            print(f"{r['ticker']:<8} ${r['price']:<9.2f} {r['prediction']:<6} {r['confidence']:<7.1f}% {r['rsi']:<7.1f} {r['adx']:<7.1f} {r['macd_histogram']:<10.4f} {r['bb_position']*100:<7.1f} ${r['sl']:<9.2f} ${r['tp']:<9.2f}")
        else:
            print(f"{r['ticker']:<8} {'ERROR':<9} {'─':<6} {'─':<8} {'─':<7} {'─':<7} {'─':<10} {'─':<7} {'─':<10} {'─':<10}")

    # Export to CSV
    if export_csv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"multi_ticker_analysis_{timestamp}.csv"

        try:
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['Ticker', 'Price', 'Prediction', 'Confidence%', 'RSI', 'ADX', 'MACD_Histogram', 'BB_Position%', 'Stop_Loss', 'Take_Profit', 'SL_Percent', 'TP_Percent']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for r in results:
                    writer.writerow({
                        'Ticker': r['ticker'],
                        'Price': f"{r['price']:.2f}" if r['price'] else 'N/A',
                        'Prediction': r['prediction'],
                        'Confidence%': f"{r['confidence']:.1f}" if r['confidence'] else 'N/A',
                        'RSI': f"{r['rsi']:.1f}" if r['rsi'] else 'N/A',
                        'ADX': f"{r['adx']:.1f}" if r['adx'] else 'N/A',
                        'MACD_Histogram': f"{r['macd_histogram']:.4f}" if r['macd_histogram'] is not None else 'N/A',
                        'BB_Position%': f"{r['bb_position']*100:.1f}" if r['bb_position'] is not None else 'N/A',
                        'Stop_Loss': f"{r['sl']:.2f}" if r['sl'] else 'N/A',
                        'Take_Profit': f"{r['tp']:.2f}" if r['tp'] else 'N/A',
                        'SL_Percent': f"{r['sl_pct']:.2f}" if r['sl_pct'] else 'N/A',
                        'TP_Percent': f"{r['tp_pct']:.2f}" if r['tp_pct'] else 'N/A'
                    })
            print(f"\n✓ Results exported to: {csv_filename}")
        except Exception as e:
            print(f"\n✗ Failed to export CSV: {e}")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced predictor analysis for multiple tickers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_enhanced.py                           # Run on default 5 tickers
  python test_enhanced.py AAPL MSFT GOOGL          # Run on specific tickers
  python test_enhanced.py TSLA AMZN --no-csv       # Run without CSV export
        """
    )
    
    parser.add_argument(
        'tickers',
        nargs='*',
        help='Ticker symbols to analyze (space-separated). Default: AAPL MSFT TSLA AMZN GOOGL'
    )
    
    parser.add_argument(
        '--no-csv',
        action='store_true',
        help='Skip CSV export'
    )
    
    args = parser.parse_args()
    
    # Use provided tickers or defaults
    tickers_to_analyze = args.tickers if args.tickers else None
    export_csv = not args.no_csv
    
    main(tickers=tickers_to_analyze, export_csv=export_csv)
