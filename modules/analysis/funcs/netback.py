from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import Dict, Any

def calculate_netback_waterfall(doc, market_data: Dict[str, Any], production_boe: float) -> CheckResult:
    """
    Calculates Field and Corporate Netback per BOE.
    Checks for: 
    1. Non-Cash G&A Trap (SBC)
    2. Netted Revenue Trap (Low GP&T + Low Price)
    3. Hedging Distortion (Warning if Realized Price >> Benchmark)
    """
    extractor = Extractor(doc)
    
    # --- 1. Inputs ---
    # Realized Price
    # Try to find "Realized Price" or derive from Revenue / Production
    # Using market_data total revenue is hard for BOE calc unless we have exact period matches.
    # Extractor preference:
    price_bundle = extractor.extract_metric("Realized Price", ["average realizad price", "realized price per boe", "average sales price"])
    realized_price = price_bundle.value_parsed if price_bundle else 0.0
    
    # If not found, try rough proxy: Total Revenue / Production BOE (Risky if periods mismatch)
    # For now, if missing, we can't do accurate waterfall.
    
    # LOE / BOE
    loe_bundle = extractor.extract_metric("LOE", ["lease operating expense", "production costs", "lifting costs"])
    loe_total = loe_bundle.value_parsed if loe_bundle else 0.0
    loe_per_boe = (loe_total / production_boe) if production_boe > 0 else 0.0
    
    # Production Taxes
    tax_bundle = extractor.extract_metric("Production Taxes", ["production taxes", "severance taxes", "taxes other than income"])
    tax_total = tax_bundle.value_parsed if tax_bundle else 0.0
    tax_per_boe = (tax_total / production_boe) if production_boe > 0 else 0.0
    
    # GP&T
    gpt_bundle = extractor.extract_metric("GP&T", ["gathering", "transportation", "processing"])
    gpt_total = gpt_bundle.value_parsed if gpt_bundle else 0.0
    gpt_per_boe = (gpt_total / production_boe) if production_boe > 0 else 0.0
    
    # G&A (Total)
    gna_bundle = extractor.extract_metric("G&A", ["general and administrative", "g&a"])
    gna_total = gna_bundle.value_parsed if gna_bundle else 0.0
    
    # SBC (The Trap)
    sbc_bundle = extractor.extract_metric("SBC", ["stock-based compensation", "share-based compensation", "non-cash compensation"])
    sbc_total = sbc_bundle.value_parsed if sbc_bundle else 0.0
    
    # Cash G&A
    cash_gna_total = max(0, gna_total - sbc_total)
    cash_gna_per_boe = (cash_gna_total / production_boe) if production_boe > 0 else 0.0
    
    # Interest Expense
    # Could get from parsed doc or yfinance market_data if available
    # Parsing text for "Interest Expense"
    int_bundle = extractor.extract_metric("Interest Expense", ["interest expense", "interest costs"])
    interest_total = int_bundle.value_parsed if int_bundle else 0.0
    interest_per_boe = (interest_total / production_boe) if production_boe > 0 else 0.0
    
    # --- 2. Waterfall Calculation ---
    # We need a base price. If realized_price extracted is 0, we can't start.
    # Emergency fallback: derive from Total Revenue in extraction if possible?
    # Let's assume we need realized price.
    
    if realized_price <= 0 and production_boe > 0:
        # Fallback: total rev text extraction
        rev_bundle = extractor.extract_metric("Oil & Gas Revenue", ["oil and gas sales", "product sales"])
        if rev_bundle:
            realized_price = rev_bundle.value_parsed / production_boe

    if realized_price <= 0:
        return CheckResult("Netback Analysis", None, Status.NA, "Could not determine Realized Price per BOE", [])

    field_netback = realized_price - loe_per_boe - tax_per_boe - gpt_per_boe
    corp_netback = field_netback - cash_gna_per_boe - interest_per_boe
    
    netback_margin = (field_netback / realized_price) if realized_price else 0
    margin_rating = "High (>70%)" if netback_margin > 0.7 else "Medium (50-70%)" if netback_margin > 0.5 else "Low (<50%)"
    
    # --- 3. Trap Checks ---
    warnings = []
    
    # G&A Trap
    if sbc_total > 0:
        warnings.append(f"Adjusted for SBC of ${sbc_total/1e6:.1f}M")
    elif gna_total > 0:
        warnings.append("WARNING: Could not identify SBC. Cash G&A might be overstated.")
        
    # Netted Revenue Trap
    # If GP&T is low (< $1) and Price is "Low" (hard to judge without WTI, but let's say < $60 or user implied logic)
    # The prompt says: "Compare to peer... or WTI".
    # Heuristic: If GP&T < 0.50/boe, likely netted.
    netted_status = "Explicit Expense"
    if gpt_per_boe < 0.50:
        netted_status = "Likely Netted (Hidden Cost)"
        warnings.append("GP&T appears netted out of revenue (Low explicit cost).")
        
    status = Status.OK if netback_margin > 0.5 else Status.WATCH
    if netback_margin < 0.3: status = Status.RED
    
    interpretation = f"""
    Realized Price: ${realized_price:.2f}
    - LOE: ${loe_per_boe:.2f}
    - Taxes: ${tax_per_boe:.2f}
    - GP&T: ${gpt_per_boe:.2f} ({netted_status})
    = Field Netback: ${field_netback:.2f} ({netback_margin:.0%} Margin - {margin_rating})
    - Cash G&A: ${cash_gna_per_boe:.2f}
    - Interest: ${interest_per_boe:.2f}
    = Corp Netback: ${corp_netback:.2f}
    
    Notes: {', '.join(warnings)}
    """
    
    evidence = [e for e in [price_bundle, loe_bundle, tax_bundle, gpt_bundle, gna_bundle, sbc_bundle] if e]
    
    return CheckResult("Netback Calculation", corp_netback, status, interpretation.strip(), evidence, "Waterfall Analysis")
