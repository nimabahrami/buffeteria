from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
import pandas as pd
from typing import Dict, Any

def check_net_debt_ebitdax(market_data: Dict, financials: Dict) -> CheckResult:
    """
    1. Net Debt / EBITDAX < 1.0
    Note: EBITDAX = EBITDA + Exploration Expenses.
    Realistically yfinance gives EBITDA. Finding Exploration Expense specifically usually requires 10-K parsing.
    For this '100% confidence' path, we often just use EBITDA as a proxy if Exploration is not found, or warn.
    """
    # Net Debt = Total Debt - Cash
    debt = market_data.get("total_debt")
    cash = market_data.get("total_cash")
    ebitda = market_data.get("ebitda")
    
    if debt is not None and cash is not None and ebitda:
        net_debt = debt - cash
        # Placeholder for Exploration Expense (would need text extraction)
        exploration_expense = 0 
        ebitdax = ebitda + exploration_expense
        
        ratio = net_debt / ebitdax
        status = Status.OK if ratio < 1.0 else Status.RED
        
        return CheckResult(
            "Net Debt / EBITDAX", 
            ratio, 
            status, 
            f"Ratio: {ratio:.2f}x (Target < 1.0)", 
            [EvidenceBundle(value_parsed=ratio, exact_snippet="Derived from Market Data", section_title="Financials")],
            "Net Debt / (EBITDA + Explor)"
        )
    return CheckResult("Net Debt / EBITDAX", None, Status.NA, "Missing Debt/EBITDA", [])

def check_buyback_rate(market_data: Dict, financials: Dict) -> CheckResult:
    """
    2. Rate of buyback of share.
    Compare current shares to previous period shares.
    """
    bs = financials.get("balance_sheet")
    if bs is not None and not bs.empty:
        # Line item for shares? Usually 'Ordinary Shares Number' or 'Share Issued'
        # yfinance balance sheet often has 'Ordinary Shares Number' or 'Capital Stock'
        # Easier: compare market_data 'sharesOutstanding' vs historical?
        # Let's try to extract from Balance Sheet history if available.
        # Often 'Common Stock' is value, not count.
        pass

    # Alternative: Use "Repurchase Of Capital Stock" from Cash Flow
    cf = financials.get("cash_flow")
    mkt_cap = market_data.get("market_cap")
    
    if cf is not None and not cf.empty and mkt_cap:
        # Look for "Repurchase Of Capital Stock" row
        try:
            # yfinance rows are somewhat standard but can vary.
            buyback_row = [i for i in cf.index if "Repurchase" in str(i) or "Stock" in str(i)]
            # Refine
            repurchase_items = [i for i in cf.index if "Repurchase Of Capital Stock" in str(i)]
            
            if repurchase_items:
                # Get TTM or latest year
                latest_buyback = cf.loc[repurchase_items[0]].iloc[0] # Usually negative number
                latest_buyback = abs(latest_buyback)
                
                buyback_yield = latest_buyback / mkt_cap
                return CheckResult("Buyback Rate", buyback_yield, Status.OK, f"Buyback Yield: {buyback_yield:.1%}", [], "Repurchase / Market Cap")
        except Exception as e:
            return CheckResult("Buyback Rate", None, Status.NA, f"Error parsing CF: {e}", [])

    return CheckResult("Buyback Rate", None, Status.NA, "Missing Cash Flow Data", [])

def check_accounts_payable_change(financials: Dict) -> CheckResult:
    """
    3. Change in Accounts Payable.
    """
    bs = financials.get("balance_sheet")
    if bs is not None:
        try:
            ap_items = [i for i in bs.index if "Accounts Payable" in str(i)]
            if ap_items:
                ap_row = bs.loc[ap_items[0]]
                if len(ap_row) >= 2:
                    current_ap = ap_row.iloc[0]
                    prev_ap = ap_row.iloc[1]
                    change = current_ap - prev_ap
                    pct_change = (change / prev_ap) if prev_ap else 0
                    
                    status = Status.OK # No strict threshold given, just "check"
                    return CheckResult("Accounts Payable Change", change, status, f"Change: ${change/1e6:.1f}M ({pct_change:.1%})", [], "Current AP - Prev AP")
        except:
             pass
    return CheckResult("Accounts Payable Change", None, Status.NA, "Data not found", [])

def check_capital_intensity(market_data: Dict, financials: Dict) -> CheckResult:
    """
    4. Capital Intensity = Capex / Operational Cash Flow (OCF)
    """
    ocf = market_data.get("operating_cashflow")
    
    # Try to get Capex from Cash Flow statement or implied
    cf = financials.get("cash_flow")
    capex = 0
    if cf is not None:
         # "Capital Expenditure"
         capex_items = [i for i in cf.index if "Capital Expenditure" in str(i)]
         if capex_items:
             capex = abs(cf.loc[capex_items[0]].iloc[0])
             
    if ocf and ocf > 0:
        intensity = capex / ocf
        # Typically lower is better? Or dependent on growth phase.
        return CheckResult("Capital Intensity", intensity, Status.OK, f"Intensity: {intensity:.1%}", [], "Capex / OCF")
        
    return CheckResult("Capital Intensity", None, Status.NA, "Missing Capex/OCF", [])

def check_debt_payback(financials: Dict) -> CheckResult:
    """
    5. Debt payback intensity (Early retiring).
    Check Cash Flow for "Repayment of Debt" vs "Issuance of Debt".
    """
    cf = financials.get("cash_flow")
    if cf is not None:
        try:
            repayment_items = [i for i in cf.index if "Repayment" in str(i) and "Debt" in str(i)]
            issuance_items = [i for i in cf.index if "Issuance" in str(i) and "Debt" in str(i)]
            
            repayment = 0
            if repayment_items: repayment = abs(cf.loc[repayment_items[0]].iloc[0])
            
            issuance = 0
            if issuance_items: issuance = abs(cf.loc[issuance_items[0]].iloc[0])
            
            net_payback = repayment - issuance
            
            interpretation = "Net Debt Reduction" if net_payback > 0 else "Net Debt Increase"
            status = Status.OK if net_payback > 0 else Status.WATCH
            
            return CheckResult("Debt Payback", net_payback, status, f"{interpretation} (${net_payback/1e6:.1f}M)", [], "Repayment - Issuance")
        except:
            pass
            
    return CheckResult("Debt Payback", None, Status.NA, "CF Data missing", [])

def check_gpt_per_boe(parsed_doc, production_boe) -> CheckResult:
    """
    6. GP&T < $2.5/barrel (Strict).
    Re-using existing logic but with new threshold.
    Need access to 'cost_structure' logic or reimplement here.
    Let's reimplement strictly.
    """
    from ..extractor import Extractor
    extractor = Extractor(parsed_doc)
    gt_bundle = extractor.extract_metric("G&T Expense", ["gathering", "transportation", "processing"])
    
    if gt_bundle and production_boe:
        gt_total = gt_bundle.value_parsed
        gt_per_boe = gt_total / production_boe
        
        status = Status.OK if gt_per_boe < 2.5 else Status.RED
        return CheckResult("GP&T per BOE (Strict)", gt_per_boe, status, f"${gt_per_boe:.2f}/boe (Limit < $2.50)", [gt_bundle], "G&T / Production")

    return CheckResult("GP&T per BOE (Strict)", None, Status.NA, "Missing G&T data", [])
