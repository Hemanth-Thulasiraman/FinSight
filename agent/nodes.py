from openai import OpenAI
from agent.state import AgentState
from tools.company_profile import get_company_profile
from tools.news_search import search_news
from tools.financial_data import get_financial_data
from tools.memory_retrieval import retrieve_prior_research
from tools.save_brief import save_brief
from db.database import get_connection, release_connection
from ingestion.db_writer import insert_research_brief, insert_brief_section
from ingestion.models import ResearchBrief, BriefSection
from tools.memory_retrieval import get_embedding
import uuid
from ingestion.models import RunLog
from ingestion.db_writer import insert_run_log

client = OpenAI()
MAX_TOOL_CALLS = 12

def check_memory(state: AgentState) -> dict:
    """Check pgvector for prior research on this ticker."""
    ticker = state["ticker"]
    result = retrieve_prior_research(ticker, f"financial research {ticker}")
    return {
        "prior_research": result,
        "tool_call_count": state["tool_call_count"] + 1,
        "messages": state["messages"] + [f"Memory check complete: {result.get('has_prior_research')}"]
    }

def get_company(state: AgentState) -> dict:
    """Fetch company profile."""
    ticker = state["ticker"]
    result = get_company_profile(ticker,)

    if result.get("error"):
        return {"status": "FAILED", "error_message": result["message"]}
    else:
        return {"company_profile": result,
         "tool_call_count": state["tool_call_count"] + 1,
         "messages": state["messages"] + [f"Company profile fetched: {result['name']}"]}
    

def get_news(state: AgentState) -> dict:
    """Fetch news articles with coverage validation."""
    ticker = state["ticker"]
    company_name = state["company_profile"]["name"]
    result = search_news(ticker, company_name)
    if result.get("error"):
        return {"status": "FAILED", "error_message": result["message"]}
    coverage_flag = result["coverage_flag"]
    return {
        "news_results": result,
        "coverage_flag": coverage_flag,
        "tool_call_count": state["tool_call_count"] + 1,
        "messages": state["messages"] + [f"News fetched: {result['article_count']} articles, coverage: {coverage_flag}"]
    }


def get_financials(state: AgentState) -> dict:
    """Fetch financial data."""
    ticker = state["ticker"]
    result = get_financial_data(ticker,)
    if result.get("error"):
        return {"status": "FAILED", "error_message": result["message"]}
    return {"tool_call_count": state["tool_call_count"] + 1,"financial_data" : result,"messages": state["messages"] + [f"Financial data fetched for {ticker}"] }


def generate_brief(state: AgentState) -> dict:
    """Generate research brief using GPT-4o."""
    profile = state["company_profile"]
    news = state["news_results"]
    financials = state["financial_data"]

    top_headlines = "\n".join(
        f"- {a['headline']} ({a['source']})"
        for a in news.get("articles", [])[:5]
    )

    coverage_warning = ""
    if state.get("coverage_flag") == "LOW_COVERAGE":
        coverage_warning = "WARNING: Limited news coverage. Flag news-based claims as low confidence."

    prior_research_section = ""
    if state.get("prior_research", {}).get("has_prior_research"):
        sections = state["prior_research"].get("sections", [])
        prior_research_section = "Prior Research Found:\n" + "\n".join(
            f"- {s['section_name']}: {s['section_text'][:200]}"
            for s in sections
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
{coverage_warning}
{prior_research_section}
Company:
  Name: {profile.get('name', 'N/A')}
  Sector: {profile.get('sector', 'N/A')}
  Industry: {profile.get('industry', 'N/A')}
Description:
{profile.get('description', 'N/A')[:500]}
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
    brief_text = response.choices[0].message.content

    return {
        "brief_content": brief_text,
        "status": "COMPLETED",
        "messages": state["messages"] + ["Brief generated successfully"]
    }

def save_output(state: AgentState) -> dict:
    """Save brief to file and persist to PostgreSQL for memory."""
    ticker = state["ticker"]
    brief_content = state["brief_content"]

    # Step 0: Insert run_log row to get a run_id
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO run_log (ticker_name, status, number_of_tool_calls)
               VALUES (%s, %s, %s) RETURNING run_id""",
            (ticker, "COMPLETED", state["tool_call_count"])
        )
        run_id = cursor.fetchone()[0]
        conn.commit()
    finally:
        release_connection(conn)

    # Step 1: Save to file
    file_result = save_brief(ticker, brief_content)
    file_path = file_result.get("file_path", "unknown")

    # Step 2: Insert into research_briefs table
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO research_briefs (run_id, ticker_name, s3_path)
               VALUES (%s, %s, %s) RETURNING brief_id""",
            (run_id, ticker, file_path)
        )
        brief_id = cursor.fetchone()[0]
        conn.commit()
    finally:
        release_connection(conn)

    # Step 3: Split brief into sections and embed each one
    sections = parse_brief_sections(brief_content)
    for section_name, section_text in sections.items():
        embedding = get_embedding(section_text)
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO brief_sections
                   (brief_id, section_name, section_text, embedding)
                   VALUES (%s, %s, %s, %s::vector)""",
                (brief_id, section_name, section_text, str(embedding))
            )
            conn.commit()
        finally:
            release_connection(conn)

    return {
        "messages": state["messages"] + [
            f"Brief saved to {file_path}",
            f"Brief and {len(sections)} sections stored in PostgreSQL"
        ]
    }

def parse_brief_sections(brief_content: str) -> dict:
    """
    Split the brief into named sections for embedding.
    Looks for markdown headers like '**1. Company Overview**'
    """
    import re
    sections = {}
    # Split on numbered headers
    parts = re.split(r'\*\*\d+\.\s+', brief_content)
    headers = re.findall(r'\*\*\d+\.\s+(.+?)\*\*', brief_content)

    for i, header in enumerate(headers):
        if i + 1 < len(parts):
            sections[header.strip()] = parts[i + 1].strip()

    # If parsing fails, store whole brief as one section
    if not sections:
        sections["full_brief"] = brief_content

    return sections

def emergency_stop(state: AgentState) -> dict:
    """Called when tool call limit exceeded or unrecoverable error."""
    return {
        "status": "FAILED",
        "error_message": f"Agent stopped: tool_call_count={state['tool_call_count']}, status={state['status']}",
        "messages": state["messages"] + ["Emergency stop triggered"]
    }