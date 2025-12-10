#!/usr/bin/env python3
"""
S&P 500 Growth Analysis HTML Report Generator
Converts CSV results to interactive HTML dashboard with filtering and sorting
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def load_latest_csv():
    """Load the most recent S&P 500 growth analysis CSV"""
    csv_files = list(Path('.').glob('sp500_growth_*.csv'))
    if not csv_files:
        print("❌ No CSV results found. Run 'python find_sp500_growth.py' first.")
        return None
    
    latest = max(csv_files, key=lambda p: p.stat().st_mtime)
    return pd.read_csv(latest), str(latest)

def generate_html(df, csv_filename):
    """Generate interactive HTML report"""
    
    # Calculate statistics
    total_stocks = len(df)
    avg_confidence = df['Growth_Probability_%'].mean()
    max_confidence = df['Growth_Probability_%'].max()
    high_confidence_count = len(df[df['Growth_Probability_%'] >= 90])
    very_high_count = len(df[df['Growth_Probability_%'] == 100.0])
    
    # Get top stocks
    top_stocks = df.nlargest(10, 'Growth_Probability_%')
    momentum_leaders = df.nlargest(10, 'Momentum_5d_%')
    
    # Prepare data for DataTable
    df_sorted = df.sort_values('Growth_Probability_%', ascending=False)
    table_data = []
    
    for idx, row in df_sorted.iterrows():
        table_data.append({
            'ticker': row['Ticker'],
            'price': f"${row['Current_Price']:.2f}",
            'prev_close': f"${row['Prev_Close']:.2f}",
            'change': f"{row['Change_%']:+.2f}%",
            'confidence': f"{row['Growth_Probability_%']:.1f}%",
            'momentum': f"{row['Momentum_5d_%']:+.2f}%",
            'rsi': f"{row['RSI']:.1f}",
            'vs_sma20': f"{row['vs_SMA20_%']:+.2f}%",
            'volatility': f"{row['Volatility_%']:.2f}%"
        })
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S&P 500 Growth Opportunities - {datetime.now().strftime('%B %d, %Y')}</title>
    <link href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        
        .timestamp {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        
        .stat-card.high {{
            border-left-color: #28a745;
        }}
        
        .stat-card.medium {{
            border-left-color: #ffc107;
        }}
        
        .stat-card.low {{
            border-left-color: #dc3545;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .stat-card.high .stat-value {{
            color: #28a745;
        }}
        
        .stat-card.medium .stat-value {{
            color: #ffc107;
        }}
        
        .stat-card.low .stat-value {{
            color: #dc3545;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #666;
            font-weight: 500;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        h2 {{
            color: #667eea;
            margin: 30px 0 20px 0;
            font-size: 1.5em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .top-picks {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .pick-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .pick-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }}
        
        .pick-rank {{
            font-size: 2em;
            font-weight: bold;
            opacity: 0.7;
            margin-bottom: 10px;
        }}
        
        .pick-ticker {{
            font-size: 1.8em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .pick-price {{
            font-size: 1.3em;
            margin: 10px 0;
            opacity: 0.9;
        }}
        
        .pick-stats {{
            font-size: 0.85em;
            opacity: 0.85;
            margin-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            padding-top: 15px;
        }}
        
        .pick-stat {{
            margin: 5px 0;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .search-box {{
            flex: 1;
            min-width: 200px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.2s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .filter-group {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e9ecef;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
            font-size: 0.9em;
        }}
        
        .filter-btn:hover {{
            border-color: #667eea;
            color: #667eea;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background: #5568d3;
        }}
        
        th.sorting::after {{
            content: ' ⇅';
        }}
        
        th.sorting_asc::after {{
            content: ' ↑';
        }}
        
        th.sorting_desc::after {{
            content: ' ↓';
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .ticker {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .confidence-100 {{
            background: #d4edda;
            color: #155724;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .confidence-90 {{
            background: #cfe2ff;
            color: #084298;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .confidence-80 {{
            background: #fff3cd;
            color: #664d03;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .confidence-70 {{
            background: #f8d7da;
            color: #842029;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .positive {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .negative {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .neutral {{
            color: #666;
        }}
        
        .rsi-overbought {{
            background: #ffebee;
            color: #c62828;
        }}
        
        .rsi-oversold {{
            background: #e8f5e9;
            color: #1b5e20;
        }}
        
        .rsi-neutral {{
            background: #fff9c4;
            color: #f57f17;
        }}
        
        footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e9ecef;
        }}
        
        .section-title {{
            margin-top: 40px;
            font-size: 1.3em;
            color: #667eea;
            font-weight: bold;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8em;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .top-picks {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 0.85em;
            }}
            
            th, td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📈 S&P 500 Growth Opportunities</h1>
            <p>Find the best stocks with 2%+ growth probability today</p>
            <div class="timestamp">
                Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card high">
                <div class="stat-label">Total Stocks</div>
                <div class="stat-value">{total_stocks}</div>
                <div class="stat-label">Analyzed</div>
            </div>
            <div class="stat-card high">
                <div class="stat-label">Average Confidence</div>
                <div class="stat-value">{avg_confidence:.1f}%</div>
                <div class="stat-label">Probability</div>
            </div>
            <div class="stat-card medium">
                <div class="stat-label">Maximum Confidence</div>
                <div class="stat-value">{max_confidence:.0f}%</div>
                <div class="stat-label">Top Signal</div>
            </div>
            <div class="stat-card high">
                <div class="stat-label">High Confidence</div>
                <div class="stat-value">{very_high_count}</div>
                <div class="stat-label">100% Signals</div>
            </div>
            <div class="stat-card high">
                <div class="stat-label">Above 90%</div>
                <div class="stat-value">{high_confidence_count}</div>
                <div class="stat-label">Strong Picks</div>
            </div>
        </div>
        
        <div class="content">
            <h2>🏆 Top 5 Picks Today</h2>
            <div class="top-picks">
"""
    
    for idx, (_, row) in enumerate(top_stocks.head(5).iterrows(), 1):
        html_content += f"""                <div class="pick-card">
                    <div class="pick-rank">#{idx}</div>
                    <div class="pick-ticker">{row['Ticker']}</div>
                    <div class="pick-price">${row['Current_Price']:.2f}</div>
                    <div class="pick-stats">
                        <div class="pick-stat">📊 Confidence: <strong>{row['Growth_Probability_%']:.1f}%</strong></div>
                        <div class="pick-stat">📈 Momentum: <strong>{row['Momentum_5d_%']:+.2f}%</strong></div>
                        <div class="pick-stat">🎯 RSI: <strong>{row['RSI']:.1f}</strong></div>
                        <div class="pick-stat">💹 Change: <strong>{row['Change_%']:+.2f}%</strong></div>
                    </div>
                </div>
"""
    
    html_content += """            </div>
            
            <h2>🚀 Momentum Leaders</h2>
            <div class="top-picks">
"""
    
    for idx, (_, row) in enumerate(momentum_leaders.head(5).iterrows(), 1):
        html_content += f"""                <div class="pick-card">
                    <div class="pick-rank">#{idx}</div>
                    <div class="pick-ticker">{row['Ticker']}</div>
                    <div class="pick-price">${row['Current_Price']:.2f}</div>
                    <div class="pick-stats">
                        <div class="pick-stat">📈 5D Momentum: <strong>{row['Momentum_5d_%']:+.2f}%</strong></div>
                        <div class="pick-stat">📊 Confidence: <strong>{row['Growth_Probability_%']:.1f}%</strong></div>
                        <div class="pick-stat">🎯 RSI: <strong>{row['RSI']:.1f}</strong></div>
                        <div class="pick-stat">📉 Volatility: <strong>{row['Volatility_%']:.2f}%</strong></div>
                    </div>
                </div>
"""
    
    html_content += f"""            </div>
            
            <div class="section-title">📋 Complete Stock Analysis</div>
            
            <div class="controls">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="🔍 Search by ticker or stats..." />
                </div>
                <div class="filter-group">
                    <button class="filter-btn active" onclick="filterTable('all')">All</button>
                    <button class="filter-btn" onclick="filterTable('100')">100%</button>
                    <button class="filter-btn" onclick="filterTable('90')">90%+</button>
                    <button class="filter-btn" onclick="filterTable('75')">75%+</button>
                </div>
            </div>
            
            <table id="resultsTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Ticker</th>
                        <th onclick="sortTable(1)">Price</th>
                        <th onclick="sortTable(2)">Change</th>
                        <th onclick="sortTable(3)">Confidence</th>
                        <th onclick="sortTable(4)">Momentum</th>
                        <th onclick="sortTable(5)">RSI</th>
                        <th onclick="sortTable(6)">vs SMA20</th>
                        <th onclick="sortTable(7)">Volatility</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for row in table_data:
        # Determine confidence badge color
        conf = float(row['confidence'].rstrip('%'))
        if conf == 100:
            conf_class = 'confidence-100'
        elif conf >= 90:
            conf_class = 'confidence-90'
        elif conf >= 80:
            conf_class = 'confidence-80'
        else:
            conf_class = 'confidence-70'
        
        # Determine change color
        change_val = float(row['change'].rstrip('%'))
        change_class = 'positive' if change_val > 0 else 'negative' if change_val < 0 else 'neutral'
        
        # Determine momentum color
        momentum_val = float(row['momentum'].rstrip('%'))
        momentum_class = 'positive' if momentum_val > 0 else 'negative' if momentum_val < 0 else 'neutral'
        
        # Determine RSI color
        rsi_val = float(row['rsi'])
        if rsi_val > 70:
            rsi_class = 'rsi-overbought'
        elif rsi_val < 30:
            rsi_class = 'rsi-oversold'
        else:
            rsi_class = 'rsi-neutral'
        
        html_content += f"""                    <tr>
                        <td><span class="ticker">{row['ticker']}</span></td>
                        <td>{row['price']}</td>
                        <td><span class="{change_class}">{row['change']}</span></td>
                        <td><span class="{conf_class}">{row['confidence']}</span></td>
                        <td><span class="{momentum_class}">{row['momentum']}</span></td>
                        <td><span class="{rsi_class}">{row['rsi']}</span></td>
                        <td>{row['vs_sma20']}</td>
                        <td>{row['volatility']}</td>
                    </tr>
