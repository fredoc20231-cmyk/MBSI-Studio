# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a vulnerability

Please report security vulnerabilities privately rather than opening a public issue.

- Use GitHub's **"Report a vulnerability"** button under the repository's **Security** tab
  (Private Vulnerability Reporting), or
- Contact the maintainers directly through the channel listed in the repository profile.

Include, where possible:
- A description of the vulnerability and its impact.
- Steps to reproduce (proof-of-concept, affected endpoint or loader, sample input).
- Affected version(s) and environment.

We aim to acknowledge reports within **5 business days** and to provide a remediation
timeline after triage.

## Scope and data-handling notes

MBSI Studio processes user-supplied spatial-omics files and exposes an HTTP API.
When deploying:

- **Do not** expose the development server (`--reload`, permissive CORS) to untrusted
  networks. Use the production profile (`docker-compose.prod.yml`).
- Treat all uploaded files as untrusted input; run the service with least-privilege
  filesystem access to `data/uploads` and `data/outputs`.
- Configure `MBSI_CORS_ALLOW_ORIGINS` to an explicit allowlist in production instead of `*`.
- Never commit secrets. Use `.env` (git-ignored) derived from `.env.example`.

## Research-use disclaimer

Outputs are computational research artifacts, not diagnostic or clinical decision-support.
See the in-app biomarker disclaimer for details.
