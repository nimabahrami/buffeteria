from modules.analyzer import Analyzer
import json

def verify():
    print("Initializing Analyzer...")
    analyzer = Analyzer()
    
    ticker = "XOM" # Exxon Mobil as standard test
    print(f"Running analysis for {ticker}...")
    
    # Note: This might fail if network is blocked or dependencies missing.
    try:
        report = analyzer.analyze_ticker(ticker)
        
        if "error" in report:
            print(f"Analysis returned error: {report['error']}")
        else:
            print(f"Analysis Success!")
            print(f"Summary: {report['summary']}")
            print(f"Scorecard Items: {len(report['scorecard'])}")
            
            # Print first few checks
            for item in report["scorecard"][:3]:
                print(f"- {item['check_name']}: {item['status']} ({item['value']})")
                
            print("Ledger entries generated:", len(report['ledger_list']))
            
    except Exception as e:
        print(f"Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
