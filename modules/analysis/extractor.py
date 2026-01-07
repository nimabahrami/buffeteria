import re
from typing import Optional, Tuple
from .evidence import EvidenceBundle

class Extractor:
    def __init__(self, doc):
        self.doc = doc

    def extract_metric(self, metric_name: str, keywords: list[str]) -> Optional[EvidenceBundle]:
        """
        Naive regex-based extraction for demonstration. 
        In a real production app, this would use an LLM or specific table parsing.
        """
        # Simple pattern: keyword ... number
        # We look for the keyword, then the next number.
        
        full_text = self.doc.full_text.lower()
        
        for k in keywords:
            pattern = re.compile(re.escape(k.lower()) + r"[:\s]+.*?(\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?)")
            match = pattern.search(full_text)
            if match:
                value_str = match.group(1)
                # Clean value
                value_clean = value_str.replace('$', '').replace(',', '')
                try:
                    value = float(value_clean)
                    
                    # Create snippet (context around match)
                    start = max(0, match.start() - 50)
                    end = min(len(full_text), match.end() + 50)
                    snippet = self.doc.full_text[start:end] # Get from original case text
                    
                    return EvidenceBundle(
                        doc_id=self.doc.doc_id,
                        section_title="Extracted via keywords",
                        exact_snippet=snippet,
                        value_parsed=value,
                        units="USD" # Default assumption, would need verification
                    )
                except ValueError:
                    continue
        
        return None
