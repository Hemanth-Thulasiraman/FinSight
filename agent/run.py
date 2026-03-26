import uuid
from langgraph.types import Command
from agent.graph import graph

def run_agent(ticker: str):
    """Run the FinSight agent with HITL checkpoints."""

    # Each run needs a unique thread_id for state isolation
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Initial state
    initial_state = {
        "ticker": ticker.upper(),
        "tool_call_count": 0,
        "status": "RUNNING",
        "messages": [],
        "company_profile": None,
        "news_results": None,
        "financial_data": None,
        "prior_research": None,
        "brief_content": None,
        "coverage_flag": None,
        "error_message": None
    }

    print(f"\nStarting FinSight agent for {ticker.upper()}...")
    print("="*50)

    # First invoke — runs until first HITL interrupt
    result = graph.invoke(initial_state, config)

    # HITL Checkpoint 1 — Disambiguation
    print(f"\nDisambiguation Check")
    print(f"Ticker entered: {ticker.upper()}")
    confirm = input("Is this the correct company? (yes/no): ").strip().lower()

    if confirm != "yes":
        new_ticker = input("Enter correct ticker: ").strip().upper()
        # Resume with corrected ticker
        result = graph.invoke(
            Command(resume={"ticker": new_ticker}),
            config
        )
    else:
        # Resume with confirmed ticker
        result = graph.invoke(
            Command(resume={}),
            config
        )

    # Agent runs through all nodes until second HITL interrupt
    # HITL Checkpoint 2 — Final Review
    print(f"\nFinal Brief Review")
    print("-"*50)
    print(result.get("brief_content", "No brief generated"))
    print("-"*50)
    approve = input("\nApprove this brief? (yes/no): ").strip().lower()

    if approve == "yes":
        result = graph.invoke(Command(resume={}), config)
        print("\nBrief approved and saved.")
    else:
        reason = input("Rejection reason: ").strip()
        print(f"Brief rejected: {reason}")
        print("In Phase 8 we will add automatic regeneration on rejection.")

    print("\nAgent run complete.")
    print(f"Messages: {result.get('messages', [])}")
    return result

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    run_agent(ticker)