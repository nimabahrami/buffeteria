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
        """
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        soup = BeautifulSoup(html_content, "lxml")
        
        # Basic text extraction
        # Separator needs to be handled carefully to avoid merging words across lines
        full_text = soup.get_text(separator=" ", strip=True) 
        
        # TODO: Implement robust section detection (Item 1, Item 7, etc.)
        # For now, we return the full text.
        
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
