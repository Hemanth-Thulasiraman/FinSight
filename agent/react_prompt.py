def build_react_prompt(state: dict) -> str:
    """
    Build the ReAct reasoning prompt.
    Tells the LLM what tools are available, what's been collected,
    and asks it to decide what to do next.
    """
    ticker = state["ticker"]
    tools_called = state.get("tools_called", [])
    tool_call_count = state.get("tool_call_count", 0)
    max_calls = 12

    # Summarize what's been collected so far
    collected = []
    if "company_profile" in tools_called:
        name = state.get("company_profile", {}).get("name", "unknown")
        collected.append(f"- Company profile: {name}")
    if "news_search" in tools_called:
        count = state.get("news_results", {}).get("article_count", 0)
        flag = state.get("coverage_flag", "UNKNOWN")
        collected.append(f"- News: {count} articles, coverage={flag}")
    if "financial_data" in tools_called:
        collected.append("- Financial data: collected")

    collected_str = "\n".join(collected) if collected else "- Nothing collected yet"

    prior = state.get("prior_research", {})
    prior_str = "Yes — prior research exists for this ticker" \
        if prior and prior.get("has_prior_research") \
        else "No prior research found"

    prompt = f"""You are a financial research agent deciding what to do next.

RESEARCH TARGET: {ticker}
TOOL CALLS USED: {tool_call_count} of {max_calls} maximum

PRIOR RESEARCH: {prior_str}

ALREADY COLLECTED:
{collected_str}

AVAILABLE TOOLS:
- company_profile: Get company name, sector, industry, description. Call this first.
- news_search: Get recent news articles. Call after company_profile.
- financial_data: Get revenue, margins, EPS, P/E ratio. Call after news_search.
- generate_brief: Generate the research brief. Call only when you have enough data.

RULES:
- Never call a tool you have already called
- If news coverage is LOW_COVERAGE, you may call news_search again with a note
- Call generate_brief when you have company_profile AND financial_data AND news_search
- Call generate_brief immediately if tool_call_count >= 10
- Never call generate_brief without at least company_profile

DECISION: Based on what you have collected so far, what should you do next?

Respond with ONLY one of these exact strings, nothing else:
company_profile
news_search
financial_data
generate_brief
"""
    return prompt