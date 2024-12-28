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
from os import getenv
from dotenv import load_dotenv
import yfinance as yf

# Load environment variables
load_dotenv()

# Your predefined Groq API key
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"  # Replace with your actual API key

# Page configuration
st.set_page_config(
    page_title="Advanced Stock Market Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stock-header {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #1f77b4;
    }
    .news-card {
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'agents_initialized' not in st.session_state:
    st.session_state.agents_initialized = False
    st.session_state.watchlist = set()
    st.session_state.analysis_history = []

def initialize_agents():
    """Initialize all agent instances"""
    if not st.session_state.agents_initialized:
        try:
            st.session_state.web_agent = Agent(
                name="Web Search Agent",
                role="Search the web for the information",
                model=Groq(api_key=GROQ_API_KEY),
                tools=[
                    GoogleSearch(fixed_language='english', fixed_max_results=5),
                    DuckDuckGo(fixed_max_results=5)
                ],
                instructions=['Always include sources'],
                show_tool_calls=True,
                markdown=True
            )

            st.session_state.finance_agent = Agent(
                name="Financial AI Agent",
                role="Providing financial insights",
                model=Groq(api_key=GROQ_API_KEY),
                tools=[
                    YFinanceTools(
                        stock_price=True,
                        company_news=True,
                        analyst_recommendations=True,
                        historical_prices=True
                    )
                ],
                instructions=["Use tables to display the data"],
                show_tool_calls=True,
                markdown=True
            )

            st.session_state.multi_ai_agent = Agent(
                name='A Stock Market Agent',
                role='A comprehensive assistant specializing in stock market analysis',
                model=Groq(api_key=GROQ_API_KEY),
                team=[st.session_state.web_agent, st.session_state.finance_agent],
                instructions=["Always include sources", "Use tables to display the data"],
                show_tool_calls=True,
                markdown=True
            )

            st.session_state.agents_initialized = True
            return True
        except Exception as e:
            st.error(f"Error initializing agents: {str(e)}")
            return False

[Previous functions remain the same: get_stock_data, create_price_chart, create_volume_chart, display_metrics]

def main():
    # Sidebar
    with st.sidebar:
        st.header("📊 Analysis Options")
        analysis_type = st.selectbox(
            "Choose Analysis Type",
            ["Comprehensive Analysis", "Technical Analysis", "Fundamental Analysis", 
             "News Analysis", "Sentiment Analysis"]
        )
        
        st.markdown("---")
        st.markdown("### Watchlist")
        watchlist_symbol = st.text_input("Add to Watchlist")
        if st.button("Add"):
            st.session_state.watchlist.add(watchlist_symbol.upper())
        
        st.markdown("#### Current Watchlist")
        for symbol in st.session_state.watchlist:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(symbol)
            with col2:
                if st.button("Remove", key=f"remove_{symbol}"):
                    st.session_state.watchlist.remove(symbol)

    # Main content
    st.markdown('<h1 class="stock-header">🤖 Advanced Stock Market Analysis</h1>', unsafe_allow_html=True)
    
    # Search and Analysis Section
    col1, col2 = st.columns([2, 1])
    with col1:
        stock_symbol = st.text_input("Enter Stock Symbol (e.g., NVDA, AAPL)", "")
    with col2:
        date_range = st.selectbox(
            "Select Time Range",
            ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]
        )

    if st.button("Analyze", type="primary"):
        if not stock_symbol:
            st.error("Please enter a stock symbol.")
            return

        try:
            # Initialize agents
            if initialize_agents():
                # Show loading spinner
                with st.spinner(f"Analyzing {stock_symbol}..."):
                    # Fetch stock data
                    info, hist = get_stock_data(stock_symbol)
                    
                    if info and hist is not None:
                        # Display company info
                        st.markdown("### Company Overview")
                        st.write(info.get('longBusinessSummary', 'No description available.'))
                        
                        # Display key metrics
                        st.markdown("### Key Metrics")
                        display_metrics(info)
                        
                        # Charts
                        st.markdown("### Price Analysis")
                        price_chart = create_price_chart(hist, stock_symbol)
                        st.plotly_chart(price_chart, use_container_width=True)
                        
                        volume_chart = create_volume_chart(hist)
                        st.plotly_chart(volume_chart, use_container_width=True)
                        
                        # AI Analysis
                        st.markdown("### AI Analysis")
                        query = f"Provide a {analysis_type.lower()} for {stock_symbol}."
                        response = st.session_state.multi_ai_agent.get_response(query)
                        st.markdown(response)
                        
                        # Add to analysis history
                        st.session_state.analysis_history.append({
                            'symbol': stock_symbol,
                            'timestamp': datetime.now(),
                            'analysis_type': analysis_type
                        })
                        
                        # Display recent searches
                        st.markdown("### Recent Analysis History")
                        history_df = pd.DataFrame(st.session_state.analysis_history)
                        if not history_df.empty:
                            st.dataframe(history_df)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
        This advanced stock market analysis tool combines:
        - Real-time market data analysis
        - AI-powered insights
        - Technical and fundamental analysis
        - News and sentiment analysis
        - Interactive charts and visualizations
        
        Use the sidebar to configure your analysis preferences and manage your watchlist.
    """)

if __name__ == "__main__":
    main()
