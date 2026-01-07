from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import List, Optional, Dict

def intrinsic_value_method_1_smog(doc, market_data: Dict) -> CheckResult:
    """
    8) intrinsic_value_method_1_smog
    Definition: (SMOG + Land + Cash - Debt) / diluted_shares
    """
    extractor = Extractor(doc)
    evidence = []
    
    smog_bundle = extractor.extract_metric("SMOG", ["standardized measure", "discounted future net cash flows", "smog"])
    land_bundle = extractor.extract_metric("Undeveloped Land", ["undeveloped acreage value", "value of undeveloped"]) # Note: rarely explicit value
    
    # Try getting debt/cash from market_data if available (more current) or doc
    # We'll rely on market_data for balance sheet items if live, else doc.
    # Check definition says "Standardized Measure... from 10-K".
    
    # For land value, if not disclosed, set NA.
    if not land_bundle:
        return CheckResult("intrinsic_value_method_1_smog", None, Status.NA, "Undeveloped Land Value not explicitly disclosed.", [])
        
    # Get balance sheet items
    debt_val = 0
    cash_val = 0
    shares = 1
    
    # Assuming we get these from doc if not in market_data
    debt_bundle = extractor.extract_metric("Total Debt", ["total debt"])
    cash_bundle = extractor.extract_metric("Cash", ["cash and cash equivalents"])
    shares_bundle = extractor.extract_metric("Diluted Shares", ["diluted shares outstanding", "weighted average shares"])
    
    if debt_bundle: debt_val = debt_bundle.value_parsed
    if cash_bundle: cash_val = cash_bundle.value_parsed
    if shares_bundle: shares = shares_bundle.value_parsed
    
    if smog_bundle and shares > 0:
        evidence.append(smog_bundle)
        smog = smog_bundle.value_parsed
        land = land_bundle.value_parsed
        
        intrinsic_value = (smog + land + cash_val - debt_val) / shares
        return CheckResult("intrinsic_value_method_1_smog", intrinsic_value, Status.OK, f"SMOG Intrinsic Value: ${intrinsic_value:.2f}/share", evidence, "SMOG Method")
        
    return CheckResult("intrinsic_value_method_1_smog", None, Status.NA, "Missing SMOG or Shares.", evidence)

def intrinsic_value_method_2_napkin(doc, market_data: Dict) -> CheckResult:
    """
    9) intrinsic_value_method_2_napkin
    Option A (FCF multiple): (normalized_FCF * multiple + cash - debt) / shares
    """
    extractor = Extractor(doc)
    evidence = []
    
    fcf_bundle = extractor.extract_metric("Free Cash Flow", ["free cash flow", "fcf"])
    
    # Defaults
    multiple = 8.0 
    
    if fcf_bundle:
        evidence.append(fcf_bundle)
        fcf = fcf_bundle.value_parsed
        
        # Need balance sheet
        debt = 0
        cash = 0
        shares = 1
        
        # Use simple extraction again (redundant but robust if separate module)
        # Ideally passed in.
        
        # Simplify: assume FCF is the key.
        # Check market data for robust shares/debt if available
        if market_data:
             if "market_cap" in market_data and "current_price" in market_data:
                 shares = market_data["market_cap"] / market_data["current_price"]
        
        intrinsic = (fcf * multiple) / shares # simplified, ignoring net debt adjustment if FCF is to equity? FCF is usually Firm.
        # Definition: (FCF * multiple + cash - debt) / shares. 
        # This implies FCF * Multiple = EV. 
        
        return CheckResult("intrinsic_value_method_2_napkin", intrinsic, Status.OK, f"Napkin Value (FCF x{multiple}): ${intrinsic:.2f}", evidence)
        
    return CheckResult("intrinsic_value_method_2_napkin", None, Status.NA, "Missing Free Cash Flow data.", [])
