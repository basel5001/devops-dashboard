![CI](https://github.com/basel5001/devops-dashboard/actions/workflows/ci.yml/badge.svg)
![Security](https://github.com/basel5001/devops-dashboard/actions/workflows/security.yml/badge.svg)

# DevOps Dashboard - DORA Metrics

A Python FastAPI application that collects [DORA metrics](https://dora.dev/) from GitHub repositories and displays them in a real-time web dashboard.

## Architecture

```
devops-dashboard/
├── src/
│   ├── collectors/
│   │   └── github_collector.py   # GitHub API metrics collector
│   ├── api/
│   │   └── main.py               # FastAPI application
│   └── dashboard/
│       └── index.html             # Single-page dashboard UI
├── tests/
│   ├── test_collector.py          # Collector unit tests
│   └── test_api.py                # API endpoint tests
├── .github/workflows/
│   ├── ci.yml                     # CI pipeline (test + lint + docker)
│   ├── security.yml               # Security scanning
│   └── renovate.yml               # Dependency updates
├── Dockerfile                     # Multi-stage container build
├── docker-compose.yml             # Docker Compose config
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
└── pyproject.toml                 # Ruff + pytest config
```

## DORA Metrics

The dashboard tracks the four key DORA metrics:

| Metric | Description | How We Measure |
|--------|-------------|----------------|
| **Deployment Frequency** | How often code is deployed to production | Count of merged PRs per week |
| **Lead Time for Changes** | Time from first commit to production | Average time from first commit on branch to PR merge |
| **Mean Time to Recovery (MTTR)** | How quickly service is restored after an incident | Average time from issue labeled `bug`/`incident` to close |
| **Change Failure Rate (CFR)** | Percentage of deployments causing failures | Ratio of PRs with `revert`/`hotfix`/`rollback` in title |

### DORA Performance Benchmarks

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| Deploy Frequency | >1/day | 1/week-1/day | 1/month-1/week | <1/month |
| Lead Time | <1 hour | <1 day | <1 week | >1 week |
| MTTR | <1 hour | <1 day | <1 week | >1 week |
| Change Failure Rate | 0-5% | 5-10% | 10-15% | >15% |

## Screenshots

<!-- Add screenshots of the dashboard here -->
*Dashboard with dark theme, metric cards, and trend charts.*

## Quick Start

### Prerequisites

- Python 3.11+
- A GitHub personal access token with `repo` scope

### Local Development

```bash
# Clone the repository
git clone https://github.com/basel5001/devops-dashboard.git
cd devops-dashboard

# Install dependencies
make install-dev

# Configure environment
cp .env.example .env
# Edit .env with your GitHub token

# Run the development server
make dev

# Open http://localhost:8000 in your browser
```

### Docker

```bash
# Build and run with Docker Compose
cp .env.example .env
# Edit .env with your GitHub token

make docker-build
make docker-run

# Open http://localhost:8000
```

### Running Tests

```bash
make test
```

### Linting

```bash
make lint
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Dashboard HTML page |
| `GET` | `/health` | Health check |
| `GET` | `/api/metrics/{owner}/{repo}?days=30` | Fetch DORA metrics |
| `GET` | `/api/metrics/{owner}/{repo}/history` | Metrics history |

### Example

```bash
curl http://localhost:8000/api/metrics/facebook/react?days=30
```

```json
{
  "deployment_frequency": 12.5,
  "lead_time_hours": 18.3,
  "mttr_hours": 4.2,
  "change_failure_rate": 3.1,
  "period_days": 30,
  "repo_name": "facebook/react",
  "collected_at": "2024-01-15T10:30:00+00:00"
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub personal access token with `repo` scope | Yes |
| `PORT` | Application port (default: `8000`) | No |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
