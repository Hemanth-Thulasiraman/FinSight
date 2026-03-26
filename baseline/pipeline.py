import os
from openai import OpenAI
from dotenv import load_dotenv
from tools.company_profile import get_company_profile
from tools.news_search import search_news
from tools.financial_data import get_financial_data
from tools.save_brief import save_brief

load_dotenv()

client = OpenAI()

def truncate(text: str, max_chars: int = 500) -> str:
    """Truncate text to max_chars to manage context window."""
    if not text:
        return "N/A"
    return text[:max_chars] + "..." if len(text) > max_chars else text

def run_baseline(ticker: str) -> str:
    """
    Run a simple sequential pipeline without an agent.
    Calls all tools in order, generates a brief, saves it.
    """ 
    print(f"Starting baseline pipeline for {ticker}...")

    # Step 1: Get company profile
    print("Fetching company profile...")
    profile = get_company_profile(ticker)
    if profile.get("error"):
        return f"Pipeline failed at company profile: {profile['message']}"

    company_name = profile["name"]

    # Step 2: Get news
    print("Searching news...")
    news = search_news(ticker, company_name)
    if news.get("error"):
        return f"Pipeline failed at news search: {news['message']}"

    # Step 3: Get financials
    print("Fetching financial data...")
    financials = get_financial_data(ticker)
    if financials.get("error"):
        return f"Pipeline failed at financials: {financials['message']}"

    # Step 4: Build prompt with truncated context
    print("Generating brief...")

    top_headlines = "\n".join(
        f"- {article['headline']} ({article['source']})"
        for article in news.get("articles", [])[:5]
    )

    prompt = f"""
You are a financial research analyst.
Write a structured research brief with these sections:
1. Company Overview
2. Recent News & Sentiment
3. Financial Analysis
4. Risk Flags
5. Summary & Recommendation

Be specific. Cite the data provided. Flag any data gaps.

Company:
  Name: {profile.get('name', 'N/A')}
  Sector: {profile.get('sector', 'N/A')}
  Industry: {profile.get('industry', 'N/A')}

Description:
  {truncate(profile.get('description', 'N/A'), 500)}

Recent News (coverage: {news.get('coverage_flag', 'N/A')}):
{top_headlines if top_headlines else '- No recent major headlines found.'}

Key Financials:
  Revenue: {financials.get('revenue', 'N/A')}
  Gross Margin: {financials.get('gross_margins', 'N/A')}
  Operating Margin: {financials.get('operating_margins', 'N/A')}
  EPS: {financials.get('earnings_per_share', 'N/A')}
  P/E Ratio: {financials.get('pe_ratio', 'N/A')}
  Free Cash Flow: {financials.get('free_cash_flow', 'N/A')}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    brief_content = response.choices[0].message.content

    # Step 5: Save the brief
    print("Saving brief...")
    from tools.save_brief import save_brief

    result = save_brief(ticker, brief_content)
    if result.get("error"):
        print(f"Warning: Failed to save brief: {result.get('message', 'Unknown error')}")
    else:
        print(f"Brief saved to {result['file_path']}")

    return brief_content

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    brief = run_baseline(ticker)
    print("\n" + "="*50)
    print(brief)