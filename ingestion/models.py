from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid

@dataclass
class RunLog:
    ticker_name: str
    status: str
    run_id: Optional[uuid.UUID] = None
    number_of_tool_calls: Optional[int] = None
    time_elapsed: Optional[float] = None
    cost: Optional[float] = None
    error_message: Optional[str] = None
    brief_s3_path: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class NewsArticle:
    source: str
    headline: str
    url: str
    body_summary: str
    s3_path: str
    run_id: Optional[uuid.UUID] = None
    published_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

@dataclass
class ResearchBrief:
    s3_path: str
    ticker_name: str
    brief_id : Optional[uuid.UUID] = None
    run_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None

@dataclass
class BriefSection:
    section_name: str
    section_text: str
    embedding: List[float]
    brief_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
