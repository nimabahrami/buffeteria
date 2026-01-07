from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import List, Optional

def check_operating_margin_per_boe(doc, production_boe: float) -> CheckResult:
    """
    4) check_operating_margin_per_boe
    Definition: Operating margin per BOE = Realized oil price per BOE minus total cost per BOE.
    Rule: Higher is better.
    """
    extractor = Extractor(doc)
    evidence = []
    
    # 1. Get Realized Price
    realized_price_bundle = extractor.extract_metric("Realized Price", ["realized price", "average realized sales price", "average sales price"])
    # 2. Get Total Cost (LOE + G&T + Production Taxes + DD&A if specified)
    # This is hard to sum up without identifying all components.
    # For MVP, we search for "Total Operating Costs" or similar aggregate.
    total_cost_bundle = extractor.extract_metric("Total Operating Expenses", ["total operating expenses", "total costs and expenses"])
    
    val = None
    status = Status.NA
    interpretation = "Data missing for Operating Margin."
    
    if realized_price_bundle and total_cost_bundle and production_boe:
        evidence.append(realized_price_bundle)
        evidence.append(total_cost_bundle)
        
        realized_price = realized_price_bundle.value_parsed
        total_cost = total_cost_bundle.value_parsed
        
        # If realized price is total revenue, divide by BOE, unless it's per BOE
        # Usually realized price is reported per BOE or total revenue.
        # This ambiguity is risky. "Realized oil price per BOE" implies unit price.
        # Extractor naively gets a number. If > 1000, likely total. If < 200, likely per BOE.
        if realized_price > 200: # Heuristic for total revenue
            realized_price_per_boe = realized_price / production_boe
        else:
            realized_price_per_boe = realized_price
            
        if total_cost > 200:
            total_cost_per_boe = total_cost / production_boe
        else:
            total_cost_per_boe = total_cost
            
        operating_margin = realized_price_per_boe - total_cost_per_boe
        val = operating_margin
        status = Status.OK # Higher is better, no RED threshold specified, just "Higher is better"
        interpretation = f"Operating Margin: ${operating_margin:.2f}/BOE (Price: ${realized_price_per_boe:.2f} - Cost: ${total_cost_per_boe:.2f})"
        
    return CheckResult("check_operating_margin_per_boe", val, status, interpretation, evidence, "Realized Price/BOE - Total Cost/BOE")

def compute_roic(doc, tax_rate: float = 0.21) -> CheckResult:
    """
    12) compute_roic
    Definition: ROIC = NOPAT / (equity + debt - cash).
    """
    extractor = Extractor(doc)
    evidence = []
    
    op_income_bundle = extractor.extract_metric("Operating Income", ["operating income", "operating profit"])
    equity_bundle = extractor.extract_metric("Total Equity", ["total equity", "total stockholders' equity"])
    debt_bundle = extractor.extract_metric("Total Debt", ["total debt", "long-term debt", "debt"]) # Naive total debt
    cash_bundle = extractor.extract_metric("Cash", ["cash and cash equivalents", "cash"])
    
    if op_income_bundle and equity_bundle and debt_bundle:
        evidence.extend([op_income_bundle, equity_bundle, debt_bundle])
        if cash_bundle: evidence.append(cash_bundle)
        
        op_income = op_income_bundle.value_parsed
        equity = equity_bundle.value_parsed
        debt = debt_bundle.value_parsed
        cash = cash_bundle.value_parsed if cash_bundle else 0
        
        nopat = op_income * (1 - tax_rate)
        invested_capital = equity + debt - cash
        
        if invested_capital > 0:
            roic = nopat / invested_capital
            return CheckResult("compute_roic", roic, Status.OK, f"ROIC is {roic:.1%}", evidence, "NOPAT / (Equity + Debt - Cash)")

    return CheckResult("compute_roic", None, Status.NA, "Missing data for ROIC", evidence)

def compute_wacc(doc, market_cap: float = None) -> CheckResult:
    """
    13) compute_wacc
    This is highly variable. We will try to extract interest expense and debt to get cost of debt.
    Cost of equity is hard from just 10-K (needs beta).
    We will assume a default Cost of Equity of 10% if not found, or use user input? 
    Prompt: "Cost of equity (CAPM if inputs exist, otherwise document based guidance)"
    """
    extractor = Extractor(doc)
    evidence = []
    
    interest_bundle = extractor.extract_metric("Interest Expense", ["interest expense"])
    debt_bundle = extractor.extract_metric("Total Debt", ["total debt", "long-term debt"])
    
    cost_of_equity = 0.10 # Placeholder default
    cost_of_debt = 0.05 # Placeholder default
    
    if interest_bundle and debt_bundle and debt_bundle.value_parsed > 0:
        evidence.extend([interest_bundle, debt_bundle])
        cost_of_debt = interest_bundle.value_parsed / debt_bundle.value_parsed
        
    # WACC = E/V * Re + D/V * Rd * (1-T)
    # We need Market Cap (E) and Total Debt (D)
    
    # Ideally Market Cap comes from market_data.
    
    wacc = 0.08 # Fallback
    
    if market_cap and debt_bundle:
        d = debt_bundle.value_parsed
        e = market_cap
        v = d + e
        tax_rate = 0.21
        wacc = (e/v)*cost_of_equity + (d/v)*cost_of_debt*(1-tax_rate)
        return CheckResult("compute_wacc", wacc, Status.OK, f"WACC estimated at {wacc:.1%}", evidence, "Weighted Avg Cost of Capital")
        
    return CheckResult("compute_wacc", None, Status.NA, "Missing Market Cap or Debt for WACC", evidence)

def check_roic_minus_wacc_spread(roic_result: CheckResult, wacc_result: CheckResult) -> CheckResult:
    """
    14) check_roic_minus_wacc_spread
    """
    if roic_result.status != Status.NA and wacc_result.status != Status.NA:
        spread = roic_result.value - wacc_result.value
        status = Status.OK if spread > 0 else Status.RED
        return CheckResult("check_roic_minus_wacc_spread", spread, status, f"Spread: {spread:.1%}", [], "ROIC - WACC")
        
    return CheckResult("check_roic_minus_wacc_spread", None, Status.NA, "Dependencies missing", [])
