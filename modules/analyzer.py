from typing import Dict, List, Any
from .retrieval.cache_manager import CacheManager
from .retrieval.market_data import MarketDataFetcher
from .extraction.parser import SecHtmlParser
from .analysis.validator import validate_industry, CheckResult, Status
from .analysis.evidence import EvidenceLedger, EvidenceBundle
from .analysis.extractor import Extractor

# Import all checks
from .analysis.funcs import cost_structure, profitability, capital, operational, valuation

class Analyzer:
    def __init__(self):
        self.cache_manager = CacheManager()
        self.market_data_fetcher = MarketDataFetcher()
        self.parser = SecHtmlParser()

    def analyze_ticker(self, ticker: str) -> Dict[str, Any]:
        """
        Main entry point. Returns a dictionary with:
        - summary
        - scorecard (list of check results)
        - ledger (json str)
        """
        # 1. Standardize Ticker
        ticker = ticker.upper()

        # 2. Fetch Live Data
        market_data = self.market_data_fetcher.get_live_data(ticker)
        
        # 2. Fetch Documents
        documents = self.cache_manager.get_documents(ticker)
        if not documents:
             return {"error": "No documents found for ticker."}
             
        # 3. Parse Document (Assume 10-K is first)
        doc_path = documents[0]['path']
        parsed_doc = self.parser.parse(doc_path, documents[0]['doc_id'])
        
        # 4. Validations
        if not validate_industry(ticker, parsed_doc.full_text):
            return {"error": "REJECTED_NON_OIL_GAS: Industry check failed."}
            
        # 5. Extract Common Dependencies (Production)
        extractor = Extractor(parsed_doc)
        prod_bundle = extractor.extract_metric("Production (BOE)", ["total production", "average daily production", "production"])
        production_boe = prod_bundle.value_parsed if prod_bundle else 1.0 # Avoid div by zero, but tag warning?
        
        # 0. Fetch Financial Statements (New Phase 2 Requirement)
        financials = self.market_data_fetcher.get_financial_statements(ticker)

        # 6. Run Checks
        results: List[CheckResult] = []
        ledger = EvidenceLedger()
        
        # Cost Structure
        results.append(cost_structure.check_loe_per_boe(parsed_doc, production_boe))
        results.append(cost_structure.check_gathering_transport_per_boe(parsed_doc, production_boe))
        results.append(cost_structure.check_gna_per_boe(parsed_doc, production_boe))
        
        # New Phase 2 Checks (Structured Data Focus)
        from .analysis.funcs import phase2_checks
        results.append(phase2_checks.check_net_debt_ebitdax(market_data, financials))
        results.append(phase2_checks.check_buyback_rate(market_data, financials))
        results.append(phase2_checks.check_accounts_payable_change(financials))
        results.append(phase2_checks.check_capital_intensity(market_data, financials))
        results.append(phase2_checks.check_debt_payback(financials))
        # Note: GP&T Strict is covered by the updated cost_structure check, but we can add the standalone if desired.
        
        # Phase 3: Netback Analysis (Waterfall)
        from .analysis.funcs import netback
        results.append(netback.calculate_netback_waterfall(parsed_doc, market_data, production_boe))


        
        # Profitability
        results.append(profitability.check_operating_margin_per_boe(parsed_doc, production_boe))
        results.append(profitability.compute_roic(parsed_doc))
        results.append(profitability.compute_wacc(parsed_doc, market_data.get("market_cap")))
        # Need results from ROIC and WACC for Spread
        results.append(profitability.check_roic_minus_wacc_spread(results[-2], results[-1])) # Index -2 is ROIC, -1 is WACC
        
        # Capital
        from .analysis.funcs import capital_fixed
        results.append(capital_fixed.check_dividend_yield(parsed_doc, market_data))
        results.append(capital_fixed.check_dividend_persistence(ticker)) # Now passing ticker!
        results.append(capital_fixed.check_payout_ratio(parsed_doc, market_data))
        results.append(capital.check_share_buybacks_trend(parsed_doc))
        results.append(capital.check_debt_low(parsed_doc, market_data))
        results.append(capital.check_capital_run_rate(parsed_doc, production_boe))
        
        # Operational
        results.append(operational.check_ownership_pipelines_and_water(parsed_doc))
        results.append(operational.check_production_efficiency(parsed_doc, production_boe))
        results.append(operational.compute_recycle_ratio(parsed_doc))
        
        # Asset Quality (Buffetria)
        from .analysis.funcs import asset_quality
        results.append(asset_quality.check_asset_quality(parsed_doc, production_boe))

        
        # Valuation
        results.append(valuation.intrinsic_value_method_1_smog(parsed_doc, market_data))
        results.append(valuation.intrinsic_value_method_2_napkin(parsed_doc, market_data))
        
        # 7. Compile Ledger
        for res in results:
            for ev in res.evidence:
                ledger.add_entry(ev)
                
        # 8. Summary
        red_flags = len([r for r in results if r.status == Status.RED])
        score = len([r for r in results if r.status == Status.OK])
        summary = f"Analysis complete for {ticker}. Score: {score}/18 OK. Red Flags: {red_flags}."
        
        return {
            "summary": summary,
            "scorecard": [r.to_dict() for r in results],
            "ledger": ledger.get_ledger_json(),
            "ledger_list": ledger.to_list()
        }
