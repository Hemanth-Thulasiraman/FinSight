from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    ticker: str  
    company_profile: Optional[dict]
    news_results: Optional[dict]
    financial_data: Optional[dict]
    prior_research: Optional[dict]
    brief_content: Optional[str]
    tool_call_count: int
    coverage_flag: Optional[str] 
    status: str
    messages: List[str]
    error_message: Optional[str]
    tools_called: List[str]      
    next_action: Optional[str]