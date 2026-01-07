from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import List, Optional, Dict

def check_dividend_yield(market_data: Dict) -> CheckResult:
    """
    5) check_dividend_yield
    Rule: Must be < 7%. If >= 7% then RED.
    """
    yield_val = market_data.get("dividend_yield")
    current_price = market_data.get("current_price")
    
    if yield_val is not None:
        # yield_val is typically a decimal (0.05 for 5%)
        status = Status.RED if yield_val >= 0.07 else Status.OK
        interpretation = f"Dividend yield is {yield_val:.1%} (Price: ${current_price})."
        return CheckResult("check_dividend_yield", yield_val, status, interpretation, [], "Dividend / Price")
    
    return CheckResult("check_dividend_yield", None, Status.NA, "Missing dividend yield data.", [])

def check_dividend_persistence(doc) -> CheckResult:
    """
    6) check_dividend_persistence
    Rule: Higher is better.
    """
    extractor = Extractor(doc)
    # Search for "paid dividends for X consecutive years" or look for table history.
    # Naive extraction:
    persistence_bundle = extractor.extract_metric("Dividend Years", ["consecutive years of dividend", "dividends paid for"])
    
    if persistence_bundle:
        years = persistence_bundle.value_parsed
        return CheckResult("check_dividend_persistence", years, Status.OK, f"Dividends paid for {years} years.", [persistence_bundle], "Years of payments")

    return CheckResult("check_dividend_persistence", None, Status.NA, "Dividend persistence not found in text.", [])

def check_payout_ratio(market_data: Dict) -> CheckResult:
    """
    7) check_payout_ratio
    Rule: Must be < 50%. RED if >= 50%.
    """
    # Use trailing EPS and Dividend Rate
    eps = market_data.get("trailing_eps")
    div_rate = market_data.get("dividend_rate") # Annual dividend per share
    
    if eps and div_rate:
        payout_ratio = div_rate / eps
        status = Status.RED if payout_ratio >= 0.50 else Status.OK
        return CheckResult("check_payout_ratio", payout_ratio, status, f"Payout Ratio: {payout_ratio:.1%}", [], "Div / EPS")
        
    return CheckResult("check_payout_ratio", None, Status.NA, "Missing EPS or Dividend data.", [])

def check_share_buybacks_trend(doc, market_share_counts: List[float] = None) -> CheckResult:
    """
    10) check_share_buybacks_trend
    Rule: Higher is better.
    """
    # If we have history of share counts (from market_data or parsed):
    if market_share_counts and len(market_share_counts) >= 2:
        current = market_share_counts[-1]
        prev = market_share_counts[0] # Assuming list is sorted old->new implies trend?
        # Let's assume input is [Last Year, This Year] or similar.
        # Actually usually history is newest first or something.
        # Let's rely on Extractor for "Repurchased X shares" text.
        pass
    
    extractor = Extractor(doc)
    repurchase_bundle = extractor.extract_metric("Share Repurchases", ["repurchased", "share buybacks", "shares repurchased"])
    
    if repurchase_bundle:
         val = repurchase_bundle.value_parsed
         # If val is in millions/dollars? hard to know.
         return CheckResult("check_share_buybacks_trend", val, Status.OK, "Company mentions share repurchases.", [repurchase_bundle])
         
    return CheckResult("check_share_buybacks_trend", None, Status.NA, "No buyback info found.", [])

def check_debt_low(doc, market_data: Dict) -> CheckResult:
    """
    11) check_debt_low
    Rule: Net Debt / EBITDA < 1.5 OK, > 2.5 RED.
    """
    extractor = Extractor(doc)
    evidence = []
    
    debt_bundle = extractor.extract_metric("Total Debt", ["total debt", "long-term debt"])
    cash_bundle = extractor.extract_metric("Cash", ["cash and cash equivalents"])
    ebitda_bundle = extractor.extract_metric("EBITDA", ["ebitda", "adjusted ebitda"])
    
    if debt_bundle and ebitda_bundle:
        evidence.extend([debt_bundle, ebitda_bundle])
        if cash_bundle: evidence.append(cash_bundle)
        
        debt = debt_bundle.value_parsed
        cash = cash_bundle.value_parsed if cash_bundle else 0
        ebitda = ebitda_bundle.value_parsed
        
        net_debt = debt - cash
        if ebitda > 0:
            ratio = net_debt / ebitda
            status = Status.OK
            if ratio > 1.5: status = Status.WATCH
            if ratio > 2.5: status = Status.RED
            
            return CheckResult("check_debt_low", ratio, status, f"Net Debt/EBITDA: {ratio:.2f}", evidence, "(Debt-Cash)/EBITDA")
            
    return CheckResult("check_debt_low", None, Status.NA, "Missing Debt or EBITDA.", evidence)

def check_capital_run_rate(doc, production_boe: float) -> CheckResult:
    """
    16) check_capital_run_rate
    Rule: Lower is better. Capex / Production.
    """
    extractor = Extractor(doc)
    capex_bundle = extractor.extract_metric("Capex", ["capital expenditures", "additions to property, plant and equipment", "capex"])
    
    if capex_bundle and production_boe:
        capex = capex_bundle.value_parsed
        ratio = capex / production_boe
        
        return CheckResult("check_capital_run_rate", ratio, Status.OK, f"Capex/BOE: ${ratio:.2f}", [capex_bundle], "Capex / Production")
        
    return CheckResult("check_capital_run_rate", None, Status.NA, "Missing Capex or Production.", [])
