import requests
import os
from langchain_core.messages import AIMessage
from agents.state import JobScanState

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

def scraper_node(state: JobScanState) -> dict:
    print("\n[Scraper Agent] Fetching live jobs from Adzuna API...")

    url = "https://api.adzuna.com/v1/api/jobs/sg/search/1"
    
    params = {
        "app_id":        ADZUNA_APP_ID,
        "app_key":       ADZUNA_APP_KEY,
        "results_per_page": 20,
        "what":          "AI engineer",
        "content-type":  "application/json",
    }

    response = requests.get(url, params=params)
    data = response.json()

    job_listings = []
    for i, job in enumerate(data.get("results", [])):
        # Extract skills by keyword scanning the description
        desc = job.get("description", "")
        #print(f"Job[{i}: {job}")
        
        skills = extract_skills_from_text(desc)
        job_listings.append({
            "id":               i + 1,
            "title":            job.get("title", ""),
            "company":          job.get("company", {}).get("display_name", "Unknown"),
            "location":         job.get("location", {}).get("display_name", "Singapore"),
            "skills_required":  skills,
            "description":      desc[:1000],  # trim long descriptions
            "category":          job.get("category", {}).get("label", "N/A"), 
                                # f"HKD {job.get('salary_min', '?')} - {job.get('salary_max', '?')}",
            "type":             job.get("contract_time", "Unknown"),
        })

    print(f"[Scraper Agent] Fetched {len(job_listings)} live job listings.")
    return {
        "job_listings": job_listings,
        "messages": [AIMessage(content=f"Scraper Agent: Fetched {len(job_listings)} live Singapore AI jobs from Adzuna.")]
    }


SKILL_KEYWORDS = [
    "Python", "PyTorch", "TensorFlow", "LangChain", "LangGraph", "LLM",
    "RAG", "Docker", "Kubernetes", "FastAPI", "SQL", "PostgreSQL",
    "Machine Learning", "Deep Learning", "NLP", "Transformer", "Ollama",
    "AWS", "GCP", "Azure", "MLflow", "Hugging Face", "React", "TypeScript",
    "ChromaDB", "Redis", "Fine-tuning", "RLHF", "OpenCV", "MCP",
]

def extract_skills_from_text(text: str) -> list[str]:
    """Simple keyword scan to pull skills from job description text."""
    text_lower = text.lower()
    return [s for s in SKILL_KEYWORDS if s.lower() in text_lower]