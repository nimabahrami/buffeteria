import yfinance as yf
from typing import Dict, Any, Optional, List
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
        
    def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches Income Statement, Balance Sheet, and Cash Flow.
        Returns a dict of DataFrames.
        """
        try:
            t = yf.Ticker(ticker)
            return {
                "income_statement": t.income_stmt,
                "balance_sheet": t.balance_sheet,
                "cash_flow": t.cashflow
            }
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return {}

    def get_volume_profile(self, ticker: str, period="1y", bins=50) -> List[Dict[str, Any]]:
        """
        Calculates Volume Profile (Volume by Price) for the given period.
        Returns list of dicts: {price_start, price_end, volume}
        """
        try:
            hist = self.get_price_history(ticker, period=period)
            if hist.empty:
                return []
            
            # Create price bins
            min_price = hist['Low'].min()
            max_price = hist['High'].max()
            price_range = max_price - min_price
            bin_size = price_range / bins
            
            # Simple approximation: Assign daily volume to the Close price bin
            # (More accurate would be distributing across High-Low, but this is fast)
            profile = {}
            for i in range(bins):
                profile[i] = 0
            
            for index, row in hist.iterrows():
                price = row['Close']
                bin_idx = int((price - min_price) / bin_size)
                if bin_idx >= bins: bin_idx = bins - 1
                profile[bin_idx] += row['Volume']
            
            result = []
            for i in range(bins):
                start = min_price + (i * bin_size)
                end = start + bin_size
                result.append({
                    "priceLevel": (start + end) / 2,
                    "volume": profile[i]
                })
                
            return result
        except Exception as e:
            print(f"Error calculating volume profile: {e}")
            return []
