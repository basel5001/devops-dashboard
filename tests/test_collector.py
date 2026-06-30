"""Tests for the GitHub metrics collector."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.collectors.github_collector import DORAMetrics, collect_metrics


def _make_mock_pr(title, merged, merged_at, commit_dates=None):
    """Create a mock PR object."""
    pr = MagicMock()
    pr.title = title
    pr.merged = merged
    pr.merged_at = merged_at

    if commit_dates:
        commits = []
        for dt in commit_dates:
            c = MagicMock()
            c.commit.author.date = dt
            commits.append(c)
        pr.get_commits.return_value = commits
    else:
        pr.get_commits.return_value = []

    return pr


def _make_mock_issue(labels, created_at, closed_at):
    """Create a mock issue object."""
    issue = MagicMock()
    mock_labels = []
    for name in labels:
        lbl = MagicMock()
        lbl.name = name
        mock_labels.append(lbl)
    issue.labels = mock_labels
    issue.created_at = created_at
    issue.closed_at = closed_at
    return issue


class TestDORAMetrics:
    """Tests for the DORAMetrics dataclass."""

    def test_dataclass_creation(self):
        m = DORAMetrics(
            deployment_frequency=5.0,
            lead_time_hours=12.5,
            mttr_hours=2.0,
            change_failure_rate=8.5,
            period_days=30,
            repo_name="owner/repo",
            collected_at="2024-01-01T00:00:00",
        )
        assert m.deployment_frequency == 5.0
        assert m.lead_time_hours == 12.5
        assert m.mttr_hours == 2.0
        assert m.change_failure_rate == 8.5
        assert m.period_days == 30
        assert m.repo_name == "owner/repo"


class TestCollectMetrics:
    """Tests for the collect_metrics function."""

    @patch("src.collectors.github_collector.Github")
    def test_basic_metrics_collection(self, mock_github_class):
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Set up merged PRs
        prs = [
            _make_mock_pr(
                "feat: add feature",
                merged=True,
                merged_at=now - timedelta(hours=5),
                commit_dates=[now - timedelta(hours=10)],
            ),
            _make_mock_pr(
                "fix: bug fix",
                merged=True,
                merged_at=now - timedelta(hours=12),
                commit_dates=[now - timedelta(hours=20)],
            ),
        ]

        # Set up issues
        issues = [
            _make_mock_issue(
                ["bug"],
                created_at=now - timedelta(hours=48),
                closed_at=now - timedelta(hours=24),
            ),
        ]

        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = prs
        mock_repo.get_issues.return_value = issues
        mock_github_class.return_value.get_repo.return_value = mock_repo

        result = collect_metrics("owner/repo", "fake-token", days=30)

        assert isinstance(result, DORAMetrics)
        assert result.repo_name == "owner/repo"
        assert result.period_days == 30
        assert result.deployment_frequency > 0
        assert result.lead_time_hours > 0
        assert result.change_failure_rate == 0.0  # no revert/hotfix PRs
        assert result.mttr_hours > 0

    @patch("src.collectors.github_collector.Github")
    def test_change_failure_rate_with_hotfix(self, mock_github_class):
        now = datetime.now(timezone.utc)

        prs = [
            _make_mock_pr("feat: add widget", merged=True, merged_at=now - timedelta(hours=1)),
            _make_mock_pr("hotfix: fix crash", merged=True, merged_at=now - timedelta(hours=2)),
            _make_mock_pr("Revert: bad change", merged=True, merged_at=now - timedelta(hours=3)),
            _make_mock_pr("fix: typo", merged=True, merged_at=now - timedelta(hours=4)),
        ]

        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = prs
        mock_repo.get_issues.return_value = []
        mock_github_class.return_value.get_repo.return_value = mock_repo

        result = collect_metrics("owner/repo", "fake-token", days=30)

        # "hotfix" + "Revert" + "fix:" = 3 out of 4 = 75%
        assert result.change_failure_rate == 75.0

    @patch("src.collectors.github_collector.Github")
    def test_no_merged_prs(self, mock_github_class):
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        mock_repo.get_issues.return_value = []
        mock_github_class.return_value.get_repo.return_value = mock_repo

        result = collect_metrics("owner/repo", "fake-token", days=30)

        assert result.deployment_frequency == 0.0
        assert result.lead_time_hours == 0.0
        assert result.change_failure_rate == 0.0

    @patch("src.collectors.github_collector.Github")
    def test_no_incidents(self, mock_github_class):
        now = datetime.now(timezone.utc)
        prs = [
            _make_mock_pr("feat: something", merged=True, merged_at=now - timedelta(hours=1)),
        ]
        # Issues without bug/incident labels
        issues = [
            _make_mock_issue(
                ["enhancement"],
                created_at=now - timedelta(hours=48),
                closed_at=now - timedelta(hours=24),
            ),
        ]

        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = prs
        mock_repo.get_issues.return_value = issues
        mock_github_class.return_value.get_repo.return_value = mock_repo

        result = collect_metrics("owner/repo", "fake-token", days=30)

        assert result.mttr_hours == 0.0

    @patch("src.collectors.github_collector.Github")
    def test_collected_at_is_iso_format(self, mock_github_class):
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        mock_repo.get_issues.return_value = []
        mock_github_class.return_value.get_repo.return_value = mock_repo

        result = collect_metrics("owner/repo", "fake-token", days=7)

        # Should parse without error
        dt = datetime.fromisoformat(result.collected_at)
        assert dt.tzinfo is not None or "+" in result.collected_at

    @patch("src.collectors.github_collector.Github")
    def test_custom_days_parameter(self, mock_github_class):
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        mock_repo.get_issues.return_value = []
        mock_github_class.return_value.get_repo.return_value = mock_repo

        result = collect_metrics("owner/repo", "fake-token", days=90)

        assert result.period_days == 90
