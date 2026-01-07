from flask import Flask, render_template, request, jsonify
from modules.analyzer import Analyzer
import pandas as pd
import yfinance as yf
import traceback

app = Flask(__name__)
analyzer = Analyzer()

# --- Helpers ---
def get_nyse_energy_tickers():
    # In a real production app, we might scrape a dynamic list or use an API.
    # For now, providing a comprehensive hardcoded list of major NYSE Energy/Oil stocks.
    return [
        "XOM", "CVX", "COP", "EOG", "OXY", "SLB", "PXD", "MPC", "PSX", "VLO", "WMB",
        "HES", "KMI", "BKR", "HAL", "DVN", "TRGP", "FANG", "CTRA", "MRO", "APA", "OVV",
        "CHK", "EQT", "SWN", "MTDR", "PR", "CIVI", "CHRD", "MUR", "SM", "CRK"
    ]

@app.route('/')
def index():
    return render_template('index.html', tickers=get_nyse_energy_tickers())

@app.route('/api/analyze')
def analyze():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
    
    try:
        # Run standard analysis
        report = analyzer.analyze_ticker(ticker)
        
        # Enhance with extra data for the frontend if needed
        # (e.g., specific chart data is fetched separately or included)
        return jsonify(report)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-data')
def market_data():
    ticker = request.args.get('ticker')
    period = request.args.get('period', '2y') # Default to 2y
    
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
    
    try:
        data = analyzer.market_data_fetcher.get_live_data(ticker)
        # Add historical price for chart
        hist = analyzer.market_data_fetcher.get_price_history(ticker, period=period)
        data['history'] = hist.reset_index().to_dict(orient='records')
        
        # Explicit EBITDA check from financials if 'ebitda' key is missing or None
        if not data.get('ebitda'):
            financials = analyzer.market_data_fetcher.get_financial_statements(ticker)
            inc = financials.get('income_statement')
            if inc is not None and not inc.empty:
                # Try to find EBITDA row
                # yfinance often keys it as "EBITDA" or "Normalized EBITDA"
                try:
                    ebitda_row = inc.loc['EBITDA']
                    if not ebitda_row.empty:
                        data['ebitda'] = ebitda_row.iloc[0] # Most recent
                except:
                    pass
                    
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8502)
