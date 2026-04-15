# Security Policy

## Local Secret Handling

- Do not commit real secrets into source control.
- Keep real credentials only in local env files or a secret manager.
- Treat `apps/api/.env.example` as template-only.
- `apps/api/.env` is for local development defaults and should remain non-sensitive.

## Recommended Practices

- Rotate API keys if accidental exposure is suspected.
- Use least-privilege credentials for all third-party integrations.
- Prefer separate keys per environment (dev/staging/prod).
- Use PostgreSQL in production; avoid SQLite for production workloads.

## Pre-Push Secret Check

Run:

```powershell
./scripts/prepush-secret-check.ps1
```

The script inspects staged patches for common credential formats and fails fast if suspicious content is found.

## Reporting a Vulnerability

If you discover a vulnerability, report it privately to the project maintainers with:

- A clear description
- Reproduction steps
- Affected files or endpoints
- Suggested mitigation
