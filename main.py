import sys
import os
# Add project root to path before any other imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from langgraph.types import Command
from agent.graph import graph
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FinSight API", version="1.0.0")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_runs = {}

class ResearchRequest(BaseModel):
    ticker: str

class ReviewRequest(BaseModel):
    approved: bool
    corrected_ticker: Optional[str] = None
    rejection_reason: Optional[str] = None

class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FinSight API"}

@app.post("/research", response_model=RunResponse)
async def start_research(request: ResearchRequest):
    run_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": run_id}}
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
    "error_message": None,
    "tools_called": [],        
    "next_action": None        
}
    graph.invoke(initial_state, config)
    active_runs[run_id] = {
        "config": config,
        "stage": "disambiguation",
        "ticker": request.ticker.upper()
    }
    return RunResponse(
        run_id=run_id,
        status="AWAITING_REVIEW",
        message=f"Please confirm ticker: {request.ticker.upper()}"
    )

@app.post("/review/{run_id}", response_model=RunResponse)
async def submit_review(run_id: str, request: ReviewRequest):
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    run_info = active_runs[run_id]
    config = run_info["config"]
    if not request.approved:
        if run_info["stage"] == "disambiguation" and request.corrected_ticker:
            graph.invoke(
                Command(resume={"ticker": request.corrected_ticker.upper()}),
                config
            )
            active_runs[run_id]["stage"] = "final_review"
            return RunResponse(
                run_id=run_id,
                status="RUNNING",
                message="Running with corrected ticker..."
            )
        else:
            del active_runs[run_id]
            return RunResponse(
                run_id=run_id,
                status="REJECTED",
                message=f"Brief rejected: {request.rejection_reason}"
            )
    result = graph.invoke(Command(resume={}), config)
    if run_info["stage"] == "disambiguation":
        active_runs[run_id]["stage"] = "final_review"
        brief_preview = ""
        if result.get("brief_content"):
            brief_preview = result["brief_content"] 
        return RunResponse(
            run_id=run_id,
            status="AWAITING_REVIEW",
            message=brief_preview
        )
    else:
        del active_runs[run_id]
        return RunResponse(
            run_id=run_id,
            status="COMPLETED",
            message="Brief approved and saved successfully."
        )

@app.get("/research/{run_id}")
async def get_run_status(run_id: str):
    if run_id not in active_runs:
        return {"run_id": run_id, "status": "NOT_FOUND"}
    run_info = active_runs[run_id]
    return {
        "run_id": run_id,
        "status": "AWAITING_REVIEW",
        "stage": run_info["stage"],
        "ticker": run_info["ticker"]
    }