from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import List, Optional, Dict, Any
import pandas as pd

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

def compute_roic(financials: Dict[str, Any], market_data: Dict[str, Any] = None, tax_rate: float = 0.21) -> CheckResult:
    """
    12) compute_roic
    Definition: ROIC = NOPAT / (Equity + Debt - Cash)
    Uses structured financial data from yfinance.
    """
    evidence = []
    
    try:
        income_stmt = financials.get('income_statement')
        balance_sheet = financials.get('balance_sheet')
        
        if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
            return CheckResult("compute_roic", None, Status.NA, "Missing financial statements", evidence)
        
        # Get Operating Income (EBIT)
        # yfinance keys: could be 'Operating Income', 'EBIT', 'Operating Revenue'
        operating_income = None
        for key in ['Operating Income', 'EBIT', 'Earnings Before Interest and Taxes']:
            if key in income_stmt.index:
                operating_income = income_stmt.loc[key].iloc[0]  # Most recent
                break
        
        # Get Total Equity
        total_equity = None
        for key in ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Total Stockholders\' Equity']:
            if key in balance_sheet.index:
                total_equity = balance_sheet.loc[key].iloc[0]
                break
        
        # Get Total Debt
        total_debt = None
        for key in ['Total Debt', 'Long Term Debt And Capital Lease Obligation', 'Net Debt']:
            if key in balance_sheet.index:
                total_debt = balance_sheet.loc[key].iloc[0]
                break
        
        # If total debt not found, try current + long term
        if total_debt is None or pd.isna(total_debt):
            current_debt = balance_sheet.loc['Current Debt'].iloc[0] if 'Current Debt' in balance_sheet.index else 0
            longterm_debt = balance_sheet.loc['Long Term Debt'].iloc[0] if 'Long Term Debt' in balance_sheet.index else 0
            if current_debt or longterm_debt:
                total_debt = (current_debt or 0) + (longterm_debt or 0)
        
        # Get Cash
        cash = None
        for key in ['Cash And Cash Equivalents', 'Cash', 'Cash Cash Equivalents And Short Term Investments']:
            if key in balance_sheet.index:
                cash = balance_sheet.loc[key].iloc[0]
                break
        
        # Validate all components exist
        if operating_income is None or pd.isna(operating_income):
            return CheckResult("compute_roic", None, Status.NA, "Operating Income not found", evidence)
        if total_equity is None or pd.isna(total_equity):
            return CheckResult("compute_roic", None, Status.NA, "Total Equity not found", evidence)
        if total_debt is None or pd.isna(total_debt):
            total_debt = 0  # Some companies have no debt
        if cash is None or pd.isna(cash):
            cash = 0
        
        # Calculate NOPAT and ROIC
        nopat = operating_income * (1 - tax_rate)
        invested_capital = total_equity + total_debt - cash
        
        if invested_capital <= 0:
            return CheckResult("compute_roic", None, Status.NA, "Invalid invested capital", evidence)
        
        roic = nopat / invested_capital
        
        interpretation = f"ROIC: {roic:.1%} (NOPAT: ${nopat/1e9:.2f}B / Invested Capital: ${invested_capital/1e9:.2f}B)"
        return CheckResult("compute_roic", roic, Status.OK, interpretation, evidence, "NOPAT / (Equity + Debt - Cash)")
        
    except Exception as e:
        return CheckResult("compute_roic", None, Status.NA, f"Error calculating ROIC: {str(e)}", evidence)

