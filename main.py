"""
JobScan Agent — Main entry point.

Usage:
    python main.py                          # uses sample resume
    python main.py --resume path/to/cv.txt  # your own resume (txt or pdf)
    python main.py --resume cv.pdf --model llama3.2:3b

What it does:
    1. Scraper Agent   — Fetching live jobs from Adzuna
    2. Analyser Agent  — uses Ollama (local LLM) to compare your resume to each job
    3. Report Agent    — writes a ranked Markdown report to output/
"""

import argparse
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from langchain_core.messages import HumanMessage

from agents.supervisor import build_graph

console = Console()


def load_resume(path: str) -> str:
    """Load resume text from .txt or .pdf file."""
    p = Path(path)
    if not p.exists():
        console.print(f"[red]ERROR: Resume file not found: {path}[/red]")
        sys.exit(1)

    if p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(p))
            return "\n".join(page.extract_text() for page in reader.pages)
        except ImportError:
            console.print("[red]pypdf not installed. Run: pip install pypdf[/red]")
            sys.exit(1)

    return p.read_text(encoding="utf-8")


def print_summary(gap_results: list) -> None:
    """Print a rich summary table to the terminal."""
    table = Table(
        title="Job Match Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Rank", style="dim", width=5)
    table.add_column("Job Title", style="bold")
    table.add_column("Company")
    table.add_column("Category")
    table.add_column("Match", justify="right")
    table.add_column("Top Missing Skill")

    for i, r in enumerate(gap_results[:10], 1):
        score = r["match_score"]
        color = "green" if score >= 70 else "yellow" if score >= 40 else "red"
        top_missing = r["missing_skills"][0] if r["missing_skills"] else "—"
        table.add_row(
            str(i),
            r["job_title"],
            r["company"],
            r["category"],
            f"[{color}]{score}%[/{color}]",
            top_missing,
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="JobScan Agent — AI Job Gap Analyser")
    parser.add_argument(
        "--resume",
        default="data/sample_resume.txt",
        help="Path to your resume (.txt or .pdf). Default: data/sample_resume.txt",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama model name (e.g. llama3.2, qwen2.5:14b). Overrides OLLAMA_MODEL env var.",
    )
    args = parser.parse_args()

    # Set model env var if passed via CLI
    if args.model:
        os.environ["OLLAMA_MODEL"] = args.model

    model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    console.print(Panel.fit(
        "[bold cyan]JobScan Agent[/bold cyan]\n"
        "Multi-agent HK AI Job Gap Analyser\n"
        f"LangGraph + Ollama ({model_name}) + ChromaDB + MCP",
        border_style="cyan",
    ))

    # Load resume
    resume_text = load_resume(args.resume)
    console.print(f"[green]Loaded resume:[/green] {args.resume} ({len(resume_text)} chars)")

    # Build and run the LangGraph pipeline
    console.print("\n[bold]Running multi-agent pipeline...[/bold]")
    graph = build_graph()

    initial_state = {
        "resume_text": resume_text,
        "resume_path": args.resume,
        "job_listings": [],
        "gap_results": [],
        "report_path": "",
        "report_markdown": "",
        "messages": [HumanMessage(content=f"Analyse my resume against HK AI jobs. Resume: {args.resume}")],
        "next_agent": None,
        "error": None,
    }

    final_state = graph.invoke(initial_state)

    # Check for errors
    if final_state.get("error"):
        console.print(f"[red]Pipeline error: {final_state['error']}[/red]")
        sys.exit(1)

    # Print results
    console.print("\n")
    print_summary(final_state["gap_results"])

    report_path = final_state.get("report_path", "")
    if report_path:
        console.print(f"\n[bold green]Report saved:[/bold green] {report_path}")
        console.print("[dim]Open the .md file to see your full gap analysis report.[/dim]")

    # Print agent message history
    console.print("\n[bold]Agent message log:[/bold]")
    for msg in final_state["messages"]:
        prefix = "User" if msg.__class__.__name__ == "HumanMessage" else "Agent"
        console.print(f"  [{prefix}] {msg.content}")


if __name__ == "__main__":
    main()
