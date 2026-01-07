import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class EvidenceBundle:
    """
    Standardized verifiable reference bundle for every extracted value.
    Input for auditability.
    """
    row_id: str = field(default_factory=lambda: hashlib.sha256().hexdigest()[:8])
    doc_id: str = "unknown"
    section_title: str = "unknown"
    locator: str = "unknown"  # page number or parsing path
    exact_snippet: str = ""
    snippet_hash: str = ""
    value_parsed: Any = None
    units: str = ""
    
    def __post_init__(self):
        # Compute SHA256 of the snippet if not provided
        if self.exact_snippet and not self.snippet_hash:
            self.snippet_hash = hashlib.sha256(self.exact_snippet.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "doc_id": self.doc_id,
            "section_title": self.section_title,
            "locator": self.locator,
            "exact_snippet": self.exact_snippet,
            "snippet_hash": self.snippet_hash,
            "value_parsed": self.value_parsed,
            "units": self.units
        }

class EvidenceLedger:
    """
    Machine-readable ledger to store all EvidenceBundles for the user to audit.
    """
    def __init__(self):
        self.entries: List[EvidenceBundle] = []

    def add_entry(self, entry: EvidenceBundle):
        self.entries.append(entry)

    def get_ledger_json(self) -> str:
        return json.dumps([e.to_dict() for e in self.entries], indent=2)

    def to_list(self) -> List[Dict]:
        return [e.to_dict() for e in self.entries]
