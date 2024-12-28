import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from phi.agent.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.googlesearch import GoogleSearch
import yfinance as yf

# Get API key from Streamlit secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# Stock symbol mappings
COMMON_STOCKS = {
    'NVIDIA': 'NVDA',
    'APPLE': 'AAPL',
    'GOOGLE': 'GOOGL',
    'MICROSOFT': 'MSFT',
    'TESLA': 'TSLA',
    'TCS': 'TCS.NS',
    'RELIANCE': 'RELIANCE.NS',
    'INFOSYS': 'INFY.NS',
    'WIPRO': 'WIPRO.NS',
    'HDFC': 'HDFCBANK.NS'
}

def get_symbol_from_name(stock_name):
    """Enhanced function to fetch stock symbol from full stock name"""
    try:
        # First check if it's already a valid symbol
        if stock_name.upper() in [symbol for symbol in COMMON_STOCKS.values()]:
            return stock_name.upper()
        
        # Check if it's in our common stocks dictionary
        stock_upper = stock_name.upper()
        if stock_upper in COMMON_STOCKS:
            return COMMON_STOCKS[stock_upper]
        
        # Try Indian stock market by appending .NS
        try:
            indian_symbol = f"{stock_name.upper()}.NS"
            ticker = yf.Ticker(indian_symbol)
            info = ticker.info
            if 'symbol' in info:
                return indian_symbol
        except:
            pass
        
        # Try US market
        ticker = yf.Ticker(stock_name)
        info = ticker.info
        if 'symbol' in info:
            return info['symbol']
        
        st.error(f"Stock symbol not found for {stock_name}")
        return None
    except Exception as e:
        st.error(f"Error finding symbol for {stock_name}: {str(e)}")
        return None

def get_stock_data(symbol):
    """Enhanced function to fetch stock data with automatic refresh"""
    try:
        stock = yf.Ticker(symbol)
        # Force refresh the data
        stock.info = None  # Clear cached info
        info = stock.info
        hist = stock.history(period="1y", auto_adjust=True)
        return info, hist
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return None, None

# [Previous functions remain the same: create_price_chart, create_volume_chart, display_metrics]

def main():
    # Sidebar
    with st.sidebar:
        st.header("📊 Analysis Options")
        analysis_type = st.selectbox(
            "Choose Analysis Type",
            ["Comprehensive Analysis", "Technical Analysis", "Fundamental Analysis", 
             "News Analysis", "Sentiment Analysis"]
        )
        
        # Add market selection
        market = st.selectbox(
            "Select Market",
            ["US Market", "Indian Market"]
        )
        
        st.markdown("---")
        st.markdown("### Watchlist")
        watchlist_symbol = st.text_input("Add to Watchlist")
        if st.button("Add"):
            symbol = get_symbol_from_name(watchlist_symbol)
            if symbol:
                st.session_state.watchlist.add(symbol)
        
        st.markdown("#### Current Watchlist")
        for symbol in st.session_state.watchlist:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(symbol)
            with col2:
                if st.button("Remove", key=f"remove_{symbol}"):
                    st.session_state.watchlist.remove(symbol)

    # Main content
    st.markdown('<h1 class="stock-header">🤖 Advanced Stock Market Analysis By Shivam Shukla</h1>', unsafe_allow_html=True)
    
    # Search and Analysis Section
    col1, col2 = st.columns([2, 1])
    with col1:
        stock_input = st.text_input(
            "Enter Stock Name or Symbol (e.g., NVIDIA, TCS, RELIANCE)", 
            help="You can enter company names like 'NVIDIA' or symbols like 'NVDA'"
        )
    with col2:
        date_range = st.selectbox(
            "Select Time Range",
            ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]
        )

    if st.button("Analyze", type="primary"):
        if not stock_input:
            st.error("Please enter a stock name or symbol.")
            return

        # Convert input to symbol
        stock_symbol = get_symbol_from_name(stock_input)
        if stock_symbol:
            try:
                # Initialize agents
                if initialize_agents():
                    # Show loading spinner
                    with st.spinner(f"Analyzing {stock_symbol}..."):
                        # Add auto-refresh mechanism
                        st.cache_data.clear()
                        
                        # Fetch fresh stock data
                        info, hist = get_stock_data(stock_symbol)
                        
                        if info and hist is not None:
                            # Display company info
                            st.markdown("### Company Overview")
                            st.write(info.get('longBusinessSummary', 'No description available.'))
                            
                            # Rest of the display code remains the same...
                            [Previous display code...]

                            # Add refresh button
                            if st.button("Refresh Data"):
                                st.experimental_rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Footer remains the same...

if __name__ == "__main__":
    main()
