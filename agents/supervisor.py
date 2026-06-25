"""
Supervisor Agent — LangGraph StateGraph orchestrator.
Routes: START -> scraper -> analyser -> report -> END
Uses conditional edges so any agent can signal an error and halt.
"""

from langgraph.graph import StateGraph, START, END
from agents.state import JobScanState
from agents.scraper_agent import scraper_node
from agents.analyser_agent import analyser_node
from agents.report_agent import report_node


def route_after_scraper(state: JobScanState) -> str:
    """After scraping: go to analyser, or END if error."""
    if state.get("error"):
        return END
    if not state.get("job_listings"):
        return END
    return "analyser"


def route_after_analyser(state: JobScanState) -> str:
    """After analysis: go to report, or END if error."""
    if state.get("error"):
        return END
    if not state.get("gap_results"):
        return END
    return "report"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph multi-agent pipeline."""
    graph = StateGraph(JobScanState)

    # Register agent nodes
    graph.add_node("scraper", scraper_node)
    graph.add_node("analyser", analyser_node)
    graph.add_node("report", report_node)

    # Wire up edges
    graph.add_edge(START, "scraper")
    graph.add_conditional_edges("scraper", route_after_scraper, {"analyser": "analyser", END: END})
    graph.add_conditional_edges("analyser", route_after_analyser, {"report": "report", END: END})
    graph.add_edge("report", END)

    return graph.compile()
