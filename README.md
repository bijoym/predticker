# Market Predictor (demo)

This is a small demo Python project that fetches recent data from Yahoo Finance and predicts whether a share will go up or down in the short term using a simple rule-based approach (optionally extendable to ML).

Features
- Fetch last ~20 minutes of 1-minute data from Yahoo Finance
- Compute 20-day and 50-day simple moving averages (SMA)
- Rule-based prediction using SMA relationship and recent momentum
- Suggest stop-loss (5%) and take-profit (10%) levels
- Plot recent price series and annotate prediction and levels

Requirements
- Python 3.9+
- Install packages:

```pwsh
python -m pip install -r requirements.txt
```

Usage

```pwsh
pwsh> python -m src.predictor --ticker AAPL
```

This opens a plot of the last minutes of intraday price data, prints a prediction (`Up` / `Down`), and shows suggested stop-loss and take-profit levels.

Notes
- This is a demo and not financial advice. The prediction is rule-based for transparency; you can extend it with ML training on historical intraday labels.
