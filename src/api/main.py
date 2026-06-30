"""FastAPI application for DORA metrics dashboard."""
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.collectors.github_collector import DORAMetrics, collect_metrics

load_dotenv()

app = FastAPI(
    title="DevOps Dashboard",
    description="DORA Metrics Dashboard - Track your team's software delivery performance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history store (replace with a database in production)
_metrics_history: dict[str, list[dict]] = {}

DASHBOARD_PATH = Path(__file__).parent.parent / "dashboard" / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard HTML page."""
    if not DASHBOARD_PATH.exists():
        raise HTTPException(status_code=404, detail="Dashboard HTML not found")
    return DASHBOARD_PATH.read_text()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
    }


@app.get("/api/metrics/{owner}/{repo}")
async def get_metrics(
    owner: str,
    repo: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    token: Optional[str] = Query(default=None, description="GitHub token (overrides env var)"),
):
    """Fetch DORA metrics for a GitHub repository."""
    github_token = token or os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub token is required. Set GITHUB_TOKEN env var or pass ?token=...",
        )

    repo_name = f"{owner}/{repo}"
    try:
        metrics = collect_metrics(repo_name, github_token, days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to collect metrics: {e}")

    # Store in history
    metrics_dict = {
        "deployment_frequency": metrics.deployment_frequency,
        "lead_time_hours": metrics.lead_time_hours,
        "mttr_hours": metrics.mttr_hours,
        "change_failure_rate": metrics.change_failure_rate,
        "period_days": metrics.period_days,
        "repo_name": metrics.repo_name,
        "collected_at": metrics.collected_at,
    }
    _metrics_history.setdefault(repo_name, []).append(metrics_dict)
    # Keep last 100 entries per repo
    _metrics_history[repo_name] = _metrics_history[repo_name][-100:]

    return metrics_dict


@app.get("/api/metrics/{owner}/{repo}/history")
async def get_metrics_history(owner: str, repo: str):
    """Get historical DORA metrics for a repository."""
    repo_name = f"{owner}/{repo}"
    history = _metrics_history.get(repo_name, [])
    return {"repo": repo_name, "entries": history, "count": len(history)}
