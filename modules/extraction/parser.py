from bs4 import BeautifulSoup
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Section:
    title: str
    content: str
    start_idx: int
    end_idx: int

@dataclass
class ParsedDocument:
    doc_id: str
    full_text: str
    sections: Dict[str, Section] = field(default_factory=dict)
    tables: List[str] = field(default_factory=list) # Placeholder for table extraction text
    
    def get_snippet(self, start: int, end: int) -> str:
        return self.full_text[start:end]

class SecHtmlParser:
    def __init__(self):
        pass
        
    def parse(self, file_path: str, doc_id: str) -> ParsedDocument:
        """
        Parses an SEC HTML file into a ParsedDocument.
        Fast extraction using regex instead of BeautifulSoup.
        """
        with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
            html_content = f.read()
        
        # Fast regex-based HTML tag removal
        import re
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode HTML entities
        import html
        text = html.unescape(text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        full_text = text.strip()
        
        parsed_doc = ParsedDocument(
            doc_id=doc_id,
            full_text=full_text,
            sections={} 
        )
        
        return parsed_doc

    def extract_tables(self, soup) -> List[str]:
        # Placeholder for table text extraction
        tables = []
        for table in soup.find_all("table"):
            tables.append(table.get_text(separator=" ", strip=True))
        return tables
