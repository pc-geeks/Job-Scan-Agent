# JobScan Agent

**Multi-agent AI system for Hong Kong AI job gap analysis**  
Built with LangGraph + Ollama (local LLM) + ChromaDB + MCP

---

## What It Does

You give it your resume. It analyses every HK AI job listing and tells you:
- Which jobs are your best matches (ranked by score)
- Exactly which skills you have vs what each job requires
- Which skills to learn to unlock more opportunities

All inference runs **locally via Ollama** — no cloud API, no cost.

---

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
    ┌─────┴──────┐──────────────┐
    ▼            ▼              ▼
Scraper      Analyser       Report
Agent        Agent          Agent
    │            │              │
Reads JSON   Ollama LLM    Writes .md
+ ChromaDB   gap analysis   report
    │            │              │
    └────────────┴──────────────┘
                 │
         LangGraph shared state
         (job listings, gap results,
          messages, report path)
```

**Stack:**
| Component | Tool |
|-----------|------|
| Orchestration | LangGraph StateGraph |
| LLM | Ollama (llama3.2 / qwen2.5) |
| Embeddings | Ollama nomic-embed-text |
| Vector store | ChromaDB |
| Tool protocol | MCP (Filesystem server) |
| Output | Markdown report |

---

## Setup

### 1. Install Ollama

Download from https://ollama.com and pull the models:

```bash
ollama pull llama3.2          # 4.7 GB, works on 8 GB RAM
ollama pull nomic-embed-text  # 274 MB, for embeddings
```

Optional — better results with more RAM:
```bash
ollama pull qwen2.5:14b       # 9 GB, needs 16 GB RAM
```

### 2. Install Python dependencies

```bash
cd jobscan_agent
pip install -r requirements.txt
```

### 3. Run

```bash
# With the included sample resume
python main.py

# With your own resume (txt or pdf)
python main.py --resume path/to/your_cv.pdf

# Use a different Ollama model
python main.py --resume cv.pdf --model qwen2.5:14b
```

---

## Output

The agent prints a ranked table to your terminal and saves a full Markdown report to `output/`:

```
╭─────────────────────────────────────────╮
│ JobScan Agent                           │
│ Multi-agent HK AI Job Gap Analyser      │
│ LangGraph + Ollama (llama3.2) + ChromaDB│
╰─────────────────────────────────────────╯

Job Match Results
┌──────┬─────────────────────────┬──────────────────┬────────────────────────┬───────┬──────────────────┐
│ Rank │ Job Title               │ Company          │ Salary                 │ Match │ Top Missing Skill│
├──────┼─────────────────────────┼──────────────────┼────────────────────────┼───────┼──────────────────┤
│    1 │ LLM Application Dev     │ AI Startup HK    │ HKD 35,000-55,000/mo  │  82%  │ LangGraph        │
│    2 │ AI Engineer             │ FinTech HK Ltd   │ HKD 40,000-60,000/mo  │  78%  │ Docker           │
│ ...  │ ...                     │ ...              │ ...                    │  ...  │ ...              │
└──────┴─────────────────────────┴──────────────────┴────────────────────────┴───────┴──────────────────┘

Report saved: output/jobscan_report_20240624_143022.md
```

---

## MCP Filesystem Server (optional)

The project includes an MCP-compliant Filesystem server that can be used independently:

```bash
python mcp_servers/filesystem_server.py
```

This exposes `read_file`, `write_file`, and `list_files` as MCP tools — compatible with any MCP client (Claude Desktop, custom agent, etc.).

---

## Customising the Job Dataset

Edit `data/hk_ai_jobs.json` to add real job listings you find on JobsDB or LinkedIn.
Each entry follows this schema:

```json
{
  "id": 11,
  "title": "AI Engineer",
  "company": "Your Target Company",
  "location": "Hong Kong",
  "skills_required": ["Python", "LangGraph", "Docker"],
  "description": "Full job description text here...",
  "salary": "HKD 50,000/month",
  "type": "Full-time"
}
```

---

## Resume Bullet Points (for your CV)

- Designed a 3-node LangGraph `StateGraph` (Scraper → Analyser → Report) with supervisor routing and typed shared state across agents
- Integrated Ollama local LLM inference (`llama3.2`) with `nomic-embed-text` embeddings — zero cloud dependency, zero API cost
- Built a RAG pipeline with ChromaDB to index 10+ HK job descriptions and perform semantic skill-gap analysis against candidate resume
- Implemented an MCP-compliant Filesystem tool server exposing `read_file`/`write_file` tools via the Model Context Protocol SDK
- Generated structured gap analysis reports (matched skills, missing skills, ranked match scores) as Markdown output

---

## Project Structure

```
jobscan_agent/
├── agents/
│   ├── state.py           # TypedDict shared state (JobScanState)
│   ├── supervisor.py      # LangGraph StateGraph + routing logic
│   ├── scraper_agent.py   # Loads job listings
│   ├── analyser_agent.py  # Ollama LLM + ChromaDB gap analysis
│   └── report_agent.py    # Markdown report writer
├── mcp_servers/
│   └── filesystem_server.py  # MCP tool server (read/write files)
├── data/
│   ├── hk_ai_jobs.json    # HK AI job listings dataset
│   └── sample_resume.txt  # Sample resume for testing
├── output/                # Generated reports go here
├── main.py                # Entry point
├── requirements.txt
├── .env.example
└── README.md
```
