import yfinance as yf
from typing import Dict, Any, Optional
import pandas as pd

class MarketDataFetcher:
    def __init__(self):
        pass
        
    def get_live_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch real-time metrics that change frequently.
        """
        stock = yf.Ticker(ticker)
        curr_price = None
        try:
             curr_price = stock.fast_info.last_price
        except:
             pass
             
        info = stock.info
        if not curr_price:
             curr_price = info.get("currentPrice") or info.get("regularMarketPrice")

        data = {
            "current_price": curr_price,
            "market_cap": info.get("marketCap"),
            "trailing_eps": info.get("trailingEps"),
            "forward_eps": info.get("forwardEps"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_rate": info.get("dividendRate"),
            "dividend_yield": info.get("dividendYield"),
            "ex_dividend_date": info.get("exDividendDate"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "ebitda": info.get("ebitda"),
            "total_debt": info.get("totalDebt"),
            "total_cash": info.get("totalCash"),
            "operating_cashflow": info.get("operatingCashflow"),
            "free_cashflow": info.get("freeCashflow"),
            "shares_outstanding": info.get("sharesOutstanding")
        }
        return data

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
        
    def get_financial_statements(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch full financial statements (Income, Balance, Cash Flow).
        Returns dict of DataFrames.
        """
        stock = yf.Ticker(ticker)
        
        # yfinance returns DataFrames where index is the line item and columns are dates
        financials = {
            "income_statement": stock.financials, 
            "balance_sheet": stock.balance_sheet,
            "cash_flow": stock.cashflow
        }
        return financials
