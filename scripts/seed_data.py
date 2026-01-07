
import sys
import os
import time
import hashlib

# Add parent dir to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_nyse_energy_tickers
from modules.analyzer import Analyzer

def seed_all():
    tickers = get_nyse_energy_tickers()
    analyzer = Analyzer()
    
    print(f"Starting seeding for {len(tickers)} tickers...")
    
    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] Processing {ticker}...")
        
        try:
            # 1. Fetch/Cache Document
            # The analyzer's analyze_ticker method triggers document fetching via cache_manager
            # But we might want to call fetch directly to be sure.
            
            # Using analyze_ticker is safer as it exercises the whole pipeline
            # including live market data fetch.
            
            result = analyzer.analyze_ticker(ticker)
            
            if "error" in result:
                print(f"  X Error for {ticker}: {result['error']}")
            else:
                print(f"  + Success for {ticker}. Score: {result.get('summary')}")
                
            # Sleep to be polite to SEC and yfinance
            time.sleep(2) 
            
        except Exception as e:
            print(f"  ! Exception for {ticker}: {e}")
            
    print("Seeding complete.")

if __name__ == "__main__":
    seed_all()
