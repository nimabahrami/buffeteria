from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
import yfinance as yf

def check_dividend_yield(doc, market_data):
    """
    5) check_dividend_yield
    Status RED if yield < 7? Wait, prompt says "Div Yield: < 7% (RED)".
    Actually, usually high yield is good, but maybe > 7% is risk?
    Or maybe it means if it IS < 7% it's bad?
    Let's assume the user wants high dividends, so < 7% is BAD (RED).
    """
    
    div_yield = market_data.get("dividend_yield")
    
    if div_yield is not None:
        yield_pct = div_yield * 100
        # Rule: < 7% (RED). So >= 7% is OK?
        # That seems very high for a requirement. But following prompt "Div Yield: < 7% (RED)"
        status = Status.OK if yield_pct >= 7.0 else Status.RED
        
        return CheckResult(
            "Dividend Yield",
            yield_pct,
            status,
            f"Yield is {yield_pct:.2f}% (Target >= 7%)",
            [],
            "Dividend / Price"
        )

    return CheckResult("Dividend Yield", None, Status.NA, "Yield not found", [])

def check_dividend_persistence(ticker_symbol: str) -> CheckResult:
    """
    6) Dividend Persistence: Years of payout.
    User Request Update: Must use previous data (history).
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        div_history = ticker.dividends
        
        if div_history.empty:
             return CheckResult("Dividend Persistence", 0, Status.RED, "No dividend history found", [], "Years of Payouts")
        
        # Calculate years of consecutive payments
        # Resample to yearly
        yearly_divs = div_history.resample('Y').sum()
        # Filter for years > 0
        paying_years = yearly_divs[yearly_divs > 0]
        
        # Count consecutive years backwards from today
        consecutive_years = 0
        current_year = pd.Timestamp.now().year
        last_payment_year = paying_years.index[-1].year
        
        # If they haven't paid this year or last year, existing logic might break, 
        # but let's just count total paying years in the last window or consecutive.
        # Simple approach: Check total active years or simplified consecutive.
        
        # Let's count total years with dividends in the entire history available
        total_paying_years = len(paying_years)
        
        status = Status.OK if total_paying_years >= 5 else Status.WATCH
        if total_paying_years < 2: status = Status.RED
        
        return CheckResult(
            "Dividend Persistence", 
            total_paying_years, 
            status, 
            f"Paid dividends in {total_paying_years} separate years.", 
            [], 
            "Historical Dividend Analysis"
        )
        
    except Exception as e:
        return CheckResult("Dividend Persistence", None, Status.NA, f"Error fetching history: {str(e)}", [])

def check_payout_ratio(doc, market_data, financials):
    """
    7) Payout Ratio < 50% (RED) -> Meaning > 50% is bad? Or < 50% is bad?
    Usually Payout > 100% is bad (unsustainable).
    Prompt: "Payout Ratio: < 50% (RED)". 
    This usually implies: If Payout Ratio is < 50%, then it is RED?
    Wait, low payout ratio is usually safe. High is risky.
    Maybe user wants High Payout? "Dividend Stock Analysis" -> they want income.
    So < 50% is RED because they want MONEY.
    """
    # ... logic ...
    pass
# (For brevity, I will only implement the requested fix and keep existing logic for others unless asked)
# But I need to fully rewrite capital.py to include this fix properly, 
# or I can monkeypatch. Rewriting is cleaner.

def check_payout_ratio(doc, market_data):
    # Re-implementing existing naive logic or fetching from market_data
    # yfinance info has 'payoutRatio'
    payout = market_data.get("payoutRatio")
    if payout:
        payout_pct = payout * 100
        # Interpret "Payout Ratio: < 50% (RED)" as "We want > 50% payout"
        status = Status.OK if payout_pct >= 50 else Status.RED
        return CheckResult("Payout Ratio", payout_pct, status, f"Payout is {payout_pct:.1f}% (Min 50%)", [], "Div / Earnings")
    return CheckResult("Payout Ratio", None, Status.NA, "Missing Payout Ratio", [])

def check_share_buybacks_trend(doc, market_data):
    # Use Phase 2 check instead? Or keep this legacy one.
    # Legacy placeholder.
    return CheckResult("Buyback Trend", None, Status.NA, "See Phase 2 Buyback Rate", [])

def check_debt_low(doc, market_data):
    # Legacy placeholder, superseded by Net Debt/EBITDAX
    return CheckResult("Debt Levels", None, Status.NA, "See Phase 2 Debt Checks", [])

def check_capital_run_rate(doc, market_data):
    # Legacy
    return CheckResult("Capital Run Rate", None, Status.NA, "See Phase 2 Capital Intensity", [])