"""
    
    html_content += f"""                </tbody>
            </table>
        </div>
        
        <footer>
            <p>📊 S&P 500 Growth Opportunity Analysis | {total_stocks} stocks analyzed | Generated {datetime.now().strftime('%B %d, %Y')}</p>
            <p>Data source: Yahoo Finance | Analysis: Technical Indicators (Momentum, RSI, SMA20, Volatility)</p>
            <p><strong>Disclaimer:</strong> This analysis is for informational purposes only. Always conduct your own due diligence before trading.</p>
        </footer>
    </div>
    
    <script>
        let currentSort = {{'column': 3, 'ascending': false}};
        let currentFilter = 'all';
        
        function filterTable(level) {{
            const rows = document.querySelectorAll('#resultsTable tbody tr');
            
            // Update active filter button
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            currentFilter = level;
            rows.forEach(row => {{
                const confidenceText = row.cells[3].textContent.trim();
                const confidence = parseFloat(confidenceText);
                
                let show = true;
                if (level !== 'all') {{
                    show = confidence >= parseFloat(level);
                }}
                
                row.style.display = show ? '' : 'none';
            }});
        }}
        
        function sortTable(column) {{
            const rows = Array.from(document.querySelectorAll('#resultsTable tbody tr'));
            const isAscending = currentSort.column === column ? !currentSort.ascending : false;
            
            rows.sort((a, b) => {{
                let aVal = a.cells[column].textContent.trim();
                let bVal = b.cells[column].textContent.trim();
                
                // Remove symbols and convert to number if possible
                aVal = aVal.replace(/[$%+]/g, '');
                bVal = bVal.replace(/[$%+]/g, '');
                
                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return isAscending ? aNum - bNum : bNum - aNum;
                }} else {{
                    return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }}
            }});
            
            const tbody = document.querySelector('#resultsTable tbody');
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
            
            currentSort = {{column, ascending: isAscending}};
        }}
        
        document.getElementById('searchInput').addEventListener('keyup', function(e) {{
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#resultsTable tbody tr');
            
            rows.forEach(row => {{
                const ticker = row.cells[0].textContent.toLowerCase();
                const matches = ticker.includes(searchTerm);
                row.style.display = matches ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    print("🔄 Generating HTML report...")
    
    result = load_latest_csv()
    if result is None:
        return
    
    df, csv_filename = result
    
    # Generate HTML
    html_content = generate_html(df, csv_filename)
    
    # Save HTML file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_filename = f"sp500_growth_{timestamp}.html"
    
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML report generated: {html_filename}")
    print(f"📊 Stocks analyzed: {len(df)}")
    print(f"📈 Average confidence: {df['Growth_Probability_%'].mean():.1f}%")
    print(f"\n💡 Open in browser: {html_filename}")

if __name__ == "__main__":
    main()
