import os
import json
from typing import List, Dict
from .sec_retriever import SECRetriever

class CacheManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.filings_dir = os.path.join(data_dir, "filings")
        self.retriever = SECRetriever(download_dir=data_dir) # Uses data/filings internally via the lib if configured
        
    def get_documents(self, ticker: str, force_update: bool = False) -> List[Dict]:
        """
        Get document paths for a ticker. Downloads if not present or force_update is True.
        Returns a list of dicts: {'doc_id': str, 'path': str, 'type': str}
        """
        # Check if we have a recent 10-K
        # For simplicity in this MVP, we verify if the folder exists and is not empty.
        # A robust version would check the submission date.
        
        doc_path_10k = self.retriever.get_filing_path(ticker, "10-K")
        
        if not doc_path_10k or force_update:
            self.retriever.fetch_filings(ticker, "10-K", amount=1)
            doc_path_10k = self.retriever.get_filing_path(ticker, "10-K")
            
        # We could also fetch 10-Q here if required.
        
        documents = []
        if doc_path_10k:
            documents.append({
                "doc_id": f"{ticker}_10K_latest",
                "path": doc_path_10k,
                "type": "10-K"
            })
            
        return documents
