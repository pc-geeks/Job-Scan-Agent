# Job Scan Agent

**Multi-agent AI system for job gap analysis**  
Built with LangGraph + Ollama (local LLM) + ChromaDB + MCP

\---

## What It Does

You give it your resume. It analyses live AI job listings and tells you:

* Which jobs are your best matches (ranked by score)
* Exactly which skills you have vs what each job requires
* Which skills to learn to unlock more opportunities

All inference runs **locally via Ollama** — no cloud API, no cost.

\---

## Architecture

```
User (resume + job title)
        │
        ▼
┌─────────────────────┐
│  Supervisor Agent   │  ← LangGraph StateGraph
│  (routing logic)    │
└─────────┬───────────┘
          │
    ┌─────┴──────┬──────────────┐
    ▼            ▼              ▼
Scraper      Analyser       Report
Agent         Agent          Agent
    │            │              │
Adzuna API   Ollama LLM    Writes .md
+ ChromaDB   gap analysis   report
    │            │              │
    └────────────┴──────────────┘
                 │
         LangGraph shared state
         (job listings, gap results,
          messages, report path)
```

**Stack:**

|Component|Tool|
|-|-|
|Orchestration|LangGraph StateGraph|
|LLM|Ollama (llama3.2 / qwen2.5)|
|Embeddings|Ollama nomic-embed-text|
|Vector store|ChromaDB|
|Tool protocol|MCP (Filesystem server)|
|Output|Markdown report|

\---

## Setup

### 1\. Install Ollama

Download from https://ollama.com and pull the models:

```bash
ollama pull llama3.2          # 4.7 GB, works on 8 GB RAM
ollama pull nomic-embed-text  # 274 MB, for embeddings
```

Optional — better results with more RAM:

```bash
ollama pull qwen2.5:14b       # 9 GB, needs 16 GB RAM
```

### 2\. Install Python dependencies

```bash
cd job\\\_scan\\\_agent
pip install -r requirements.txt
```

### 3\. Run

```bash
# With the included sample resume
python main.py

# With your own resume (txt or pdf)
python main.py --resume path/to/your\\\_cv.pdf

# Use a different Ollama model
python main.py --resume cv.pdf --model qwen2.5:14b
```

\---

## Output

The agent prints a ranked table to your terminal and saves a full Markdown report to `output/`:

```
╭─────────────────────────────────────────╮
│ JobScan Agent                           │
│ Multi-agent Job Gap Analyser            │
│ LangGraph + Ollama (llama3.2) + ChromaDB│
╰─────────────────────────────────────────╯

Job Match Results
┌──────┬─────────────────────┬────────────────┬──────────────────┬───────┬──────────────────┐
│ Rank │ Job Title           │ Company        │ Category         │ Match │ Top Missing Skill│
├──────┼─────────────────────┼────────────────┼──────────────────┼───────┼──────────────────┤
│    1 │ LLM Application Dev │ Tech Aalto     │ IT Jobs          │  82%  │ LangGraph        │
│    2 │ AI Engineer         │ Virtuos        │ Engineering Jobs │  78%  │ Docker           │
│  ... │ ...                 │ ...            │ ...              │  ...  │ ...              │
└──────┴─────────────────────┴────────────────┴──────────────────┴───────┴──────────────────┘

Report saved: output/jobscan\\\_report\\\_20260624\\\_195457.md
```

\---

## MCP Filesystem Server (optional)

The project includes an MCP-compliant Filesystem server that can be used independently:

```bash
python mcp\\\_servers/filesystem\\\_server.py
```

This exposes `read\\\_file`, `write\\\_file`, and `list\\\_files` as MCP tools — compatible with any MCP client (Claude Desktop, custom agent, etc.).

\---

## Summary

* Designed a 3-node LangGraph `StateGraph` (Scraper → Analyser → Report) with supervisor routing and typed shared state across agents
* Integrated Ollama local LLM inference (`llama3.2`) with `nomic-embed-text` embeddings — zero cloud dependency, zero API cost
* Built a RAG pipeline with ChromaDB to index live job descriptions and perform semantic skill-gap analysis against candidate resume
* Implemented an MCP-compliant Filesystem tool server exposing `read\\\_file`/`write\\\_file` tools via the Model Context Protocol SDK
* Generated structured gap analysis reports (matched skills, missing skills, ranked match scores) as Markdown output

\---

## Project Structure

```
job\\\_scan\\\_agent/
├── agents/
│   ├── state.py               # TypedDict shared state (JobScanState)
│   ├── supervisor.py          # LangGraph StateGraph + routing logic
│   ├── scraper\\\_agent.py       # Fetching live jobs from Adzuna API
│   ├── analyser\\\_agent.py      # Ollama LLM + ChromaDB gap analysis
│   └── report\\\_agent.py        # Markdown report writer
├── mcp\\\_servers/
│   └── filesystem\\\_server.py   # MCP tool server (read/write files)
├── data/
│   └── sample\\\_resume.txt      # Sample resume for testing
├── output/                    # Generated reports go here
├── main.py                    # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

