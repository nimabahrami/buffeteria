from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import List

def check_loe_per_boe(doc, production_boe: float) -> CheckResult:
    """
    1) check_loe_per_boe
    Definition: Lease Operating Expense per BOE (USD/BOE).
    Rule: Must be < 8. If >= 8 then RED.
    """
    extractor = Extractor(doc)
    # Keywords to search for LOE
    loe_bundle = extractor.extract_metric("Lease Operating Expense", ["lease operating expense", "production expense", "operating costs"])
    
    evidence = []
    if loe_bundle:
        evidence.append(loe_bundle)
        loe_total = loe_bundle.value_parsed
        
        # We need production_boe input. Assuming it's passed in or extracted separately?
        # The prompt says: "Every numeric input used... must come from the provided documents"
        # For this function to work, we need both LOE and Production.
        # Use the passed production_boe for calculation.
        
        if production_boe and production_boe > 0:
            loe_per_boe = loe_total / production_boe
            
            status = Status.OK if loe_per_boe < 8 else Status.RED
            interpretation = f"LOE per BOE is ${loe_per_boe:.2f}, which is {'below' if status == Status.OK else 'above'} the $8 threshold."
            
            return CheckResult(
                check_name="check_loe_per_boe",
                value=loe_per_boe,
                status=status,
                interpretation=interpretation,
                evidence=evidence,
                formula="Lease Operating Expense / Production (BOE)"
            )
    
    return CheckResult(
        check_name="check_loe_per_boe",
        value=None,
        status=Status.NA,
        interpretation="Could not extract Lease Operating Expense or Production data.",
        evidence=evidence
    )

def check_gathering_transport_per_boe(doc, production_boe: float) -> CheckResult:
    """
    2) check_gathering_transport_per_boe
    Definition: Gathering, Processing, Transportation per BOE (USD/BOE).
    Rule: Must be < 6. Lower is better.
    """
    extractor = Extractor(doc)
    gt_bundle = extractor.extract_metric("G&T Expense", ["gathering", "transportation", "processing", "gathering, processing and transportation"])
    
    evidence = []
    if gt_bundle:
        evidence.append(gt_bundle)
        gt_total = gt_bundle.value_parsed
        
        if production_boe and production_boe > 0:
            gt_per_boe = gt_total / production_boe
            status = Status.OK if gt_per_boe < 2.5 else Status.RED
            
            return CheckResult(
                check_name="check_gathering_transport_per_boe",
                value=gt_per_boe,
                status=status,
                interpretation=f"G&T per BOE is ${gt_per_boe:.2f} (Strict Limit < $2.50).",
                evidence=evidence,
                formula="G&T Expense / Production (BOE)"
            )

    return CheckResult(
        check_name="check_gathering_transport_per_boe",
        value=None,
        status=Status.NA,
        interpretation="Could not extract G&T Expense.",
        evidence=evidence
    )

def check_gna_per_boe(doc, production_boe: float) -> CheckResult:
    """
    3) check_gna_per_boe
    Definition: General and Administrative expense per BOE (USD/BOE).
    Rule: Must be < 3. Lower is better.
    """
    extractor = Extractor(doc)
    gna_bundle = extractor.extract_metric("G&A Expense", ["general and administrative", "g&a"])
    
    evidence = []
    if gna_bundle:
        evidence.append(gna_bundle)
        gna_total = gna_bundle.value_parsed
        
        if production_boe and production_boe > 0:
            gna_per_boe = gna_total / production_boe
            status = Status.RED if gna_per_boe >= 3 else Status.OK
            
            return CheckResult(
                check_name="check_gna_per_boe",
                value=gna_per_boe,
                status=status,
                interpretation=f"G&A per BOE is ${gna_per_boe:.2f}.",
                evidence=evidence,
                formula="G&A Expense / Production (BOE)"
            )

    return CheckResult(
        check_name="check_gna_per_boe",
        value=None,
        status=Status.NA,
        interpretation="Could not extract G&A Expense.",
        evidence=evidence
    )
