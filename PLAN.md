# Foresight — Refined Project Plan

## Context

Foresight is a greenfield project (only `README.md` exists today) aimed at being a data-first, AI-native operations platform for DTC / e-com brands. The current `README.md` lists five high-level "Define" TODOs that need to be broken into concrete, sequenced work.

The goal of this planning pass is to lock in the foundational decisions and produce an actionable backlog of developer stories — each with detailed, "why-explained" acceptance criteria so the next sessions can move directly into implementation.

## MVP Wedge

A **thin vertical slice across all three pillars**, end-to-end:

- **Data:** Shopify orders + inventory ingested into Postgres, raw exports landed in S3.
- **Forecast:** SKU-level stockout / days-of-cover (simplest first model; demand & revenue forecasts come after).
- **Agent:** One abstracted agent that can answer ops questions in Slack against the data layer.
- **UX:** Minimal Next.js web app for setup/dashboards + Slack as the primary agent surface.
- **Infra:** Docker Compose locally; AWS ECS Fargate as the deployment target.
- **Out of scope for MVP:** wiki/KB, "Ops Gym" RL environment, additional data sources (Klaviyo, Amazon, CSV).

## Architectural Decisions

| Area | Decision |
|---|---|
| Backend language/framework | Python + FastAPI |
| Python tooling | `uv` (project manager, lockfile, venv, runner) |
| DB | Postgres (RDS in prod), local via Docker Compose |
| Object storage | S3 (LocalStack or MinIO locally) for raw exports + ML artifacts |
| ORM / migrations | SQLAlchemy 2.x + Alembic |
| Frontend | Next.js (App Router), TypeScript |
| Node package manager | `pnpm` with security-hardened defaults (strict peer deps, no phantom deps, postinstall script allowlist, lockfile + integrity hashes committed, Dependabot enabled) |
| Git workflow | `develop` integration branch; `feature/{story-id}-{slug}` per story; PR → UAT → squash merge to `develop` |
| Agent layer | Thin abstraction (`AgentClient` protocol) — concrete framework deferred until first agent ships |
| Local infra | Docker Compose (api, db, worker, web, localstack/minio) |
| Cloud infra | AWS ECS Fargate, RDS Postgres, S3, ALB; IaC via Terraform |
| First data source | Shopify (orders + inventory) only |
| First forecast | Days-of-cover / stockout per SKU |

## Story Status

Tracks completion state per story. Updated as part of each story's documentation phase. PR links go to the squash-merge commit on `develop`.

