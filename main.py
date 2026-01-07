import streamlit as st
import pandas as pd
import altair as alt
from modules.analyzer import Analyzer

def apply_bloomberg_style():
    """
    Inject CSS for Bloomberg Terminal Aesthetic.
    Colors: Black background, Orange (#FF9900) text for headers, White/Green for data.
    Font: Monospace/Roboto Mono.
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
        
        .stApp {
            background-color: #000000;
            color: #E0E0E0;
            font-family: 'Roboto Mono', monospace;
        }
        
        /* Headers */
        h1, h2, h3, h4 {
            color: #FF9900 !important;
            font-family: 'Roboto Mono', monospace;
            text-transform: uppercase;
        }
        
        /* Metrics */
        .stMetric {
            background-color: #1A1A1A;
            border: 1px solid #333;
            padding: 10px;
        }
        .stMetric label {
            color: #FF9900 !important;
        }
        .stMetric div[data-testid="stMetricValue"] {
            color: #00FF00 !important; /* Green for data */
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #111111;
        }
        
        /* Buttons */
        div.stButton > button {
            background-color: #FF9900;
            color: black;
            font-weight: bold;
            border-radius: 0px; /* Square terminal look */
            border: none;
        }
        div.stButton > button:hover {
            background-color: #CC7A00;
            color: white;
        }
        
        /* Tables/Dataframes */
        .stDataFrame {
            border: 1px solid #333;
        }
        
        /* Status Tags */
        .status-ok { color: #00FF00; font-weight: bold; }
        .status-red { color: #FF0000; font-weight: bold; }
        .status-watch { color: #FFFF00; font-weight: bold; }
        
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="ANTIGRAVITY TERMINAL", 
        page_icon="📟", # Vintage computer icon
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_bloomberg_style()

    st.title("ANTIGRAVITY TERMINAL // O&G ANALYZER")
    st.markdown("`SECURE CONNECTION ESTABLISHED...`")
    
    # Sidebar: Dropdown Configuration
    st.sidebar.header(">> COMMAND CENTER")
    
    # Pre-defined list of Oil & Gas majors
    og_tickers = ["XOM", "CVX", "COP", "EOG", "PXD", "OXY", "HES", "DVN", "MRO", "BP", "SHEL", "TTE", "EQNR"]
    ticker = st.sidebar.selectbox("SELECT TICKER", og_tickers)
    
    st.sidebar.write("---")
    st.sidebar.caption("DATA SOURCES:")
    st.sidebar.text("[x] INCOME STATEMENT")
    st.sidebar.text("[x] BALANCE SHEET")
    st.sidebar.text("[x] CASH FLOW")
    st.sidebar.text("[x] SEC 10-K (TEXT)")
    st.sidebar.text("[ ] EARNINGS CALL (AUDIO)")
    
    analyzer = Analyzer()

    if st.sidebar.button("EXECUTE ANALYSIS"):
        st.write(f"> INITIATING SEQUENCE FOR {ticker}...")
        
        try:
            with st.spinner('FETCHING LIVE DATA STREAMS...'):
                report = analyzer.analyze_ticker(ticker)
                
            if "error" in report:
                st.error(f"ERROR: {report['error']}")
            else:
                # --- Dashboard Layout ---
                # Top Row: Price & Macro
                market_data = analyzer.market_data_fetcher.get_live_data(ticker)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("LAST PRICE", f"${market_data.get('current_price', 0):.2f}")
                col2.metric("MARKET CAP", f"${(market_data.get('market_cap', 0)/1e9):.1f}B")
                col3.metric("P/E RATIO", f"{market_data.get('trailing_pe', 0):.1f}x")
                col4.metric("DIV YIELD", f"{(market_data.get('dividend_yield', 0)*100):.2f}%" if market_data.get('dividend_yield') else "N/A")
                
                st.write("---")
                
                # Main Split
                c_left, c_right = st.columns([2, 1])
                
                with c_left:
                    st.subheader(">> PRICE ACTION (1Y)")
                    hist = analyzer.market_data_fetcher.get_price_history(ticker)
                    if not hist.empty:
                        # Chart styling: Green line on black
                        chart = alt.Chart(hist.reset_index()).mark_line(color='#00FF00', strokeWidth=2).encode(
                            x=alt.X('Date', axis=alt.Axis(labelColor='#E0E0E0', titleColor='#FF9900')),
                            y=alt.Y('Close', axis=alt.Axis(labelColor='#E0E0E0', titleColor='#FF9900'), scale=alt.Scale(zero=False)),
                            tooltip=['Date', 'Close', 'Volume']
                        ).properties(height=350, background='#000000')
                        st.altair_chart(chart, use_container_width=True)
                
                with c_right:
                    st.subheader(">> SYSTEM STATUS")
                    st.info(report["summary"].upper())
                    
                    # Mini Gauge
                    import re
                    score_match = re.search(r"Score: (\d+)/18", report["summary"])
                    score = int(score_match.group(1)) if score_match else 0
                    st.progress(score/18.0)
                    st.caption(f"CONFIDENCE: {int((score/18)*100)}%")

                # --- Scorecard "Terminal" View ---
                st.write("---")
                st.subheader(">> DIAGNOSTIC SCORECARD")
                
                scorecard_df = pd.DataFrame(report["scorecard"])
                # Clean up for display
                display_df = scorecard_df[['check_name', 'value', 'status', 'interpretation']].copy()
                display_df.columns = ['CHECK', 'VALUE', 'STATUS', 'DETAILS']
                
                # Custom HTML table implementation for full terminal control
                for index, row in display_df.iterrows():
                    status_color = "#00FF00" if row['STATUS'] == "OK" else "#FF0000" if row['STATUS'] == "RED" else "#FFFF00"
                    
                    st.markdown(f"""
                    <div style="border-bottom: 1px dashed #333; padding: 5px; font-family: 'Roboto Mono', monospace;">
                        <span style="color: #888;">{row['CHECK'].upper()}</span>
                        <span style="float: right; color: {status_color}; font-weight: bold;">[{row['STATUS']}]</span>
                        <br>
                        <span style="color: #E0E0E0;">{str(row['VALUE'])[:10]}</span> | 
                        <span style="color: #AAA; font-size: 0.9em;">{row['DETAILS']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("---")
                st.subheader(">> EVIDENCE LEDGER")
                st.json(report["ledger_list"], expanded=False)

        except Exception as e:
            st.error(f"SYSTEM FAILURE: {e}")
            st.exception(e)

if __name__ == "__main__":
    main()
