#!/usr/bin/env python
"""
Paper Trading with Configuration
Demonstrates how to use the config file for automated paper trading
"""

import asyncio
from src.config import load_config
from trade_with_ibkr import IBKRTradingBot
from src.ibkr_executor import RiskManager


async def main():
    """Main trading workflow with config"""
    
    # Load configuration
    config = load_config('config_paper_trading.ini')
    
    print("\n" + "="*80)
    print("PAPER TRADING SYSTEM WITH CONFIG".center(80))
    print("="*80 + "\n")
    
    # Display configuration
    config.print_summary()
    
    # Check if in dry run mode
    if config.dry_run_mode:
        print("\n⚠️  DRY RUN MODE ENABLED - No real trades will be placed\n")
    
    # Initialize trading bot with config values
    print("Initializing trading bot...\n")
    bot = IBKRTradingBot(
        account_size=config.account_size,
        max_risk_percent=config.max_risk_percent
    )
    
    # Get symbols to trade
    symbols = config.all_symbols
    if not symbols:
        print("No symbols configured. Adding default stocks...")
        symbols = config.get_symbols('stocks')[:3]
    
    print(f"Symbols to trade: {', '.join(symbols[:5])}")
    if len(symbols) > 5:
        print(f"  ... and {len(symbols) - 5} more symbols\n")
    
    # Trade each symbol
    results = []
    for symbol in symbols[:3]:  # Trade first 3 symbols as demo
        print(f"\n{'='*80}")
        print(f"Analyzing {symbol}...".center(80))
        print('='*80)
        
        try:
            # Generate prediction using config settings
            result = await bot.analyze_and_trade(
                symbol,
                min_confidence=config.min_confidence,
                dry_run=config.dry_run_mode
            )
            
            if result.get('success'):
                results.append({
                    'symbol': symbol,
                    'direction': result['direction'],
                    'confidence': result['confidence'],
                    'entry': result['entry'],
                    'stop_loss': result['stop_loss'],
                    'take_profit': result['take_profit']
                })
                print(f"\n✓ Analysis complete for {symbol}")
            else:
                print(f"\n✗ Analysis skipped for {symbol}: {result.get('message')}")
        
        except Exception as e:
            print(f"\n✗ Error analyzing {symbol}: {str(e)}")
    
    # Summary of results
    if results:
        print(f"\n\n{'='*80}")
        print("TRADING SUMMARY".center(80))
        print('='*80 + "\n")
        
        for r in results:
            print(f"{r['symbol']:8} | {r['direction']:6} | Conf: {r['confidence']:5.1f}% | "
                  f"Entry: ${r['entry']:.2f} | SL: ${r['stop_loss']:.2f} | TP: ${r['take_profit']:.2f}")
        
        print(f"\n{'='*80}\n")


async def run_single_symbol(symbol: str, config_file: str = 'config_paper_trading.ini'):
    """Run analysis for a single symbol"""
    
    config = load_config(config_file)
    bot = IBKRTradingBot(config.account_size, config.max_risk_percent)
    
    print(f"\n{'='*80}")
    print(f"Paper Trading: {symbol}".center(80))
    print('='*80 + "\n")
    
    result = await bot.analyze_and_trade(
        symbol,
        min_confidence=config.min_confidence,
        dry_run=config.dry_run_mode
    )
    
    if result.get('success'):
        print(f"\n{'='*80}")
        print(f"✓ Analysis Complete - {symbol}".center(80))
        print('='*80)
        print(f"""
Direction:         {result['direction']}
Confidence:        {result['confidence']:.1f}%
Entry:             ${result['entry']:.2f}
Stop Loss:         ${result['stop_loss']:.2f}
Take Profit:       ${result['take_profit']:.2f}
Quantity:          {result['quantity']} shares
Risk/Reward:       1:{result['trade_result'].get('risk_reward_ratio', 0):.2f}

Mode:              {"DRY RUN" if config.dry_run_mode else "LIVE"}
Account:           ${config.account_size:,.0f}
Max Risk:          {config.max_risk_percent}% (${config.account_size * config.max_risk_percent / 100:.2f})
""")
    else:
        print(f"\n✗ Analysis failed: {result.get('message')}")


async def compare_configs(config1: str, config2: str):
    """Compare two configurations"""
    
    c1 = load_config(config1)
    c2 = load_config(config2)
    
    print(f"\n{'='*80}")
    print("CONFIGURATION COMPARISON".center(80))
    print('='*80 + "\n")
    
    print(f"{'Setting':<30} | {config1:<20} | {config2:<20}")
    print("-" * 80)
    print(f"{'Account Size':<30} | ${c1.account_size:>18,.0f} | ${c2.account_size:>18,.0f}")
    print(f"{'Max Risk %':<30} | {c1.max_risk_percent:>18.1f}% | {c2.max_risk_percent:>18.1f}%")
    print(f"{'Min Confidence':<30} | {c1.min_confidence:>18.1f}% | {c2.min_confidence:>18.1f}%")
    print(f"{'Max Positions':<30} | {c1.max_positions:>18} | {c2.max_positions:>18}")
    print(f"{'Timeframe':<30} | {c1.timeframe:>20} | {c2.timeframe:>20}")
    print(f"{'Trading Mode':<30} | {c1.auto_trading_mode:>20} | {c2.auto_trading_mode:>20}")
    print(f"{'Dry Run':<30} | {str(c1.dry_run_mode):>20} | {str(c2.dry_run_mode):>20}")
    print(f"{'Symbols':<30} | {len(c1.all_symbols):>18} | {len(c2.all_symbols):>18}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'single' and len(sys.argv) > 2:
            # Trade single symbol
            symbol = sys.argv[2]
            asyncio.run(run_single_symbol(symbol))
        
        elif command == 'compare' and len(sys.argv) > 3:
            # Compare configs
            asyncio.run(compare_configs(sys.argv[2], sys.argv[3]))
        
        else:
            print("Usage:")
            print("  python trade_with_config.py                 # Run multi-symbol trading")
            print("  python trade_with_config.py single AAPL     # Trade single symbol")
            print("  python trade_with_config.py compare cfg1 cfg2  # Compare configs")
    else:
        # Run main multi-symbol trading
        asyncio.run(main())
