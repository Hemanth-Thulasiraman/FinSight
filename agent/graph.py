from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agent.state import AgentState
from agent.nodes import check_memory, generate_brief, save_output, emergency_stop
from agent.react_node import react_node

MAX_TOOL_CALLS = 12

def should_continue(state: AgentState) -> str:
    """Routes after every node."""
    if state.get("status") == "FAILED":
        return "emergency_stop"
    if state.get("tool_call_count", 0) >= MAX_TOOL_CALLS:
        return "emergency_stop"
    return "continue"

def react_router(state: AgentState) -> str:
    """
    Routes after react_node.
    If LLM decided generate_brief, go there.
    Otherwise loop back to react_node for next tool call.
    """
    if state.get("status") == "FAILED":
        return "emergency_stop"
    if state.get("tool_call_count", 0) >= MAX_TOOL_CALLS:
        return "emergency_stop"
    if state.get("next_action") == "generate_brief":
        return "generate_brief"
    return "react"

def build_graph():
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("check_memory", check_memory)
    workflow.add_node("react", react_node)
    workflow.add_node("generate_brief", generate_brief)
    workflow.add_node("save_output", save_output)
    workflow.add_node("emergency_stop", emergency_stop)

    # Entry point
    workflow.set_entry_point("check_memory")

    # After memory check → enter ReAct loop
    workflow.add_conditional_edges(
        "check_memory",
        should_continue,
        {"continue": "react", "emergency_stop": "emergency_stop"}
    )

    # ReAct loop — LLM decides next action
    workflow.add_conditional_edges(
        "react",
        react_router,
        {
            "react": "react",           # loop back
            "generate_brief": "generate_brief",
            "emergency_stop": "emergency_stop"
        }
    )

    # After brief generation → save
    workflow.add_conditional_edges(
        "generate_brief",
        should_continue,
        {"continue": "save_output", "emergency_stop": "emergency_stop"}
    )

    # Terminal edges
    workflow.add_edge("save_output", END)
    workflow.add_edge("emergency_stop", END)

    memory = MemorySaver()
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["check_memory", "save_output"]
    )

graph = build_graph()