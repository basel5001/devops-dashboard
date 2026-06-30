# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email the maintainers at **security@example.com** with details of the vulnerability.
3. Include steps to reproduce, potential impact, and any suggested fixes.
4. You should receive an acknowledgment within **48 hours**.
5. We will work with you to understand and address the issue before any public disclosure.

## Security Practices

- **Secrets**: GitHub tokens are never logged or stored in plain text. Use environment variables or a secrets manager.
- **Dependencies**: We use Renovate for automated dependency updates and run security scanning in CI.
- **Docker**: The container runs as a non-root user with a minimal base image.
- **CORS**: Configure allowed origins appropriately for production deployments.

## Disclosure Policy

We follow coordinated disclosure. We ask that you give us reasonable time to address the issue before making any information public.
