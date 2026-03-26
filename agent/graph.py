from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agent.state import AgentState
from agent.nodes import (
    check_memory, get_company, get_news,
    get_financials, generate_brief,
    save_output, emergency_stop
)

MAX_TOOL_CALLS = 12

def should_continue(state: AgentState) -> str:
    """
    Conditional router — runs after every node.
    Returns the name of the next node to execute.
    """
    if state.get("status") == "FAILED":
        return "emergency_stop"
    if state.get("tool_call_count", 0) >= MAX_TOOL_CALLS:
        return "emergency_stop"
    return "continue"

def build_graph():
    """Build and compile the LangGraph agent."""

    # Initialize the graph with our state schema
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("check_memory", check_memory)
    workflow.add_node("get_company", get_company)
    workflow.add_node("get_news", get_news)
    workflow.add_node("get_financials", get_financials)
    workflow.add_node("generate_brief", generate_brief)
    workflow.add_node("save_output", save_output)
    workflow.add_node("emergency_stop", emergency_stop)

    # Set entry point — first node to execute
    workflow.set_entry_point("check_memory")

    # Add conditional edges after each node
    workflow.add_conditional_edges(
        "check_memory",
        should_continue,
        {"continue": "get_company", "emergency_stop": "emergency_stop"}
    )
    workflow.add_conditional_edges(
        "get_company",
        should_continue,
        {"continue": "get_news", "emergency_stop": "emergency_stop"}
    )
    workflow.add_conditional_edges(
        "get_news",
        should_continue,
        {"continue": "get_financials", "emergency_stop": "emergency_stop"}
    )
    workflow.add_conditional_edges(
        "get_financials",
        should_continue,
        {"continue": "generate_brief", "emergency_stop": "emergency_stop"}
    )
    workflow.add_conditional_edges(
        "generate_brief",
        should_continue,
        {"continue": "save_output", "emergency_stop": "emergency_stop"}
    )

    # Terminal edges — these go to END
    workflow.add_edge("save_output", END)
    workflow.add_edge("emergency_stop", END)

    # Compile with memory checkpointer for HITL support
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before= ["check_memory","save_output"])

# Build the graph at module level
graph = build_graph()