| Story | Title | Status | PR | Merge SHA |
|---|---|---|---|---|
| E1.S0 | Git & branch bootstrap | ✅ Done | [#1](https://github.com/logankud/foresight/pull/1), [#2](https://github.com/logankud/foresight/pull/2) | `476d119`, `a9828e9` |
| E1.S1 | Initialize repo & dependency tooling | ✅ Done | [#3](https://github.com/logankud/foresight/pull/3) | `0c78cce` |
| E1.S2 | Adopt monorepo layout | ✅ Done | [#4](https://github.com/logankud/foresight/pull/4) | `f94235e` |
| E1.S3 | Makefile / dev commands | ✅ Done | [#5](https://github.com/logankud/foresight/pull/5) | `c50978e` |
| E1.S4 | Pre-commit hooks | ✅ Done | [#6](https://github.com/logankud/foresight/pull/6) | `b76b039` |
| E1.S5 | CI skeleton (GitHub Actions) | ✅ Done | [#7](https://github.com/logankud/foresight/pull/7) | `41222b6` |
| E1.S6 | Decision-rationale capture (ADRs deferred) | ✅ Done | [#8](https://github.com/logankud/foresight/pull/8) | `3f220cc` |
| E2.S0 | Minimal Postgres in compose | 🟡 In review | _(this PR)_ | — |
| E2.S1 | Define core entity models | ⚪ Pending | — | — |
| E2.S2 | Raw event landing (S3 + RawEvent table) | ⚪ Pending | — | — |
| E2.S3 | Storage abstractions (BlobStore + DB session) | ⚪ Pending | — | — |
| E2.S4 | Alembic baseline migration | ⚪ Pending | — | — |
| E2.S5 | Seed script | ⚪ Pending | — | — |

> All later epics (E2–E10) are pending. Status rows for those stories will be added as each epic's planning phase begins.

## Epics (Overview)

| ID | Epic | Theme |
|---|---|---|
| E1 | Foundations & Tooling | Repo, monorepo layout, dev tooling, CI, ADR system |
| E2 | Data Model & Storage | Entity model, raw landing, storage abstractions, migrations, seed |
| E3 | API Foundation (FastAPI) | App bootstrap, auth, schemas, error model, MVP endpoints |
| E4 | Shopify Ingestion + Worker | OAuth, backfill, webhooks, retry/ops endpoints |
| E5 | Forecasting Pipeline | Velocity, days-of-cover, artifacts, backtest |
| E6 | Agent Layer + Slack | AgentClient protocol, tools, conversation persistence, Slack adapter, eval harness |
| E7 | Web App (Next.js) | Auth, Setup, Inventory/Forecast, Agent Chat screens |
| E8 | Local Infrastructure | Compose stack, Dockerfiles, env templates |
| E9 | AWS Infrastructure | Terraform modules (network/data/services), CI image push, secrets, dev deploy |
| E10 | UX Journey Acceptance Docs | Onboard, Daily Check-in, Reorder Triggered |

## Developer Stories

Each story includes a user-story description, acceptance criteria with **what** and **why** for each item, and upstream dependencies. Story IDs (`E#.S#`) are stable and meant to be referenced from PRs, commits, and issues.

---

### E1 — Foundations & Tooling

**E1.S0 — Git & branch bootstrap**
- **User story:** As a developer, I want the repo initialized as a git repo with a `develop` integration branch and a GitHub remote, so the per-story `feature/{story}` → PR → UAT → merge workflow described in `CLAUDE.md` actually has rails to run on.
- **Acceptance criteria:**
  - `git init` performed with `main` as the default branch; an initial commit on `main` carries `README.md`, `PLAN.md`, `CLAUDE.md`, `LICENSE` (placeholder), and the expanded `.gitignore`. — *Why:* A real initial commit gives every later branch a common ancestor; without it, `git log` and PR diffs are messy.
  - `develop` branched from `main` and pushed. `main` **remains the GitHub default branch** (it's the public face of the repo and tracks releases); `CONTRIBUTING.md` documents that all feature PRs must explicitly target `develop`, and branch protection on `main` blocks accidental landings. — *Why:* Keeping `main` as default keeps the most-stable branch front-and-center for visitors; using `develop` as the integration target preserves classic gitflow without surrendering the default-branch slot to active integration work.
  - GitHub remote created via `gh repo create` (private). — *Why:* The remote is required for the first PR; creating it as part of bootstrap means E1.S1 doesn't pause on infra setup.
  - Branch protection guidance documented in `CONTRIBUTING.md` (E1.S6 will add it): require PR review on `develop`, require status checks once CI lands. — *Why:* Protection is a manual one-time GitHub UI step we can't fully automate; documenting it ensures it actually gets done.
  - `.gitignore` placeholder created with the obvious entries (`.env`, `.venv/`, `node_modules/`, `__pycache__/`, `.DS_Store`); fully populated in E1.S1. — *Why:* Even the bootstrap commit needs an ignore file or the first push pulls in editor cruft.
  - First feature branch (`feature/E1.S0-git-bootstrap`) demonstrates the workflow end-to-end: branch → commit → push → PR → user UAT → squash merge to `develop`. — *Why:* The first run proves the workflow before any real code rides on it; finding broken settings now is much cheaper than mid-E1.S1.
- **Depends on:** —

**E1.S1 — Initialize repo & dependency tooling**
- **User story:** As a developer, I want a repo bootstrapped with `uv` for Python, `pnpm` for Node, a complete `.gitignore`, and a `LICENSE`, so dependency installs are deterministic, secure-by-default, and ready for everything downstream.
- **Acceptance criteria:**
  - `pyproject.toml` declares Python ≥3.11, project name `foresight`, and dependency groups (`dev`, `test`, `lint`); `uv.lock` committed. — *Why:* Modern Python features (PEP 695 type params, `tomllib`) require ≥3.11; uv's lockfile is deterministic across machines and replaces pip/pip-tools; group-scoped installs let CI install only what each job needs.
  - `uv sync` succeeds with no warnings on a clean checkout; `uv run python -c "import foresight"` works after the package is created. — *Why:* `uv sync` is the canonical install path — it must be clean from day one or onboarding immediately stalls.
  - `web/package.json` declares `next`, `react`, `react-dom`, `typescript`; `pnpm-lock.yaml` committed; `engines.node` and `packageManager` pinned. — *Why:* `packageManager` in package.json (Corepack) prevents contributors from accidentally using npm/yarn against a pnpm lockfile, which is the single biggest source of phantom-dep bugs.
  - Security-hardened pnpm config in `web/.npmrc`: `auto-install-peers=true`, `strict-peer-dependencies=true`, `enable-pre-post-scripts=false` with explicit allowlist via `onlyBuiltDependencies`, `verify-store-integrity=true`. — *Why:* These flags collectively block phantom deps, malicious postinstall scripts (a top npm attack class), and tampered cache; they're the cheapest defense-in-depth available.
  - `.gitignore` excludes `.venv/`, `node_modules/`, `.env`, `.env.*` (except `.env.example`), `dist/`, `build/`, `__pycache__/`, `*.pyc`, `.next/`, `.DS_Store`, `.idea/`, `.vscode/` (allow `.vscode/extensions.json`). — *Why:* Build outputs bloat the repo and `.env` can leak secrets; excluding day-one avoids history-rewriting cleanups later. Allowing `.vscode/extensions.json` keeps shared IDE recommendations without leaking personal settings.
  - `LICENSE` file present at repo root. — *Why:* GitHub and many tools key off LICENSE presence; even a placeholder signals intent and keeps later license selection a one-line change.
  - `.github/dependabot.yml` configured for both Python (`uv`/`pip`) and `npm` ecosystems with weekly cadence on `develop`. — *Why:* Security updates that require human action don't happen; Dependabot turns it into review-and-merge.
- **Depends on:** E1.S0

**E1.S2 — Adopt monorepo layout**
- **User story:** As a developer, I want the agreed monorepo skeleton committed with placeholder modules, so future code lands in predictable places.
- **Acceptance criteria:**
  - Directory tree matches `foresight/{core,agents,api,worker}/`, `tests/`, `web/`, `infra/{compose,terraform}`, `scripts/`, `docs/`. — *Why:* A predictable layout removes the daily "where does this go?" cognitive tax and makes onboarding faster. (Originally planned as a uv workspace with `packages/{core,agents}` and `services/{api,worker}`; collapsed to a single `foresight` package with subpackages after user review for simpler mental model.)
  - Every subpackage has `__init__.py`; pytest discovers all four subpackages. — *Why:* Without proper package markers, imports look fine but break in CI; verifying discovery prevents a confusing class of test failures.
  - tsconfig path aliases (`@/*` → `web/`) resolve in both editor and `next build`. — *Why:* Aliases keep import paths stable as files move; verifying both editor and build prevents drift between IDE and CI.
  - Layering rule codified: `foresight.core` cannot import from `foresight.api`, `foresight.worker`, or `foresight.agents`; `foresight.api` and `foresight.worker` cannot import from each other; `foresight.agents` may import from `foresight.core` only. — *Why:* Layered dependencies keep the data layer reusable and testable in isolation; codifying the rule early avoids a costly untangle later. Documented in `foresight/__init__.py` and `CONTRIBUTING.md`; will be machine-enforced via `import-linter` in E1.S4.
- **Depends on:** E1.S1

**E1.S3 — Makefile / dev commands**
- **User story:** As a developer, I want one-line commands (`make up/migrate/seed/test/fmt/lint`), so I don't have to memorize per-service incantations.
- **Acceptance criteria:**
  - Each target works on a clean clone (Docker installed): boot stack, run alembic, populate seed, run all suites, format/lint. — *Why:* Memorizable verbs lower the barrier for new contributors and reduce typos that take down local envs.
  - `make help` lists every target with one-line descriptions. — *Why:* Self-documenting Makefiles eliminate "what targets exist?" Slack questions and stay accurate as targets change.
  - Targets fail fast and noisily on missing prerequisites (Docker daemon, env vars). — *Why:* Silent partial failures waste hours; clear error messages surface root causes immediately.
  - No target hardcodes a contributor's home directory or local path. — *Why:* Portable Makefiles work in CI, dev containers, and across OSes without per-machine edits.
- **Depends on:** E1.S2

**E1.S4 — Pre-commit hooks**
- **User story:** As a developer, I want pre-commit running ruff + black + mypy + eslint + prettier before each commit, so style/type issues are caught locally.
- **Acceptance criteria:**
  - `pre-commit install` succeeds and `.pre-commit-config.yaml` lives at repo root. — *Why:* Project-level hook config means new clones get the same checks without per-machine setup.
  - Hooks are scoped: touching `.py` runs Python tooling, touching `.ts/.tsx` runs JS tooling. — *Why:* Scoped hooks keep commit times short by only running checks relevant to the changed files.
  - The same versions of every linter run in CI. — *Why:* Drift between local and CI lints means "passes locally, fails in CI" loops; pinning versions removes that friction class.
  - mypy runs in strict mode on `foresight.core` and `foresight.api`. — *Why:* Strict mode catches the high-value bugs (Any-leakage, missing None checks) early when the codebase is small enough to stay clean.
- **Depends on:** E1.S1

**E1.S5 — CI skeleton (GitHub Actions)**
- **User story:** As a developer, I want PRs to run lint + types + tests for both Python and Node, so quality gates aren't manual.
- **Acceptance criteria:**
  - Workflow runs on PR open + push to main; matrix covers Python (lint/type/test) and Node (lint/type/build). — *Why:* Running on PR blocks merging broken code; running on main verifies branch protection actually held.
  - Empty PR triggers a green workflow in <5 minutes. — *Why:* Fast feedback keeps the dev loop tight; >5 min CI starts inviting "let me skip CI just this once."
  - Caching enabled for pip/npm with cache key = lockfile hash. — *Why:* Cold installs dominate CI runtime; correct cache keys deliver the speedup without serving stale deps.
  - Required status checks configured on `main` so failed CI blocks merge. — *Why:* A green CI badge is only meaningful if it gates merging; otherwise it's decoration.
  - Test artifacts (junit/sarif) uploaded on failure. — *Why:* Artifacts make root-causing CI failures possible without re-running locally; SARIF surfaces in the PR UI for fast triage.
- **Depends on:** E1.S2, E1.S4

**E1.S6 — Decision-rationale capture (ADR system deferred)**
- **User story:** As a developer, I want every load-bearing architectural decision made during E1 to be discoverable later, so future contributors don't have to reverse-engineer rationale from git history.
- **Decision (revised in review):** The originally-planned ADR system was reviewed and **deferred indefinitely**. By the time E1.S6 came up, decision rationale was already captured in 5+ places:
  - `PLAN.md` Architectural Decisions table — Python tooling, DB, infra targets, etc.
  - `PLAN.md` "Why:" lines on every acceptance criterion in every story.
  - `CONTRIBUTING.md` — workflow, prerequisites, layering rules, CI overview.
  - `foresight/__init__.py` — layering rules captured as the module docstring.
  - Commit messages (markdown body with Summary / Changes / Why per `CLAUDE.md`).
  - PR descriptions (every PR template forces a "Why" justification).
  Adding a 7th surface (per-decision ADR files) would mostly duplicate existing content while creating drift risk. ADRs earn their keep on multi-team / long-lived / open-source projects; for a solo MVP they're ceremony cost without proportional benefit.
- **Re-introduction trigger:** Re-evaluate when **any** of these become true: (a) second contributor joins, (b) the project hits a 12-month mark, (c) PLAN.md grows past ~3000 lines making decision discovery painful.
- **Acceptance criteria (revised):**
  - PLAN.md Architectural Decisions table is current and reflects every decision made in E1.
  - CONTRIBUTING.md captures the git workflow, layering rules, prerequisites, and CI overview.
  - `foresight/__init__.py` docstring documents the layering rules.
  - This deferral itself is recorded — readable from `PLAN.md` (here) and from the merge commit.
- **Depends on:** E1.S2

---

### E2 — Data Model & Storage

**E2.S0 — Minimal Postgres in compose (early sliver of E8.S1)**
- **User story:** As a developer working on E2 stories, I want a Postgres instance reachable via `make up` so that entity-model tests and migrations have a real DB to run against without waiting for the full Compose stack in E8.
- **Acceptance criteria:**
  - `infra/compose/docker-compose.yml` exists with a single `db` service (Postgres 16, alpine variant) on host port `5432`. — *Why:* A real Postgres in dev catches the bugs SQLite hides (JSONB, RLS, native indexes). Alpine keeps the image small.
  - Healthcheck via `pg_isready -U postgres` with sensible interval/timeout. — *Why:* Lets `make up` block until the DB is actually serving connections, so subsequent migrate/seed/test commands don't race against an unready DB.
  - Persistent named volume (`foresight_db_data`) so DB state survives `compose down`. — *Why:* Devs hate re-seeding every restart; explicit `compose down -v` is the documented reset.
  - `make up` promoted from stub to a working target invoking compose; `make down` promoted similarly. The stub message for compose targets is removed. — *Why:* `make up` always means "bring up the local stack as currently defined"; today that's just the DB, but E8.S1 extends without renaming.
  - `make db-shell` target added — opens a `psql` prompt against the running DB. — *Why:* Every Postgres-using project needs a quick shell escape hatch; defining it once removes a class of "how do I connect locally?" questions.
  - `.env.example` checked in with `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Real `.env` gitignored (already in `.gitignore` from E1). — *Why:* Documents the contract; missing env vars produce a clear failure mode rather than mystery connection errors.
  - `CONTRIBUTING.md` "Prerequisites" updated to require Docker. — *Why:* Foresight is now a "Docker required" project; the README should match reality.
- **Depends on:** E1.S3 (Makefile targets to promote)

**E2.S1 — Define core entity models**
- **User story:** As a developer, I want SQLAlchemy 2.x models for the core entities, so all downstream layers have a typed, queryable schema.
- **Acceptance criteria:**
  - All listed models defined with PEP 484 type-annotated columns; mypy strict-mode clean. — *Why:* Typed models give the API, worker, and tests a single source of truth that the IDE understands; without them every consumer redeclares types.
  - Every row carries a non-null `tenant_id` foreign key with an index. — *Why:* Forgetting `tenant_id` on even one table is the bug that leaks customer data; enforcing at schema time makes that mistake structurally impossible.
  - `Variant.sku` unique within a `Brand`; `Order.shopify_gid` unique globally. — *Why:* Natural keys catch ingestion bugs immediately (duplicate insert fails loudly) instead of silently corrupting analytics.
  - `Forecast` and `ForecastPoint` schemas record `model_name`, `model_version`, and `inputs_as_of`. — *Why:* Auditing why a recommendation was made requires knowing which model ran on which inputs at which time; bolting this on later means rewriting tables.
  - Relationship navigation works in unit tests against an ephemeral Postgres. — *Why:* Relationships are the most common source of N+1 bugs; testing them early surfaces lazy-load surprises before they hit production.
- **Depends on:** E1.S2

**E2.S2 — Raw event landing (S3 + RawEvent table)**
- **User story:** As a developer, I want immutable raw landing for Shopify events (blob in S3, index row in Postgres), so transformations downstream are reproducible.
- **Acceptance criteria:**
  - Writing a `RawEvent` produces a blob at `s3://bucket/raw/{tenant}/{source}/{date}/{gid}.json` and an index row pointing to it. — *Why:* Splitting blob (large, immutable) from index (small, queryable) lets us scan millions of events cheaply while keeping the truth in S3.
  - Blobs are write-once; the writer never updates an existing key. — *Why:* Immutability means a backfill bug can be re-run without corrupting prior state, and audits remain trustworthy.
  - `replay(tenant, since)` reproduces canonical entities deterministically from raw blobs. — *Why:* If we can't reproduce modeled state from raw, we can't fix transformation bugs without losing fidelity; this story exists precisely to enable safe reprocessing.
  - Oversized payloads (>1MB) handled without truncation; a content-hash is stored on the row. — *Why:* Shopify webhook payloads can be large; truncation = silent data loss. Hashes let us detect corruption and dedupe at ingestion.
- **Depends on:** E2.S1, E2.S3

**E2.S3 — Storage abstractions (BlobStore + DB session)**
- **User story:** As a developer, I want a `BlobStore` protocol with S3 + LocalFs impls, plus a Postgres session factory parameterized by `DATABASE_URL`, so the same code runs locally and in AWS.
- **Acceptance criteria:**
  - `BlobStore` protocol exposes `put`, `get`, `presigned_url`, `exists`, `delete`; both impls satisfy it. — *Why:* A small, complete interface keeps callers free of provider conditionals; the same business code runs in compose and Fargate.
  - Switching impls is a single env var (`BLOB_STORE=local|s3`). — *Why:* Single-knob config means deploy envs differ in configuration, not code, removing a class of "works on my laptop" surprises.
  - Postgres session factory respects `DATABASE_URL`, `DB_POOL_SIZE`, and `DB_STATEMENT_TIMEOUT`. — *Why:* Environments differ on pool sizing and timeout policy (RDS proxy vs. local socket); making them tunable avoids per-env code forks.
  - Tests parametrize across both BlobStore impls. — *Why:* Bugs that only show up in S3 (presign edge cases, object-not-found races) need to be reproducible locally; running tests against both surfaces them on PR.
- **Depends on:** E1.S2

**E2.S4 — Alembic baseline migration**
- **User story:** As a developer, I want `alembic upgrade head` to create the full schema from a clean Postgres, so envs are repeatable.
- **Acceptance criteria:**
  - Fresh DB → migrate → schema matches models exactly (verified by `alembic check`). — *Why:* Schema drift between models and migrations is the single biggest source of "passes in dev, fails in prod" deploys.
  - Downgrade path returns DB to empty. — *Why:* Untestable rollbacks become un-runnable rollbacks under pressure; the only way to know they work is to run them.
  - `alembic check` runs in CI on every PR. — *Why:* Models change in PRs more often than migrations; catching missing migrations at PR time prevents merge-then-break-deploy.
  - Migration files use deterministic IDs (timestamp + slug). — *Why:* Random IDs make merging concurrent migrations chaotic; deterministic ordering lets reviewers see the sequence at a glance.
- **Depends on:** E2.S1

**E2.S5 — Seed script**
- **User story:** As a developer, I want `make seed` to populate one tenant, ~50 SKUs, ~90 days of orders + inventory snapshots.
- **Acceptance criteria:**
  - Produces 1 tenant, 1 brand, ~50 variants, ~90 days of orders + daily inventory snapshots. — *Why:* The whole point of seed is to unblock parallel work; covering the full data model means every downstream story can develop without Shopify access.
  - Deterministic given `SEED=42 make seed`. — *Why:* Determinism lets bugs be reproduced exactly; without it, "couldn't repro" becomes the dominant test outcome.
  - Order velocities vary across SKUs (some hot, some dead). — *Why:* A flat distribution makes the forecast trivially correct; realistic variation exposes the cases the model actually has to handle.
  - Runtime under 10 seconds on a developer laptop. — *Why:* Slow seed = developers run it less = stale local data; sub-10s keeps `make seed` part of the everyday loop.
- **Depends on:** E2.S4

---

### E3 — API Foundation (FastAPI)

**E3.S1 — Bootstrap FastAPI app**
- **User story:** As a developer, I want `foresight/api/` exposing `/health`, `/version`, `/docs`, with a versioned `/api/v1` router.
- **Acceptance criteria:**
  - `GET /health` returns `{status: "ok", db: "ok"}` after a DB ping; `GET /version` returns commit SHA + build time. — *Why:* Health that doesn't check dependencies is decoration; including DB and exposing build info turns 3am incident response from a guessing game into a lookup.
  - OpenAPI docs render at `/docs` (Swagger) and `/redoc`. — *Why:* Auto-generated docs are the API's contract; if they don't render, the contract isn't real.
  - All business routes live under `/api/v1`. — *Why:* Versioning the path lets us ship breaking changes alongside the old API without a flag day.
  - `pytest tests/api` runs in <5s on the empty stack. — *Why:* Fast tests stay run-frequently; slow tests get skipped under deadline pressure.
- **Depends on:** E1.S2, E2.S1

**E3.S2 — Auth (JWT + service key)**
- **User story:** As a developer, I want JWT bearer auth for the web app and a service key for Slack/worker callbacks.
- **Acceptance criteria:**
  - JWT verified by signature + expiry + issuer; service key compared in constant time. — *Why:* Permissive auth = data leak; constant-time comparison prevents the timing-attack class on the service key.
  - Protected endpoint returns 401 without auth, 403 for valid-but-unauthorized JWT, 200 for valid auth. — *Why:* Distinguishing 401 from 403 lets clients react correctly (login vs. ask-for-permission); collapsing them confuses both clients and humans.
  - JWT carries `tenant_id` claim and the API rejects mismatches between claim and queried resource. — *Why:* Without per-tenant claim enforcement, any valid token can read any tenant's data; this is the single most important auth invariant for multi-tenant SaaS.
  - Key rotation tested by issuing two valid signing keys in parallel. — *Why:* Rotation that's never tested fails the day you actually need to rotate; testing it now means rotation is a non-event later.
- **Depends on:** E3.S1

**E3.S3 — Schemas, error model, pagination convention**
- **User story:** As a developer, I want Pydantic schemas separated from ORM models, a structured error envelope, and one pagination convention.
- **Acceptance criteria:**
  - Pydantic schemas live in `foresight/api/schemas/`; ORM models in `foresight/core/models/`. — *Why:* Mixing concerns means a private DB column accidentally lands in an API response; physical separation makes leaks unlikely.
  - Error envelope is `{code: str, message: str, details: dict | null}` with a stable `code` taxonomy. — *Why:* Stable codes mean clients can branch on error class without parsing English; English-only errors lock UX changes to backend deploys.
  - Pagination is cursor-based (`?cursor=...&limit=...`) with a documented max page size. — *Why:* Cursor pagination is stable under writes (offset pagination skips/duplicates rows on insert); choosing once now avoids per-endpoint divergence.
  - Convention captured in `docs/api/conventions.md` (or an ADR). — *Why:* Conventions that aren't written get re-litigated every PR; one canonical doc is the cheapest enforcement mechanism.
- **Depends on:** E3.S1

**E3.S4 — Read endpoints over seed data**
- **User story:** As an ops user, I want `GET /tenants/me`, `/products`, `/products/{id}`, `/inventory/snapshots`, so I can browse my data via the API once seeded.
- **Acceptance criteria:**
  - Every endpoint enforces tenant scoping from the JWT claim; cross-tenant lookups return 404 (not 403). — *Why:* 404 vs 403 prevents tenant-existence enumeration; 403 leaks "this tenant exists, you just can't see it."
  - Responses match published Pydantic schemas; contract tests fail on shape drift. — *Why:* Contract tests are the cheap version of consumer-driven contracts; they catch breaking changes before clients hit them.
  - `/inventory/snapshots` supports filtering by SKU and date range with sane defaults. — *Why:* Without defaults, naive callers fetch the full table; with defaults, the cost of a mistake is bounded.
  - p50 latency <100ms on seed data. — *Why:* Dev-loop slowness compounds; setting a budget early catches accidental N+1s when the codebase is small enough to fix easily.
- **Depends on:** E2.S5, E3.S2, E3.S3

**E3.S5 — Job & forecast endpoints (stubs)**
- **User story:** As an ops user, I want `POST /ingestion/shopify/connect`, `GET /ingestion/jobs`, `POST /forecasts/run`, `GET /forecasts/{id}/points`.
- **Acceptance criteria:**
  - Endpoints return shape-correct stub responses (real types, fake data). — *Why:* Stubbing the contract first lets the web app and Slack adapter build against a stable surface while workers/models land in parallel.
  - Each endpoint has a contract test passing for the stub and the eventual real impl. — *Why:* Contract tests are the boundary that lets two streams progress without blocking each other.
  - Stubs return a `Deprecation` header pointing to the issue/story that will replace them. — *Why:* Without a marker, stubs become permanent; an explicit pointer is the only thing that prevents "that's how it's always worked."
  - `POST /forecasts/run` is idempotent given an `idempotency_key` body field. — *Why:* Forecast runs are expensive; clients retrying without idempotency double the bill and produce duplicate `Forecast` rows.
- **Depends on:** E3.S4

**E3.S6 — Agent chat endpoint (stub)**
- **User story:** As an ops user, I want `POST /agents/chat` accepting a prompt + conversation context and returning an `AgentResult`, so web and Slack share one path.
- **Acceptance criteria:**
  - Request body: `{conversation_id?, message, context?}`; response includes `message`, `tool_calls`, `conversation_id`, `usage`. — *Why:* Tracking `tool_calls` and `usage` in the response lets the UI show what the agent did and lets ops monitor cost without separate plumbing.
  - Stub returns canned response with `is_stub: true`. — *Why:* Marking stubs makes it impossible for clients to mistake them for real responses in logs or screenshots.
  - Endpoint streams via SSE when `Accept: text/event-stream`, otherwise returns full JSON. — *Why:* Streaming makes the chat UI feel responsive; supporting both modes from the start avoids a forced rewrite when E6 lands.
  - Contract tests cover both streaming and non-streaming. — *Why:* Streaming bugs (mid-message disconnect, header handling) only surface under test; covering both modes pre-impl prevents regressions later.
- **Depends on:** E3.S2, E3.S3

---

### E4 — Shopify Ingestion + Worker

**E4.S1 — Worker scaffold + scheduler**
- **User story:** As a developer, I want `foresight/worker/` with APScheduler (or arq) wired into Compose.
- **Acceptance criteria:**
  - Worker boots in compose with a healthcheck endpoint; a no-op scheduled job logs every 30s. — *Why:* Visible heartbeat catches "worker silently died" — the most common worker bug — at a glance.
  - Job framework supports both scheduled and on-demand jobs through one API. — *Why:* One API means the API service can enqueue jobs the same way the scheduler does; two APIs forks the codebase and doubles the bug surface.
  - Worker exits non-zero on unrecoverable errors; compose restart policy = `unless-stopped`. — *Why:* Crash-and-restart is the cheap supervisor; exiting clean (not hanging) is what makes that strategy work.
  - Job failures emit structured logs with `job_id`, `tenant_id`, `attempt`, `error`. — *Why:* Structured logs are queryable; freeform error spew isn't, and the worker is exactly where you'll need to query at 2am.
- **Depends on:** E1.S2

**E4.S2 — Shopify OAuth install flow**
- **User story:** As an ops user, I want to connect my Shopify store via OAuth and have offline access tokens stored per `Brand`.
- **Acceptance criteria:**
  - HMAC + nonce verified on callback. — *Why:* Skipping HMAC means anyone can spoof a callback for any shop; this is a Shopify-documented attack class, not theoretical.
  - Offline access tokens stored encrypted at rest using a tenant-scoped KMS key (or local equivalent). — *Why:* Plaintext tokens in the DB = total compromise on any DB read; encrypting at rest blunts the impact of partial breaches.
  - Reinstalling the same shop replaces the token without creating a duplicate `Brand`. — *Why:* Duplicate Brands silently double inventory/orders downstream; the upsert is a one-liner, the cleanup is a migration.
  - Tests use a mock Shopify server (`pytest-httpserver` / `respx`); no live Shopify required. — *Why:* Live-API tests are flaky and require credentials; mocks let CI run anywhere.
  - Failed installs leave no partial Brand row. — *Why:* Partial state is the worst kind of state; transactional install means retry is safe.
- **Depends on:** E3.S5, E2.S1

**E4.S3 — Initial backfill (products, inventory, 12mo orders)**
- **User story:** As an ops user, I want my last 12 months of orders, current inventory, and product catalog backfilled after install.
- **Acceptance criteria:**
  - Backfill respects Shopify rate limits (Retry-After header); no repeated 429s in logs. — *Why:* Hammering the API gets the app banned; respecting rate limits is the difference between a clean backfill and a ticket from Shopify.
  - Re-runs are idempotent and resume from the last cursor. — *Why:* Backfills will fail mid-run; without resumability the only option is start-over, and a 12-month order history is hours of API calls.
  - `IngestionJob` records `started_at`, `ended_at`, rows-per-table, errors, `last_cursor`. — *Why:* These fields turn "is the backfill done?" from a guess into a query; without them ops can't answer customer questions.
  - Row counts after backfill match a sampled Shopify admin export within 1%. — *Why:* Drift > 1% means the model is missing data and any downstream forecast is wrong; this is the integration's ground truth.
  - Raw payloads land in S3 (E2.S2) before transformation. — *Why:* Raw-first means a transformation bug is fixable by replay; transformation-first means it's permanent.
- **Depends on:** E4.S1, E4.S2, E2.S2

**E4.S4 — Webhook handlers (orders, inventory)**
- **User story:** As an ops user, I want `orders/create`, `orders/updated`, and `inventory_levels/update` ingested in near-real-time.
- **Acceptance criteria:**
  - Each webhook verifies `X-Shopify-Hmac-Sha256` against the store's shared secret. — *Why:* Unverified webhooks are unauthenticated POSTs from the internet; trusting them = trivial data injection.
  - Handlers idempotent on Shopify GID + `updated_at`. — *Why:* Shopify retries webhooks on any non-2xx; idempotency is the only safe strategy.
  - Handlers ack within 1s by enqueueing async processing; heavy work runs on the worker. — *Why:* Shopify times out webhook responses at 5s; doing heavy work synchronously courts retry storms.
  - End-to-end lag (event → DB row) <60s in compose. — *Why:* A forecast on yesterday's data is a stale forecast; lag budgets keep "real-time" honest.
  - Failed processing produces a retryable `IngestionJob` entry. — *Why:* Drops are silent; retryable jobs make recovery a one-button operation.
- **Depends on:** E4.S3

**E4.S5 — Job retry + ops endpoints**
- **User story:** As an ops user, I want to retry failed jobs and inspect job history.
- **Acceptance criteria:**
  - `POST /ingestion/jobs/{id}/retry` resumes from `last_cursor` rather than restarting. — *Why:* Restart-from-zero on a 12-month backfill is hours; resume is minutes. The difference defines whether ops can self-serve.
  - `GET /ingestion/jobs` paginated, filterable by status and brand. — *Why:* Without filters, ops scrolls; with them, ops finds the failed job in 2 clicks.
  - Retry rate-limited per job (e.g., 1/min). — *Why:* Without a limit, a panicked operator clicking retry repeatedly creates the storm they're trying to fix.
  - Job detail includes a sanitized error trace and an offending-payload reference. — *Why:* Errors without payloads are unfixable; including a (safe) reference makes incidents reproducible without DB access.
- **Depends on:** E4.S4, E3.S5

---

### E5 — Forecasting Pipeline

**E5.S1 — Velocity computation utility**
- **User story:** As a developer, I want a pure function computing trailing-N-day units sold per SKU.
- **Acceptance criteria:**
  - Signature: `velocity(orders, sku, window_days, as_of) -> float` — pure, no side effects. — *Why:* Pure functions are testable, cacheable, and parallelizable; impure ones are none of those.
  - Edge cases handled: zero orders → 0.0; one-order-in-window → linear extrapolation noted in metadata. — *Why:* Zero/sparse SKUs are 30%+ of any catalog; treating them as errors crashes the forecast for the long tail.
  - Unit tests cover zero-velocity, steady, growing, declining, and holiday-spike shapes. — *Why:* These five shapes are the velocity surface area; missing any one means a class of customer is invisibly mis-forecast.
  - Performance: 10k SKUs × 90-day window in <2s on a single core. — *Why:* The forecast runs nightly per tenant; slow velocity means slow forecast means stale answers.
  - Lives in `foresight/core/forecasting/` — importable by API and worker. — *Why:* Co-locating with models means tests and prod use exactly the same code path.
- **Depends on:** E2.S5

**E5.S2 — Days-of-cover forecast**
- **User story:** As an ops user, I want a forecast computing days until each SKU stocks out at current velocity.
- **Acceptance criteria:**
  - `POST /forecasts/run` produces a `Forecast` + one `ForecastPoint` per active SKU with `days_of_cover`, `current_inventory`, `velocity`, `confidence_band`. — *Why:* Confidence bands are the difference between "you'll stock out in 7 days" and "in 5–12 days"; the latter is honest, the former is overconfident.
  - SKUs with zero velocity report `days_of_cover: null` + a `reason`. — *Why:* `null` is honest about unknowns; reporting infinity or a giant number makes the forecast look broken to humans.
  - `Forecast` row stores `model_name`, `model_version`, `inputs_as_of`. — *Why:* Without these, A/B comparing model changes is impossible; with them it's a join.
  - Endpoint returns 202 + `forecast_id` immediately, processes async on the worker. — *Why:* Forecasts on real catalogs take seconds-to-minutes; sync responses block the UI; async + polling is the standard pattern.
  - Run completes for the seed dataset in <10s end-to-end. — *Why:* Fast feedback during dev keeps the loop tight; slow forecasts get run less often = less debugged.
- **Depends on:** E5.S1, E2.S1

**E5.S3 — S3 artifact + reproducibility**
- **User story:** As a developer, I want each forecast run to persist a CSV/Parquet artifact (input snapshot + output) to S3.
- **Acceptance criteria:**
  - Artifact contains: input velocity, input inventory snapshot, output points, model version, run config. — *Why:* These are the exact ingredients for replay; any missing piece breaks reproducibility.
  - Artifact key: `s3://bucket/forecasts/{tenant}/{forecast_id}.parquet`. — *Why:* Parquet is columnar, compresses well, and queryable from DuckDB/Athena without conversion.
  - `Forecast` row stores artifact key + content hash. — *Why:* Storing the hash detects tampering or accidental overwrite; storing the key is what makes replay possible.
  - `replay(forecast_id)` reproduces the same `ForecastPoint` rows bit-for-bit. — *Why:* If replay isn't a tested function, replay doesn't actually work; it just looks like it might.
  - Presigned-URL endpoint exists for downloading artifacts (auth + tenant-scoped). — *Why:* Customers will ask "what data did this forecast use?"; presigned URLs answer that without granting bucket access.
- **Depends on:** E5.S2, E2.S3

**E5.S4 — Backtest harness**
- **User story:** As a developer, I want to replay historical inventory + orders against the model and report MAE.
- **Acceptance criteria:**
  - `make backtest` against seed data holds out the last 14 days and prints MAE in days. — *Why:* Holdout-based eval is the only honest measure; in-sample is meaningless.
  - Backtest split is deterministic given a seed and stored alongside the result. — *Why:* Reproducible splits = reproducible results; non-deterministic splits invite p-hacking by accident.
  - Report breaks MAE down by SKU velocity tier (hot/medium/long-tail). — *Why:* Aggregate MAE hides the long-tail being terrible; tiered reporting prevents shipping an "average is fine" model with a broken segment.
  - CI runs a small backtest and fails if MAE regresses by >20% vs. main. — *Why:* Quality regression as a build break = quality is non-negotiable; without it, model quality silently drifts down.
  - Report saved as a Markdown artifact in CI for review. — *Why:* Numbers in CI logs get skimmed; a Markdown artifact in the PR gets read.
- **Depends on:** E5.S2, E2.S5

---

### E6 — Agent Layer + Slack

**E6.S1 — AgentClient protocol + Tool registry**
- **User story:** As a developer, I want a thin `AgentClient` protocol and a `Tool` registry, so we can swap concrete LLM/agent stacks later.
- **Acceptance criteria:**
  - `AgentClient` protocol exposes `run(prompt, tools, context) -> AgentResult` only — no framework-specific types leak. — *Why:* A protocol that leaks types defeats the point; if `AgentResult` references LangChain classes, you can't swap LangChain.
  - `Tool` is data: `name`, `description`, `input_schema` (JSON Schema), `handler`. — *Why:* Tools as data (not subclasses) means they're declarable in YAML, testable in isolation, and addable without inheritance ceremonies.
  - Registry validates uniqueness and that schemas validate. — *Why:* Duplicate names = silent shadowing; invalid schemas = runtime errors that look like model failures.
  - Four tools registered: `get_inventory`, `get_velocity`, `run_forecast`, `search_orders` with JSON schemas. — *Why:* These four cover the three demo journeys; more tools come after journeys are demoable.
  - Mock implementation passes the unit tests; no Anthropic/OpenAI calls required. — *Why:* Tests that hit the network are flaky and slow; mocking the agent layer is what makes the rest testable.
- **Depends on:** E1.S2

**E6.S2 — First concrete agent impl (Anthropic SDK)**
- **User story:** As an ops user, I want to ask the agent a question and get an answer that uses tools when needed.
- **Acceptance criteria:**
  - Uses Claude Sonnet 4.6 (or latest available) via the Anthropic SDK with prompt caching enabled. — *Why:* Sonnet hits the right cost/latency point for chat; prompt caching cuts repeated-context costs by ~10x.
  - System prompt + tool descriptions cached as a single block. — *Why:* Caching the largest stable prefix maximizes hit rate; per-message caching is a footgun (low hit rate, complex invariants).
  - Tool calls dispatch through E6.S1 registry; tool errors return as `tool_result` with `is_error: true` (not exceptions). — *Why:* Surfacing errors as tool results lets the model recover/clarify; throwing exceptions terminates the turn unhelpfully.
  - Eval harness with ≥10 fixed prompts passes ≥90%; assertions check expected tool calls, not exact wording. — *Why:* Wording-strict evals fail on harmless paraphrases; tool-call-strict evals catch real regressions.
  - Per-call usage (input/output/cache tokens) logged in a structured field. — *Why:* Token usage is the bill; structured logs let it be charted before the surprise invoice.
- **Depends on:** E6.S1, E5.S2, E3.S4

**E6.S3 — Conversation persistence**
- **User story:** As an ops user, I want my Slack/web thread context to persist.
- **Acceptance criteria:**
  - `AgentConversation` rows scope to `(tenant_id, thread_id, surface)` with `surface ∈ {slack, web}`. — *Why:* Threading by surface prevents Slack and web threads from accidentally bleeding into each other for the same user.
  - Messages stored with role, content, `tool_calls`, `tool_results`, `created_at`. — *Why:* Round-trip fidelity is required to resume a conversation; collapsing structure now means rebuilding it later.
  - Resuming by `conversation_id` re-injects prior turns respecting cache boundaries. — *Why:* Naïve re-injection blows the cache every turn; respecting boundaries keeps cost predictable.
  - Conversation expiry policy documented (e.g., archive after 30 days idle). — *Why:* Without a policy the table grows forever; deciding now lets indexes be sized correctly.
  - Tenant deletion cascades to conversations. — *Why:* GDPR/customer churn require deletability; orphaned conversations are an audit finding waiting to happen.
- **Depends on:** E6.S2, E2.S1

**E6.S4 — Slack adapter**
- **User story:** As an ops user, I want `@foresight` in Slack to route to the agent and reply in-thread.
- **Acceptance criteria:**
  - Slack signature (`X-Slack-Signature` + timestamp window) verified on every inbound. — *Why:* Skipping signature verification = anyone can post to your endpoint as Slack; this is a documented Slack abuse class.
  - Slash command + app_mention both supported and route to the same backend. — *Why:* Two surfaces, one backend: divergence between them is drift between channels and DMs.
  - Replies post in-thread, never to channel root, unless explicitly requested. — *Why:* Channel-root replies spam the channel and erode trust; in-thread keeps conversations contained.
  - Long agent runs post a "thinking…" placeholder within 3s and update on completion. — *Why:* Slack times out the initial response at 3s; placeholder + edit is the standard pattern and keeps the UX honest about latency.
  - Errors post a user-friendly message + an internal log with the conversation_id. — *Why:* End-users seeing a stack trace = trust loss; internal log entry = on-call can still debug.
- **Depends on:** E6.S3, E3.S6

**E6.S5 — Eval harness in CI**
- **User story:** As a developer, I want a small fixed eval set running on every PR.
- **Acceptance criteria:**
  - Eval set committed in `evals/` as YAML: prompt + expected tool calls + expected answer regex. — *Why:* Storing as data (not code) lets non-engineers add cases; YAML diffs cleanly in PRs.
  - `make eval` runs the set, reports per-case pass/fail, prints aggregate. — *Why:* Aggregate-only reporting hides which case regressed; per-case is the actionable view.
  - CI fails when aggregate score drops below `MAIN - 5%`. — *Why:* Hard floors miss slow drift; tracking against main catches it without flagging noise.
  - Eval results uploaded as CI artifact and linked from the PR. — *Why:* In-line links remove the friction of "check the run logs"; reviewers actually look at what's one click away.
  - Adding a prompt requires updating `evals/CHANGELOG.md`. — *Why:* Changing the eval set silently moves the goalposts; explicit changelog keeps quality measurable.
- **Depends on:** E6.S2

---

### E7 — Web App (Next.js)

**E7.S1 — Next.js scaffold + auth**
- **User story:** As a developer, I want `web/` scaffolded with App Router, NextAuth, an API client, and shadcn/ui.
- **Acceptance criteria:**
  - Next.js App Router + TypeScript strict mode; ESLint + Prettier in pre-commit. — *Why:* Strict mode catches the `any` leaks that turn into runtime bugs; pre-commit means style debates happen once, not every PR.
  - NextAuth handles login (magic link or OAuth) and session lifecycle. — *Why:* Rolling auth in-house is a security-team time sink; NextAuth is battle-tested and integrates with the JWT layer cleanly.
  - API client in `web/lib/api.ts` includes the JWT and retries 401 once after refresh. — *Why:* A single client = one place to change auth/headers/timeouts; per-call fetches diverge.
  - shadcn/ui set up with documented theme tokens; components in `web/components/ui/`. — *Why:* shadcn vendors source = no version-lock surprises and easy theming. Locating in one place keeps the design system findable.
  - Dev mode hot-reload works through compose; `/login` redirects when logged out and home when logged in. — *Why:* Broken hot-reload kills the dev loop; verifying redirect behavior catches the most common auth wiring mistake.
- **Depends on:** E3.S2

**E7.S2 — Setup / Connect Shopify screen**
- **User story:** As an ops user, I want to connect my store and see backfill progress.
- **Acceptance criteria:**
  - Connect button initiates OAuth via the API; flow returns to a status page polling `IngestionJob`. — *Why:* Self-serve onboarding is the difference between "talk to sales" and "try it in 5 minutes"; the status page is the difference between hope and clarity.
  - Status page shows current step, rows ingested, ETA, last error. — *Why:* Granular progress beats a spinner; users wait if they can see progress.
  - Failed step offers a Retry button calling `POST /ingestion/jobs/{id}/retry`. — *Why:* One-click retry from the failure point closes the loop on most transient issues without involving support.
  - Reconnecting an already-connected store warns instead of duplicating. — *Why:* Most "weird state" bugs come from accidental reconnects; an explicit warning prevents the support ticket.
  - Loading and error states render correctly when the API is down. — *Why:* UIs that handle the happy path only fail loudly the day infra hiccups; defining the unhappy path now is much cheaper.
- **Depends on:** E7.S1, E4.S2

**E7.S3 — Inventory & Forecast screen**
- **User story:** As an ops user, I want a sortable SKU table with current stock, days-of-cover, and a tiny velocity sparkline.
- **Acceptance criteria:**
  - Columns: SKU, name, `current_inventory`, `days_of_cover`, `velocity_30d`, sparkline. — *Why:* These are the columns ops actually scan when triaging reorders; adding more dilutes the signal.
  - Default sort: ascending by `days_of_cover`. — *Why:* The default view should answer "what's most urgent"; making the user re-sort every load is friction.
  - Filters: brand, days_of_cover range, velocity > 0. — *Why:* Filtering out long-tail dead SKUs is the single biggest UX request from ops users; including it day one earns trust.
  - Empty state shows a "complete onboarding" CTA. — *Why:* Empty-state without guidance is a dead end; a CTA turns it into a path forward.
  - Loads <500ms p50 against seed data; pagination kicks in >100 SKUs. — *Why:* Large catalogs are normal in DTC (10k+ SKUs); paginating from the start prevents browser death on real data.
- **Depends on:** E7.S1, E3.S4, E5.S2

**E7.S4 — Agent chat screen**
- **User story:** As an ops user, I want a chat pane that talks to the same agent backend Slack uses.
- **Acceptance criteria:**
  - Chat UI streams responses via SSE; partial messages render character-by-character. — *Why:* Streaming is what makes a chat feel like talking to someone, not waiting on a slow API.
  - Conversation persists across reloads via `conversation_id` in URL or local storage. — *Why:* Losing context on refresh is a documented frustration; persistence is the floor, not a nice-to-have.
  - Tool calls render as collapsible "Used tool: search_orders" cards inline. — *Why:* Surfacing tool calls is what makes the agent trustworthy; a black-box answer is harder to act on.
  - Errors surface in the UI with a Retry. — *Why:* Hidden errors look like "the agent gave up"; visible errors with retry restore agency.
  - Send disabled while a stream is in flight; ⏎ submits, ⇧⏎ newlines. — *Why:* These keymaps are the ChatGPT-set norm; deviating earns no points and confuses users.
- **Depends on:** E7.S1, E6.S2

---

### E8 — Local Infrastructure

**E8.S1 — Compose stack**
- **User story:** As a developer, I want `make up` to bring up api + worker + web + db + localstack with healthchecks.
- **Acceptance criteria:**
  - `docker-compose up` brings every service to healthy in <60s on a clean machine. — *Why:* Onboarding cost ≈ time-to-first-green-run; >60s pushes new contributors into "is this even working?" mode.
  - Healthchecks: api → /health, worker → heartbeat, db → `pg_isready`, localstack → `_localstack/health`. — *Why:* Healthchecks are how compose orders startup; without them api boots before db is ready and you get phantom failures.
  - Volumes persist DB across `compose down`; `compose down -v` is the documented reset. — *Why:* Resetting on every restart makes seed-then-iterate flows painful; making the reset explicit prevents accidental data loss.
  - Services bind to localhost only by default. — *Why:* Exposing dev services on 0.0.0.0 has accidentally leaked customer data to office Wi-Fi at multiple companies; localhost default prevents the worst-case mistake.
  - `make up` is idempotent. — *Why:* Idempotent dev commands let muscle memory be safe; non-idempotent ones get aliased to "down then up" which slows everyone down.
- **Depends on:** E1.S3, E2.S4, E3.S1

**E8.S2 — Per-service Dockerfiles**
- **User story:** As a developer, I want multi-stage Dockerfiles for api, worker, web with non-root users.
- **Acceptance criteria:**
  - Builder + slim runtime stages; final images < 250MB compressed. — *Why:* Small images = fast pulls in CI, fast Fargate cold-starts, smaller attack surface.
  - All processes run as `appuser` (non-root). — *Why:* Root containers compromise to host root in many escape paths; non-root closes that class of issue.
  - Healthcheck baked into the image. — *Why:* In-image healthchecks work in any orchestrator (compose, ECS, k8s) without external glue.
  - Build args for `APP_VERSION` (commit SHA) populate `/version`. — *Why:* When prod is on fire, "what version is running?" needs a one-second answer; baking it into the image guarantees that.
  - `.dockerignore` excludes test fixtures, `.git`, `node_modules`. — *Why:* Bloated build contexts make every push slow; `.dockerignore` is free CI speedup.
- **Depends on:** E1.S2

**E8.S3 — Env templates + local secrets**
- **User story:** As a developer, I want `.env.example` checked in and a documented local secrets workflow.
- **Acceptance criteria:**
  - `.env.example` lists every required and optional env var with description and example. — *Why:* Undocumented env vars become "ask the original author" rituals; the example file IS the documentation.
  - App fails fast with a clear error when a required env var is missing (names the var). — *Why:* Cryptic boot failures dominate day-of-onboarding tickets; named errors make them self-service.
  - `.env*` gitignored and a pre-commit hook flags accidental commits. — *Why:* One leaked `.env` in git history is a credential rotation nightmare; the pre-commit hook is a cheap last line of defense.
  - Secrets workflow documented in README (where Shopify/Slack creds come from, how to rotate). — *Why:* Docs that exist before the first incident save the incident; written after, they're forensic, not preventive.
- **Depends on:** E1.S2

---

### E9 — AWS Infrastructure

**E9.S1 — Terraform module: network**
- **User story:** As a developer, I want a `modules/network` module provisioning VPC, subnets, NAT, security groups.
- **Acceptance criteria:**
  - VPC with public + private subnets across 2 AZs; NAT in each AZ for HA. — *Why:* Single-AZ NAT is the most common availability footgun in AWS; cross-AZ HA is the standard pattern.
  - Security groups for `alb`, `ecs_services`, `rds` exported as outputs; least-privilege rules. — *Why:* Permissive SGs are the AWS equivalent of leaving the door open; least-privilege at the module level makes the right thing the easy thing.
  - Reusable across `dev`/`prod` via input variables. — *Why:* Hand-rolled-per-env networking is how prod and dev drift; one module enforces parity.
  - `terraform plan` after `apply` is a clean no-op. — *Why:* Drift between TF state and reality is the source of "why did my next apply break things"; clean plan means state is honest.
  - Module README documents inputs, outputs, and a usage example. — *Why:* Undocumented modules don't get reused; reused undocumented modules become tribal knowledge.
- **Depends on:** E1.S6

**E9.S2 — Terraform module: data**
- **User story:** As a developer, I want `modules/data` provisioning RDS Postgres + S3 buckets + IAM roles.
- **Acceptance criteria:**
  - RDS Postgres 16; multi-AZ disabled in dev, enabled in prod. — *Why:* Multi-AZ in dev burns money for no benefit; in prod it's required for SLA.
  - S3 buckets created with versioning + SSE + block-public-access. — *Why:* Each of these defaults has a real-world breach behind it; defaulting to safe means we don't have to remember to flip every flag.
  - IAM roles split: ECS task execution role vs. task role. — *Why:* Splitting execution role (pull image, write logs) from task role (app permissions) is least-privilege done right.
  - DB credentials stored in Secrets Manager; no plaintext in TF state or output. — *Why:* TF state is sensitive; `sensitive = true` is the floor, Secrets Manager is the ceiling.
  - Backup retention configurable per env (1d dev, 7d+ prod). — *Why:* Backups in dev are noise; in prod they're survival.
- **Depends on:** E9.S1

**E9.S3 — Terraform module: services**
- **User story:** As a developer, I want `modules/services` provisioning ECS cluster + Fargate services + ALB + task defs for api, worker, web.
- **Acceptance criteria:**
  - Three Fargate services with autoscaling on CPU + request count. — *Why:* Static counts waste money or page on traffic spikes; autoscaling is the standard answer.
  - ALB target groups: `/api/*` → api, `/` → web; worker is internal-only. — *Why:* Routing at the ALB keeps services small (no in-app routing); internal-only on worker prevents accidental public exposure of jobs.
  - Task definitions reference SHA-tagged ECR images. — *Why:* Hardcoded `:latest` is the deploy footgun; SHA-tagged images make rollbacks a one-line change.
  - ALB health checks gate deployments — bad tasks don't take traffic. — *Why:* Without health-gated deploys, a bad deploy takes traffic; with them, the bad version never gets traffic.
  - Logs ship to CloudWatch with 30-day retention. — *Why:* 30 days hits the compliance/cost balance most teams want; explicit policy beats default-forever (cost) or default-7-days (too short).
- **Depends on:** E9.S2, E8.S2

**E9.S4 — Image build + push pipeline (ECR)**
- **User story:** As a developer, I want GitHub Actions building and pushing api, worker, web images to ECR on merge to main.
- **Acceptance criteria:**
  - Three images build in parallel, tagged with commit SHA + per-env `latest`. — *Why:* Parallel builds keep total deploy time reasonable; SHA tags enable rollbacks; env-scoped `latest` enables canary patterns.
  - OIDC used for AWS auth — no long-lived keys in GitHub. — *Why:* Long-lived keys in GitHub are a top breach vector; OIDC removes the key entirely.
  - Layer caching brings incremental builds <2 min. — *Why:* Cold builds train developers to skip CI; fast caches keep the loop honest.
  - Trivy/grype scan runs on the image; high-severity CVEs fail the build. — *Why:* Shipping known-CVE images is avoidable risk; the scan is a 30-second insurance policy.
  - Push failures alert via Slack or PR comment. — *Why:* Silent failures are slow to discover; loud failures get fixed in the same PR.
- **Depends on:** E1.S5, E8.S2

**E9.S5 — Secrets workflow (Secrets Manager)**
- **User story:** As a developer, I want `core.settings` to read from env locally and from Secrets Manager in cloud envs via `APP_ENV`.
- **Acceptance criteria:**
  - `core.settings` checks `APP_ENV`; `dev`/`prod` read Secrets Manager; `local` reads `.env`. — *Why:* One settings module = one place to reason about config; per-env settings spawn drift.
  - Secrets cached for the process lifetime with an explicit refresh API. — *Why:* Hitting Secrets Manager every request blows the rate limit; caching is required.
  - Rotation tested: rotating DB password, restarting the task, succeeds without code changes. — *Why:* Untested rotation is unrotated rotation; testing now means rotation is a non-event later.
  - Local dev cannot accidentally read prod Secrets Manager. — *Why:* Pointing local dev at prod secrets is one slipped env var away; making it structurally impossible is cheap insurance.
- **Depends on:** E9.S2

**E9.S6 — Smoke deploy (dev env live)**
- **User story:** As a stakeholder, I want a live URL where `/api/v1/health` returns 200 and the web app loads.
- **Acceptance criteria:**
  - `terraform apply envs/dev` produces a reachable ALB; `/api/v1/health` returns 200 on a public DNS name. — *Why:* A live URL is the proof the whole stack works; until then, every component is theoretical.
  - Web app at `/` loads and authenticates against the API. — *Why:* End-to-end auth is what reveals CORS/cookie/SSL issues that local compose hides.
  - Smoke test in CI hits `/api/v1/health` after each deploy and rolls back on failure. — *Why:* Manual post-deploy checks get skipped; automated rollback is what makes "deploy on every merge" safe.
  - Runbook documents deploy + rollback steps. — *Why:* Runbooks written before the first incident save the incident; written after, they're forensic.
  - Cost guardrail: dev env <$50/month idle. — *Why:* Idle costs sneak up on side projects; setting a budget early forces the smaller-instance choice that's almost always fine.
- **Depends on:** E9.S3, E9.S4, E9.S5

---

### E10 — UX Journey Acceptance Docs

**E10.S1 — Onboard journey**
- **User story:** As a stakeholder, I want a single-page doc tracing Onboard from connect → backfill → first forecast.
- **Acceptance criteria:**
  - Doc covers trigger, screens, API calls, data writes, failure modes, success criteria. — *Why:* These dimensions distinguish "works on the happy path" from "ships"; missing any one means a class of bug ships.
  - Steps cross-reference E4.S2/E4.S3/E5.S2/E7.S2. — *Why:* Cross-referencing keeps the journey doc in sync with implementation; orphan docs rot fastest.
  - Failure modes named with intended UX (auth denied, rate-limited, partial backfill, zero-velocity catalog). — *Why:* Listing failures by name forces the design conversation; "we'll handle errors" is not a design.
  - Success metric: time from "connect" to "first useful forecast view" <15 minutes for a 1-year-old store. — *Why:* Without a number, "fast onboarding" is a vibe; with one, it's testable.
  - Walked through with one stakeholder before merge. — *Why:* Solo-authored journey docs miss the obvious; one outside review catches 80% of those.
- **Depends on:** E4.S3, E7.S2, E5.S2

**E10.S2 — Daily check-in journey**
- **User story:** As a stakeholder, I want the Daily Check-in journey documented (web or Slack ask → agent answer with cited SKUs + days-of-cover).
- **Acceptance criteria:**
  - Three example questions documented with expected agent behavior + tool calls. — *Why:* Concrete examples are the difference between an aspirational doc and a testable one; tool-call expectations make eval cases trivial.
  - Cross-references to E6 + E7.S3. — *Why:* Same as E10.S1: cross-references keep the doc honest as code moves.
  - "What good looks like" defined: cites SKUs by name, cites days-of-cover, notes confidence. — *Why:* Vague success ("the agent is helpful") survives no PR review; specific success is testable.
  - Two failure modes covered: agent doesn't know, agent gives wrong answer. — *Why:* How an agent fails defines whether users trust it; designing failure modes is more important than designing happy paths.
- **Depends on:** E6.S4, E7.S3

**E10.S3 — Reorder triggered journey**
- **User story:** As a stakeholder, I want the Reorder Triggered journey documented (forecast flag → Slack alert → user ack writes to DB).
- **Acceptance criteria:**
  - Doc maps trigger logic (which `days_of_cover` threshold, eligibility rules). — *Why:* Threshold logic is the most-debated part of any reorder feature; pinning it in the doc precedes the inevitable bikeshed.
  - Slack alert format pinned (fields, blocks, action buttons). — *Why:* Blocks change message permission and delivery; deciding once means consistent alerts across the product.
  - Ack writes a `ReorderAck` row visible to subsequent agent answers. — *Why:* Closing the loop (agent → alert → ack → agent) is what turns the agent from chatbot into operator; this row is the data plumbing.
  - Demoable in compose: trigger forecast → Slack alert in mock channel → ack → ack visible in agent answer. — *Why:* End-to-end demoability is the only honest acceptance for a journey; partial demos hide integration bugs.
- **Depends on:** E5.S2, E6.S4

---

## Dependency Graph (high-level)

```
E1 ──► E2 ──► E3 ──► E4 ──► E5
              │       │      │
              ├──► E6 ◄──────┤
              ├──► E7 ◄──────┤
              ▼              ▼
              E8 ──► E9     E10 (cross-cutting acceptance)
```

- **E1** unblocks everything.
- **E2** is the keystone — every other epic reads or writes the data model.
- **E8** can land in parallel with E2/E3 since it's mostly orchestration.
- **E9** depends on E8 images and the Terraform module work.
- **E10** is cross-cutting and serves as acceptance for E4–E7.

## Suggested Sequencing (4-sprint MVP)

| Sprint | Focus | Stories |
|---|---|---|
| 1 | Foundations | E1.* fully; E2.S1–S4; E3.S1–S3; E8.S1–S3 |
| 2 | Shopify in | E2.S5; E3.S4–S6; E4.S1–S4; E1.S5/CI maturation |
| 3 | Forecast + Web | E4.S5; E5.S1–S4; E7.S1–S3; E10.S1 |
| 4 | Agent + Deploy | E6.S1–S5; E7.S4; E9.S1–S6; E10.S2–S3 |

## Open Questions To Park (not blocking MVP)

- Multi-tenant isolation: row-level vs. schema-per-tenant — defer until second customer.
- Agent framework lock-in (Claude Agent SDK vs. LangGraph) — revisit after the first real Slack conversations.
- Wiki/KB design — pulled from MVP; revisit in v2 alongside richer agent skills.
- "Ops Gym" RL environment — explicitly post-MVP; the data model should make this possible without redesign.
