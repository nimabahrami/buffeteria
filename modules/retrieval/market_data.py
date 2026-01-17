import yfinance as yf
from typing import Dict, Any, Optional, List
import pandas as pd

class MarketDataFetcher:
    def __init__(self):
        self.cache_file = "data/market_cache.json"

    def _load_cache(self) -> Dict[str, Any]:
        import json
        import os
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_cache(self, cache: Dict[str, Any]):
        import json
        import os
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"Failed to save market cache: {e}")

    def get_live_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch real-time metrics using live API calls.
        """
        stock = yf.Ticker(ticker)
        data = {}
        
        try:
            curr_price = None
            try:
                curr_price = stock.fast_info.last_price
            except:
                pass
                
            info = stock.info
            if not curr_price:
                curr_price = info.get("currentPrice") or info.get("regularMarketPrice")

            if curr_price: 
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

        except Exception as e:
            print(f"Live fetch failed for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            
        return {}

    def get_price_history(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """
        Fetch price history using live API calls.
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            print(f"History fetch failed for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
        
    def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches Income Statement, Balance Sheet, and Cash Flow using live API calls.
        """
        try:
            t = yf.Ticker(ticker)
            financials = {
                "income_statement": t.income_stmt,
                "balance_sheet": t.balance_sheet,
                "cash_flow": t.cashflow
            }
            return financials
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_volume_profile(self, ticker: str, period="1y", bins=50) -> List[Dict[str, Any]]:
        """
        Calculates Volume Profile (Volume by Price) for the given period.
        """
        # Uses get_price_history, so it inherits caching automatically!
        try:
            hist = self.get_price_history(ticker, period=period)
            if hist.empty:
                return []
            
            # Create price bins
            min_price = hist['Low'].min()
            max_price = hist['High'].max()
            if pd.isna(min_price) or pd.isna(max_price): return []
            
            price_range = max_price - min_price
            if price_range == 0: return []
            
            bin_size = price_range / bins
            
            # Simple approximation
            profile = {}
            for i in range(bins):
                profile[i] = 0
            
            for index, row in hist.iterrows():
                price = row['Close']
                if pd.isna(price): continue
                
                bin_idx = int((price - min_price) / bin_size)
                if bin_idx >= bins: bin_idx = bins - 1
                if bin_idx < 0: bin_idx = 0
                
                vol = row['Volume']
                if not pd.isna(vol):
                    profile[bin_idx] += vol
            
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
