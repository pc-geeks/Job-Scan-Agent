"""
Analyser Agent — compares the resume against each job listing using Ollama (local LLM).
Uses ChromaDB for semantic skill matching via RAG.
Produces a GapResult for every job: matched skills, missing skills, match score.
"""

import json
import re
import os
from pathlib import Path
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import AIMessage
from agents.state import JobScanState, GapResult

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHROMA_DIR = str(Path(__file__).parent.parent / "data" / "chroma_db")

ANALYSE_PROMPT = """You are an expert resume and job description analyser.

Candidate resume:
\"\"\"
{resume_text}
\"\"\"

Job listing:
Title: {job_title} at {company}
Required skills: {skills_required}
Description: {description}

Compare the resume to the job listing carefully. 
Respond ONLY with a valid JSON object. No markdown, no explanation, no extra text.

{{
  "matched_skills": ["list of skills the candidate HAS that the job requires"],
  "missing_skills": ["list of skills the job requires that the candidate LACKS"],
  "match_score": <integer 0-100>,
  "recommendation": "<one sentence: should they apply and why>"
}}"""


def _parse_json_safe(text: str) -> dict:
    """Strip markdown fences and parse JSON robustly."""
    text = re.sub(r"```json|```", "", text).strip()
    # Find first { ... } block in case model adds preamble
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _build_vectorstore(job_listings: list, embeddings) -> Chroma:
    """Index job descriptions into ChromaDB for semantic search."""
    docs = [
        f"Job: {j['title']} at {j['company']}\nSkills: {', '.join(j['skills_required'])}\n{j['description']}"
        for j in job_listings
    ]
    ids = [str(j["id"]) for j in job_listings]
    vectorstore = Chroma(
        collection_name="hk_jobs",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    vectorstore.add_texts(texts=docs, ids=ids)
    return vectorstore


def analyser_node(state: JobScanState) -> dict:
    """
    For each job listing, asks Ollama to compare the resume and return
    matched skills, missing skills, and a match score.
    """
    print(f"\n[Analyser Agent] Starting gap analysis with Ollama ({OLLAMA_MODEL})...")

    resume_text = state["resume_text"]
    job_listings = state["job_listings"]

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        format="json",
    )

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_BASE_URL,
    )

    # Build ChromaDB index (demonstrates RAG pattern)
    print("[Analyser Agent] Indexing job descriptions into ChromaDB...")
    _build_vectorstore(job_listings, embeddings)

    gap_results: list[GapResult] = []

    for i, job in enumerate(job_listings):
        print(f"[Analyser Agent] Analysing job {i+1}/{len(job_listings)}: {job['title']} @ {job['company']}")

        prompt = ANALYSE_PROMPT.format(
            resume_text=resume_text,
            job_title=job["title"],
            company=job["company"],
            skills_required=", ".join(job["skills_required"]),
            description=job["description"],
        )

        try:
            response = llm.invoke(prompt)
            parsed = _parse_json_safe(response.content)
            #print(f"id: {job["id"]}, llm response: {parsed}\n")
            
            #tomorrow analyze and optimize
            gap_results.append({
                "job_id": job["id"],
                "job_title": job["title"],
                "company": job["company"],
                "category": job["category"],
                "matched_skills": parsed.get("matched_skills", []),
                "missing_skills": parsed.get("missing_skills", []),
                "match_score": int(parsed.get("match_score", 0)),
                "recommendation": parsed.get("recommendation", ""),
            })

        except Exception as e:
            print(f"[Analyser Agent] Warning: failed to parse response for job {job['id']}: {e}")
            gap_results.append({
                "job_id": job["id"],
                "job_title": job["title"],
                "company": job["company"],
                "category": job["category"],
                "matched_skills": [],
                "missing_skills": job["skills_required"],
                "match_score": 0,
                "recommendation": "Could not analyse — check Ollama connection.",
            })

    # Sort by match score descending
    gap_results.sort(key=lambda x: x["match_score"], reverse=True)

    print(f"[Analyser Agent] Gap analysis complete. Top match: {gap_results[0]['job_title']} ({gap_results[0]['match_score']}%)")

    return {
        "gap_results": gap_results,
        "messages": [AIMessage(
            content=f"Analyser Agent: Completed gap analysis for {len(gap_results)} jobs. "
                    f"Top match: {gap_results[0]['job_title']} at {gap_results[0]['company']} "
                    f"({gap_results[0]['match_score']}% match)."
        )]
    }