def compute_wacc(financials: Dict[str, Any], market_data: Dict[str, Any]) -> CheckResult:
    """
    13) compute_wacc
    WACC = (E/V) * Re + (D/V) * Rd * (1-T)
    Where:
    - E = Market Value of Equity (market cap)
    - D = Market Value of Debt (approximated by book value)
    - V = E + D
    - Re = Cost of Equity (CAPM: Rf + Beta * (Rm - Rf))
    - Rd = Cost of Debt (Interest Expense / Total Debt)
    - T = Tax Rate
    """
    evidence = []
    
    try:
        income_stmt = financials.get('income_statement')
        balance_sheet = financials.get('balance_sheet')
        
        if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
            return CheckResult("compute_wacc", None, Status.NA, "Missing financial statements", evidence)
        
        # Get Market Cap (Equity value)
        market_cap = market_data.get('market_cap')
        if not market_cap or market_cap <= 0:
            return CheckResult("compute_wacc", None, Status.NA, "Market cap not available", evidence)
        
        # Get Total Debt
        total_debt = None
        for key in ['Total Debt', 'Long Term Debt And Capital Lease Obligation', 'Net Debt']:
            if key in balance_sheet.index:
                total_debt = balance_sheet.loc[key].iloc[0]
                break
        
        if total_debt is None or pd.isna(total_debt):
            current_debt = balance_sheet.loc['Current Debt'].iloc[0] if 'Current Debt' in balance_sheet.index else 0
            longterm_debt = balance_sheet.loc['Long Term Debt'].iloc[0] if 'Long Term Debt' in balance_sheet.index else 0
            total_debt = (current_debt or 0) + (longterm_debt or 0)
        
        if total_debt is None or pd.isna(total_debt):
            total_debt = market_data.get('total_debt', 0)
        
        if total_debt is None:
            total_debt = 0
        
        # Get Interest Expense for Cost of Debt
        interest_expense = None
        for key in ['Interest Expense', 'Interest Expense Non Operating', 'Net Interest Income']:
            if key in income_stmt.index:
                interest_expense = abs(income_stmt.loc[key].iloc[0])  # Make positive
                break
        
        # Calculate Cost of Debt
        if interest_expense and total_debt > 0:
            cost_of_debt = interest_expense / total_debt
        else:
            cost_of_debt = 0.05  # Default 5% if can't calculate
        
        # Calculate Cost of Equity using CAPM
        # Re = Rf + Beta * (Rm - Rf)
        risk_free_rate = 0.045  # Current 10-year Treasury ~4.5%
        equity_risk_premium = 0.055  # Historical equity risk premium ~5.5%
        
        # Try to get beta from market data (yfinance provides this)
        beta = market_data.get('beta')
        if beta is None or pd.isna(beta):
            # Try to get from info
            import yfinance as yf
            try:
                ticker_symbol = market_data.get('symbol', 'XOM')  # Fallback
                stock = yf.Ticker(ticker_symbol)
                beta = stock.info.get('beta', 1.0)
            except:
                beta = 1.0  # Default to market beta
        
        if beta is None or pd.isna(beta) or beta <= 0:
            beta = 1.0
        
        cost_of_equity = risk_free_rate + beta * equity_risk_premium
        
        # Calculate Tax Rate
        tax_expense = None
        pretax_income = None
        for key in ['Tax Provision', 'Income Tax Expense']:
            if key in income_stmt.index:
                tax_expense = income_stmt.loc[key].iloc[0]
                break
        
        for key in ['Pretax Income', 'Income Before Tax']:
            if key in income_stmt.index:
                pretax_income = income_stmt.loc[key].iloc[0]
                break
        
        if tax_expense and pretax_income and pretax_income > 0:
            tax_rate = abs(tax_expense) / abs(pretax_income)
        else:
            tax_rate = 0.21  # Default corporate tax rate
        
        # Calculate WACC
        total_value = market_cap + total_debt
        
        weight_equity = market_cap / total_value
        weight_debt = total_debt / total_value
        
        wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
        
        interpretation = f"WACC: {wacc:.1%} (CoE: {cost_of_equity:.1%} @ {weight_equity:.0%}, CoD: {cost_of_debt:.1%} @ {weight_debt:.0%}, Beta: {beta:.2f})"
        return CheckResult("compute_wacc", wacc, Status.OK, interpretation, evidence, "WACC Formula")
        
    except Exception as e:
        return CheckResult("compute_wacc", None, Status.NA, f"Error calculating WACC: {str(e)}", evidence)

def check_roic_minus_wacc_spread(roic_result: CheckResult, wacc_result: CheckResult) -> CheckResult:
    """
    14) check_roic_minus_wacc_spread
    """
    if roic_result.status != Status.NA and wacc_result.status != Status.NA:
        spread = roic_result.value - wacc_result.value
        status = Status.OK if spread > 0 else Status.RED
        return CheckResult("check_roic_minus_wacc_spread", spread, status, f"Spread: {spread:.1%}", [], "ROIC - WACC")
        
    return CheckResult("check_roic_minus_wacc_spread", None, Status.NA, "Dependencies missing", [])
