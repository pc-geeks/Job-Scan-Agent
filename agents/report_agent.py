"""
Report Agent — generates a structured Markdown gap analysis report.
Writes the file via MCP Filesystem server pattern (direct file write here).
"""

from datetime import datetime
from pathlib import Path
from langchain_core.messages import AIMessage
from agents.state import JobScanState

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _score_bar(score: int) -> str:
    """Visual ASCII progress bar for match score."""
    filled = round(score / 10)
    empty = 10 - filled
    return f"[{'█' * filled}{'░' * empty}] {score}%"


def report_node(state: JobScanState) -> dict:
    """
    Writes a detailed Markdown report with:
    - Summary table of all jobs ranked by match score
    - Per-job breakdown of matched / missing skills
    - Recommended action list (skills to learn)
    """
    print("\n[Report Agent] Generating gap analysis report...")

    gap_results = state["gap_results"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    filename = f"jobscan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Aggregate missing skills across all jobs ---
    from collections import Counter
    all_missing = []
    for r in gap_results:
        all_missing.extend(r["missing_skills"])
    top_missing = Counter(all_missing).most_common(10)

    # --- Build Markdown ---
    lines = []

    lines.append("# JobScan Agent — Gap Analysis Report")
    lines.append(f"\n**Generated:** {timestamp}  ")
    lines.append(f"**Jobs analysed:** {len(gap_results)}  ")
    lines.append(f"**Model:** Ollama (local LLM)  \n")

    lines.append("---\n")

    # Summary table
    lines.append("## Summary — All Jobs Ranked by Match Score\n")
    lines.append("| Rank | Job Title | Company | category | Match |")
    lines.append("|------|-----------|---------|--------|-------|")
    for i, r in enumerate(gap_results, 1):
        lines.append(
            f"| {i} | {r['job_title']} | {r['company']} | {r['category']} | {r['match_score']}% |"
        )

    lines.append("\n---\n")

    # Top 5 detailed breakdowns
    lines.append("## Top 5 Best-Matching Jobs — Detailed Breakdown\n")
    for r in gap_results[:5]:
        lines.append(f"### {r['job_title']} — {r['company']}")
        lines.append(f"**Category:** {r['category']}  ")
        lines.append(f"**Match score:** {_score_bar(r['match_score'])}\n")

        if r["matched_skills"]:
            lines.append("**Matched skills ✓**")
            for s in r["matched_skills"]:
                lines.append(f"- {s}")
        else:
            lines.append("**Matched skills:** none detected")

        lines.append("")

        if r["missing_skills"]:
            lines.append("**Missing skills ✗**")
            for s in r["missing_skills"]:
                lines.append(f"- {s}")
        else:
            lines.append("**Missing skills:** none — great fit!")

        lines.append(f"\n**Recommendation:** {r['recommendation']}\n")
        lines.append("---\n")

    # Skills to learn
    lines.append("## Skills Gap — What to Learn Next\n")
    lines.append("These skills appear most frequently in jobs you are missing:\n")
    lines.append("| Skill | Appears in N jobs |")
    lines.append("|-------|-------------------|")
    for skill, count in top_missing:
        lines.append(f"| {skill} | {count} |")

    lines.append("\n---\n")
    lines.append("This report was produced by **JobScan Agent**, a multi-agent AI system built with:")
    lines.append("- **LangGraph** — multi-agent StateGraph orchestration (Supervisor → Scraper → Analyser → Report)")
    lines.append("- **Ollama** — fully local LLM inference (no cloud API required)")
    lines.append("- **ChromaDB** — vector store for semantic job description indexing")
    lines.append("- **MCP pattern** — Filesystem tool server for reading resume and writing this report")
    
    markdown = "\n".join(lines)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"[Report Agent] Report written to: {report_path}")

    return {
        "report_path": str(report_path),
        "report_markdown": markdown,
        "messages": [AIMessage(
            content=f"Report Agent: Gap analysis report written to {report_path}"
        )]
    }
