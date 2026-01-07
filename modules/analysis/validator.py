from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
from .evidence import EvidenceBundle

class Status(Enum):
    OK = "OK"
    RED = "RED"
    WATCH = "WATCH" # For debt check mainly
    NA = "NA"
    REJECTED = "REJECTED"

@dataclass
class CheckResult:
    """
    Standard output format for all 18 analysis functions.
    """
    check_name: str
    value: Any
    status: Status
    interpretation: str
    evidence: List[EvidenceBundle] = field(default_factory=list)
    formula: str = ""
    errors_or_notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "check_name": self.check_name,
            "value": self.value,
            "status": self.status.value,
            "interpretation": self.interpretation,
            "formula": self.formula,
            "evidence": [e.to_dict() for e in self.evidence],
            "errors_or_notes": self.errors_or_notes
        }

def validate_industry(ticker: str, industry_data: str) -> bool:
    """
    Hard Constraint 1: Industry filter.
    Returns True if Oil & Gas, False otherwise.
    """
    # Placeholder simple check. In real app, check 'industry' field from 10-K or data provider.
    return "oil" in industry_data.lower() or "gas" in industry_data.lower() or "energy" in industry_data.lower()
