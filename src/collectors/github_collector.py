"""GitHub metrics collector for DORA metrics."""
import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from github import Github


@dataclass
class DORAMetrics:
    deployment_frequency: float  # deploys per week
    lead_time_hours: float  # avg hours from commit to deploy
    mttr_hours: float  # avg hours to recover from incidents
    change_failure_rate: float  # percentage of failed changes
    period_days: int
    repo_name: str
    collected_at: str


def collect_metrics(repo_name: str, token: str, days: int = 30) -> DORAMetrics:
    """Collect DORA metrics from a GitHub repository."""
    g = Github(token)
    repo = g.get_repo(repo_name)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Deployment Frequency: merged PRs as proxy for deployments
    merged_prs = list(repo.get_pulls(state="closed", sort="updated", direction="desc"))
    recent_merges = [
        pr for pr in merged_prs
        if pr.merged and pr.merged_at and pr.merged_at.replace(tzinfo=timezone.utc) > since
    ]
    weeks = max(days / 7, 1)
    deploy_freq = len(recent_merges) / weeks
    
    # Lead Time: avg time from first commit to merge
    lead_times = []
    for pr in recent_merges[:50]:  # sample last 50
        commits = list(pr.get_commits())
        if commits and pr.merged_at:
            first_commit = commits[0].commit.author.date.replace(tzinfo=timezone.utc)
            merged = pr.merged_at.replace(tzinfo=timezone.utc)
            delta = (merged - first_commit).total_seconds() / 3600
            if delta > 0:
                lead_times.append(delta)
    avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
    
    # Change Failure Rate: PRs with "revert" or "hotfix" in title
    failure_count = sum(
        1 for pr in recent_merges
        if any(kw in (pr.title or "").lower() for kw in ["revert", "hotfix", "rollback", "fix:"])
    )
    cfr = (failure_count / len(recent_merges) * 100) if recent_merges else 0
    
    # MTTR: avg time to close issues labeled "bug" or "incident"
    issues = list(repo.get_issues(state="closed", since=since, labels=[]))
    incident_times = []
    for issue in issues:
        labels = [l.name.lower() for l in issue.labels]
        if any(kw in labels for kw in ["bug", "incident", "outage"]):
            if issue.closed_at and issue.created_at:
                created = issue.created_at.replace(tzinfo=timezone.utc)
                closed = issue.closed_at.replace(tzinfo=timezone.utc)
                delta = (closed - created).total_seconds() / 3600
                if delta > 0:
                    incident_times.append(delta)
    avg_mttr = sum(incident_times) / len(incident_times) if incident_times else 0
    
    return DORAMetrics(
        deployment_frequency=round(deploy_freq, 2),
        lead_time_hours=round(avg_lead_time, 1),
        mttr_hours=round(avg_mttr, 1),
        change_failure_rate=round(cfr, 1),
        period_days=days,
        repo_name=repo_name,
        collected_at=datetime.now(timezone.utc).isoformat(),
    )
