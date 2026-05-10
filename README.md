# Foresight

#### Tired of always being reactive instead of proactive with your business operations? You need Foresight!

#### Blind, uninformed forecasts leading to over- or under-estimating operational demand? You need Foresight!

## About 

#### Foresight is a first-of-its-kind platform for DTC / e-com brands to streamline and optimize their operations. 

## Key Features

Data-first, AI native features:
- Secure cataloging and storing of your operational data (at any scale)
-- Order Data
-- Inventory Data
-- 
- Fleet of Agents to reason over organizational knoweldge and operational data to complete tasks on your behalf - extend your human team 
-- have converstations (integrate with chat / messaging tools ie. Slack)
-- "living" knowledge base (wiki-style for humans & agents to interract with)
-- define and schedule Skills and Tasks
- Traditional ML for forecasting 
- 
- (Future) "Ops Gym" - Reinforcement Learning environment generated from operational data for state-of-the-art forecasting


## Project Status

Foresight is in **early foundations** (Epic 1 — *Foundations & Tooling*). The repository is a documentation-only skeleton today; executable code, infrastructure, and the MVP vertical slice land across the epics planned in [`PLAN.md`](./PLAN.md).

| Epic | Theme | Status |
|---|---|---|
| E1 | Foundations & Tooling | 🟡 In progress (S0/S1/S2 done, S3 in review, S4–S6 pending) |
| E2 | Data Model & Storage | ⚪ Not started |
| E3 | API Foundation (FastAPI) | ⚪ Not started |
| E4 | Shopify Ingestion + Worker | ⚪ Not started |
| E5 | Forecasting Pipeline | ⚪ Not started |
| E6 | Agent Layer + Slack | ⚪ Not started |
| E7 | Web App (Next.js) | ⚪ Not started |
| E8 | Local Infrastructure | ⚪ Not started |
| E9 | AWS Infrastructure | ⚪ Not started |
| E10 | UX Journey Acceptance Docs | ⚪ Not started |

See `PLAN.md` for the full developer-story breakdown with acceptance criteria.

## Contributing

Contributors should read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before opening a PR. Quick reference:

- `main` is the **default branch** and tracks releases.
- `develop` is the **integration branch**; all feature PRs target it.
- One feature branch per story (`feature/{story-id}-{slug}`), one squash commit per branch.
- PRs go through the [PR template](./.github/PULL_REQUEST_TEMPLATE.md), require ≥80% test coverage on touched code (or a documented exemption), and must be approved before squash-merging.

## Roadmap

Detailed epics and developer stories are tracked in [`PLAN.md`](./PLAN.md). The MVP wedge is a thin vertical slice through three pillars:

1. **Data** — Shopify ingestion (orders + inventory) into Postgres, raw exports to S3.
2. **Forecast** — SKU-level days-of-cover / stockout prediction.
3. **Agent** — One Slack-surfaced agent that answers ops questions against the data layer.