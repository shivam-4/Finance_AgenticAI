from phi.agent.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.googlesearch import GoogleSearch
from os import getenv
from dotenv import load_dotenv


load_dotenv()

webAgent = Agent(
    name="Web Search Agent",
    role="Search the web for the information",
    model = Groq(api_key=getenv('GROQ_API_KEY')),
    tools=[GoogleSearch(fixed_language='english',fixed_max_results=5),DuckDuckGo(fixed_max_results=5)],
    instructions=['Always include sources'],
    show_tool_calls=True,
    markdown=True
)

finance_agent = Agent(
    name="Financial AI Agent",
    role="Providing financial insights",
    model = Groq(api_key=getenv('GROQ_API_KEY')),
    tools= [YFinanceTools(stock_price=True,company_news=True,analyst_recommendations=True,historical_prices=True)],
    instructions=["Use tables to display the data"],
    show_tool_calls=True,
    markdown=True
)

multi_ai_agent = Agent(
    name='A Stock Market Agent',
    role='A comprehensive assistant specializing in stock market analysis by combining financial insights with real-time web searches to deliver accurate, up-to-date information',
    model=Groq(api_key=getenv('GROQ_API_KEY')),
    team=[webAgent,finance_agent],
    instructions=["Always include sources","Use tables to display the data"],
    show_tool_calls=True,
    markdown=True
)

multi_ai_agent.print_response("Summarize analyst recommendation and share the latest news for Nvidia.",stream=True)