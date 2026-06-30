"""Tests for the FastAPI application."""
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app, _metrics_history
from src.collectors.github_collector import DORAMetrics


@pytest.fixture
def client():
    """Create a test client."""
    _metrics_history.clear()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_format(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestDashboardEndpoint:
    """Tests for the dashboard HTML endpoint."""

    def test_dashboard_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "DORA" in response.text


class TestMetricsEndpoint:
    """Tests for the metrics API endpoint."""

    def test_metrics_without_token_returns_401(self, client):
        with patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/metrics/owner/repo")
            assert response.status_code == 401
            assert "token" in response.json()["detail"].lower()

    @patch("src.api.main.collect_metrics")
    def test_metrics_with_valid_token(self, mock_collect, client):
        mock_collect.return_value = DORAMetrics(
            deployment_frequency=5.0,
            lead_time_hours=12.5,
            mttr_hours=2.0,
            change_failure_rate=8.5,
            period_days=30,
            repo_name="owner/repo",
            collected_at="2024-01-01T00:00:00+00:00",
        )

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            response = client.get("/api/metrics/owner/repo")

        assert response.status_code == 200
        data = response.json()
        assert data["deployment_frequency"] == 5.0
        assert data["lead_time_hours"] == 12.5
        assert data["mttr_hours"] == 2.0
        assert data["change_failure_rate"] == 8.5
        assert data["repo_name"] == "owner/repo"

    @patch("src.api.main.collect_metrics")
    def test_metrics_with_query_token(self, mock_collect, client):
        mock_collect.return_value = DORAMetrics(
            deployment_frequency=3.0,
            lead_time_hours=6.0,
            mttr_hours=1.0,
            change_failure_rate=5.0,
            period_days=14,
            repo_name="owner/repo",
            collected_at="2024-01-01T00:00:00+00:00",
        )

        response = client.get("/api/metrics/owner/repo?token=my-token&days=14")
        assert response.status_code == 200
        mock_collect.assert_called_once_with("owner/repo", "my-token", 14)

    @patch("src.api.main.collect_metrics")
    def test_metrics_collection_failure_returns_502(self, mock_collect, client):
        mock_collect.side_effect = Exception("API rate limit exceeded")

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            response = client.get("/api/metrics/owner/repo")

        assert response.status_code == 502
        assert "rate limit" in response.json()["detail"].lower()

    @patch("src.api.main.collect_metrics")
    def test_metrics_custom_days(self, mock_collect, client):
        mock_collect.return_value = DORAMetrics(
            deployment_frequency=1.0,
            lead_time_hours=1.0,
            mttr_hours=1.0,
            change_failure_rate=1.0,
            period_days=7,
            repo_name="owner/repo",
            collected_at="2024-01-01T00:00:00+00:00",
        )

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            response = client.get("/api/metrics/owner/repo?days=7")

        assert response.status_code == 200
        mock_collect.assert_called_once_with("owner/repo", "test-token", 7)

    def test_metrics_invalid_days(self, client):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            response = client.get("/api/metrics/owner/repo?days=0")
        assert response.status_code == 422


class TestHistoryEndpoint:
    """Tests for the metrics history endpoint."""

    def test_empty_history(self, client):
        response = client.get("/api/metrics/owner/repo/history")
        assert response.status_code == 200
        data = response.json()
        assert data["repo"] == "owner/repo"
        assert data["entries"] == []
        assert data["count"] == 0

    @patch("src.api.main.collect_metrics")
    def test_history_after_fetch(self, mock_collect, client):
        mock_collect.return_value = DORAMetrics(
            deployment_frequency=5.0,
            lead_time_hours=12.5,
            mttr_hours=2.0,
            change_failure_rate=8.5,
            period_days=30,
            repo_name="owner/repo",
            collected_at="2024-01-01T00:00:00+00:00",
        )

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            client.get("/api/metrics/owner/repo")

        response = client.get("/api/metrics/owner/repo/history")
        data = response.json()
        assert data["count"] == 1
        assert data["entries"][0]["deployment_frequency"] == 5.0
