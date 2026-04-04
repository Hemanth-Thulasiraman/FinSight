from openai import OpenAI
from agent.state import AgentState
from agent.react_prompt import build_react_prompt
from tools.company_profile import get_company_profile
from tools.news_search import search_news
from tools.financial_data import get_financial_data
import numpy as np

client = OpenAI()

VALID_ACTIONS = {"company_profile", "news_search", "financial_data", "generate_brief"}

def react_node(state: AgentState) -> dict:
    """
    The ReAct reasoning node.
    LLM decides what tool to call next based on current state.
    """
    # Build reasoning prompt
    prompt = build_react_prompt(state)

    # Ask LLM to decide next action
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0
    )

    raw_action = response.choices[0].message.content.strip().lower()

    # Validate — if LLM gives invalid response, default to safest next action
    if raw_action not in VALID_ACTIONS:
        tools_called = state.get("tools_called", [])
        if "company_profile" not in tools_called:
            raw_action = "company_profile"
        elif "news_search" not in tools_called:
            raw_action = "news_search"
        elif "financial_data" not in tools_called:
            raw_action = "financial_data"
        else:
            raw_action = "generate_brief"

    # Execute the chosen tool
    tools_called = state.get("tools_called", [])
    ticker = state["ticker"]

    if raw_action == "company_profile":
        result = get_company_profile(ticker)
        if result.get("error"):
            return {"status": "FAILED", "error_message": result["message"]}
        return {
            "company_profile": result,
            "tools_called": tools_called + ["company_profile"],
            "tool_call_count": state["tool_call_count"] + 1,
            "next_action": "react",
            "messages": state["messages"] + [f"ReAct: called company_profile → {result['name']}"]
        }

    elif raw_action == "news_search":
        company_name = state.get("company_profile", {}).get("name", ticker)
        result = search_news(ticker, company_name)
        if result.get("error"):
            return {"status": "FAILED", "error_message": result["message"]}
        coverage_flag = result["coverage_flag"]
        return {
            "news_results": result,
            "coverage_flag": coverage_flag,
            "tools_called": tools_called + ["news_search"],
            "tool_call_count": state["tool_call_count"] + 1,
            "next_action": "react",
            "messages": state["messages"] + [f"ReAct: called news_search → {result['article_count']} articles, {coverage_flag}"]
        }

    elif raw_action == "financial_data":
        result = get_financial_data(ticker)
        if result.get("error"):
            return {"status": "FAILED", "error_message": result["message"]}
        return {
            "financial_data": result,
            "tools_called": tools_called + ["financial_data"],
            "tool_call_count": state["tool_call_count"] + 1,
            "next_action": "react",
            "messages": state["messages"] + [f"ReAct: called financial_data → revenue={result.get('revenue')}"]
        }

    elif raw_action == "generate_brief":
        return {
            "next_action": "generate_brief",
            "messages": state["messages"] + ["ReAct: decided → generate_brief"]
        }
