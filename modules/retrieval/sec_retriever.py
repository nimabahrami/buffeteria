import os
from sec_edgar_downloader import Downloader
from typing import List, Optional
import glob

class SECRetriever:
    def __init__(self, download_dir: str = "data/filings", email: str = "user@example.com", company: str = "User"):
        """
        Initialize the SEC Retriever.
        
        Args:
            download_dir: Directory to save downloaded filings.
            email: User email required by SEC EDGAR API.
            company: User company/name required by SEC EDGAR API.
        """
        self.download_dir = download_dir
        # Standard SEC User-Agent format: 'AppName/Version (Company; Email)' or just 'Company Email'
        # The library generic Downloader takes 'company' and 'email'.
        self.downloader = Downloader(company, email, download_dir)

    def fetch_filings(self, ticker: str, filing_type: str = "10-K", amount: int = 1):
        """
        Fetch the latest filings for a given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'XOM').
            filing_type: Type of filing ('10-K', '10-Q').
            amount: Number of recent filings to download.
        """
        print(f"Fetching {amount} {filing_type}(s) for {ticker}...")
        try:
            count = self.downloader.get(filing_type, ticker, limit=amount)
            print(f"Successfully downloaded {count} filings.")
        except Exception as e:
            print(f"Error downloading filings: {e}")

    def get_filing_path(self, ticker: str, filing_type: str = "10-K") -> Optional[str]:
        """
        Get the path to the most recent downloaded filing.
        Presumes the structure: download_dir/sec-edgar-filings/TICKER/FILING_TYPE/ACCESSION_NUMBER/primary-document.html
        """
        # The library default structure:
        # {download_dir}/sec-edgar-filings/{ticker}/{filing_type}/{accession_number}/{primary_doc}
        
        # We need to find the specific path.
        base_path = os.path.join(self.download_dir, "sec-edgar-filings", ticker, filing_type)
        if not os.path.exists(base_path):
            return None
            
        # Get all accession folders
        accession_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        if not accession_dirs:
            return None
            
        # Sort by name (roughly corresponds to time, but imperfect) or modified time?
        # Better: basic alphabetical sort on accession usually works for "latest" if it's the standard format?
        # Actually, let's just pick the first one found or implement time checking.
        # For this MVP, we'll take the one with the latest creation time.
        
        latest_dir = max(accession_dirs, key=lambda d: os.path.getctime(os.path.join(base_path, d)))
        full_dir_path = os.path.join(base_path, latest_dir)
        
        # Find the .html or .txt file
        # Usually full-submission.txt or just the primary document.
        # The downloader usually grabs the primary HTML.
        html_files = glob.glob(os.path.join(full_dir_path, "*.html"))
        if html_files:
            return html_files[0] # Return the first HTML found
            
        txt_files = glob.glob(os.path.join(full_dir_path, "*.txt"))
        if txt_files:
            return txt_files[0]
            
        return None
