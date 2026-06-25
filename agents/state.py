"""
Shared LangGraph state definition for JobScan Agent.
All agents read from and write to this typed state.
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class JobListing(TypedDict):
    id: int
    title: str
    company: str
    location: str
    skills_required: list[str]
    description: str
    category: str
    type: str


class GapResult(TypedDict):
    job_id: int
    job_title: str
    company: str
    category: str
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: int
    recommendation: str


class JobScanState(TypedDict):
    # Input
    resume_text: str
    resume_path: str

    # Loaded by scraper agent
    job_listings: list[JobListing]

    # Produced by analyser agent
    gap_results: list[GapResult]

    # Produced by report agent
    report_path: str
    report_markdown: str

    # Agent message history (LangGraph managed)
    messages: Annotated[list, add_messages]

    # Control flow
    next_agent: Optional[str]
    error: Optional[str]
