# `infra/`

Infrastructure-as-code for both local development and AWS deployment.

| Subdir | Purpose | Primary epic |
|---|---|---|
| `compose/` | `docker-compose.yml` orchestrating `api`, `worker`, `web`, `db`, `localstack`. | E8 |
| `terraform/` | AWS modules (`network`, `data`, `services`) + per-env workspaces (`dev`, `prod`). | E9 |

Both are placeholders until their respective epics begin.

## Conventions

- **Compose** is the single source of truth for the local dev environment. The `foresight.api` and `foresight.worker` containers plus the Next.js `web/` app must all be reachable via `docker-compose up`.
- **Terraform** state lives in S3 with DynamoDB locking. The first `terraform apply` from a clean checkout creates only `dev`; promoting changes to `prod` is a deliberate, reviewed action.
- **Secrets** never live in this tree. Local secrets go in `.env` (gitignored); cloud secrets live in AWS Secrets Manager and are resolved at runtime by `foresight.settings`.
