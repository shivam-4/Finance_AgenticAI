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

def create_price_chart(hist_data, symbol):
    """Create an interactive price chart using plotly"""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist_data.index,
        open=hist_data['Open'],
        high=hist_data['High'],
        low=hist_data['Low'],
        close=hist_data['Close'],
        name='Price'
    ))
    
    fig.update_layout(
        title=f'{symbol} Stock Price',
        yaxis_title='Price',
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )
    return fig

def create_volume_chart(hist_data):
    """Create volume chart using plotly"""
    fig = px.bar(hist_data, x=hist_data.index, y='Volume')
    fig.update_layout(
        title='Trading Volume',
        yaxis_title='Volume',
        template='plotly_white'
    )
    return fig

def display_metrics(info):
    """Display key metrics in a grid"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A'):,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A'):,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("52 Week Low", f"${info.get('fiftyTwoWeekLow', 'N/A'):,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

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
                            response = st.session_state.multi_ai_agent.print_response(query, stream=True)
                            
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
                            
                            # Add refresh button
                            if st.button("Refresh Data"):
                                st.experimental_rerun()

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
