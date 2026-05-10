# Foresight — top-level Makefile.
#
# One consistent way to run common dev / CI tasks. Every target is .PHONY
# (none produce files). Add a `## description` comment after the target
# definition and `make help` will pick it up automatically.
#
# Pattern: contributors should never need to invoke `uv`, `pnpm`, or
# `pytest` directly during day-to-day work. `make help` is the canonical
# entrypoint.

.DEFAULT_GOAL := help

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

# ----- Node version detection -----
# Prefer the keg-only Node 22 LTS install (set up in E1.S1) so `pnpm`
# operations run on the same Node line that CI / Docker will use. Fall
# back to whatever `node` is on PATH otherwise; `engine-strict=false`
# in `web/.npmrc` keeps things working on developer machines with
# different Node versions.
NODE22_BIN := /opt/homebrew/opt/node@22/bin
NODE_PATH_PREFIX := $(if $(wildcard $(NODE22_BIN)/node),$(NODE22_BIN):,)
PNPM := PATH="$(NODE_PATH_PREFIX)$$PATH" pnpm

# ----- Stub helper -----
# Used by targets whose real implementation lands in a later story. Prints
# a clear pointer so contributors know where to look.
define _stub
@echo "🚧 \`make $(1)\` is a stub. The real implementation lands in story $(2)."
@echo "   See PLAN.md → $(2) for details."
endef

# ====================================================================
# Help (default)
# ====================================================================

.PHONY: help
help:  ## Show this help message
	@printf "\033[1mForesight — make targets\033[0m\n\n"
	@awk 'BEGIN {FS = ":.*?## "} \
	     /^[a-zA-Z0-9_-]+:.*?## / { \
	       printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 \
	     }' $(MAKEFILE_LIST)
	@printf "\n\033[2mTargets marked 🚧 are stubs awaiting a future story.\033[0m\n"

# ====================================================================
# Setup
# ====================================================================

.PHONY: install
install: install-py install-web  ## Install Python and Node deps (run after clone)

.PHONY: install-py
install-py:  ## Install Python deps via uv
	uv sync

.PHONY: install-web
install-web:  ## Install Node deps via pnpm
	cd web && $(PNPM) install

# ====================================================================
# Quality gates (Python)
# ====================================================================

.PHONY: test
test:  ## Run pytest with coverage
	uv run pytest

.PHONY: fmt
fmt:  ## Format Python code (ruff format)
	uv run ruff format foresight tests

.PHONY: lint
lint:  ## Lint, type-check, and verify layering (ruff + mypy + import-linter)
	uv run ruff check foresight tests
	uv run mypy
	uv run lint-imports

.PHONY: hooks
hooks:  ## Install pre-commit on PATH and register git hooks
	# Install pre-commit as a uv tool so it stays on PATH even when the
	# project venv is re-synced. Idempotent. See CONTRIBUTING.md.
	uv tool install pre-commit
	uv tool run pre-commit install

.PHONY: pre-commit
pre-commit:  ## Run all pre-commit hooks against every file in the repo
	uv run pre-commit run --all-files

.PHONY: ci
ci: install lint test  ## CI meta-target: install + lint + test (mirrors what CI will run in E1.S5)

# ====================================================================
# Web app (Next.js)
# ====================================================================

.PHONY: web-dev
web-dev:  ## Run the Next.js dev server
	cd web && $(PNPM) dev

.PHONY: web-build
web-build:  ## Build the Next.js app for production
	cd web && $(PNPM) build

.PHONY: web-lint
web-lint:  ## Lint the web app (next lint + tsc)
	cd web && $(PNPM) lint
	cd web && $(PNPM) type-check

# ====================================================================
# Stack lifecycle (stubs — land in E8.S1)
# ====================================================================

.PHONY: up
up:  ## 🚧 Boot the local Docker Compose stack
	$(call _stub,up,E8.S1)

.PHONY: down
down:  ## 🚧 Tear down the local Docker Compose stack
	$(call _stub,down,E8.S1)

# ====================================================================
# Data / database (stubs — land in E2.S4 / E2.S5)
# ====================================================================

.PHONY: migrate
migrate:  ## 🚧 Apply Alembic database migrations
	$(call _stub,migrate,E2.S4)

.PHONY: seed
seed:  ## 🚧 Populate the database with synthetic Shopify-shaped data
	$(call _stub,seed,E2.S5)

# ====================================================================
# Maintenance
# ====================================================================

.PHONY: clean
clean:  ## Remove caches, venvs, and build artifacts (destructive)
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -not -path "./node_modules/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf web/node_modules web/.next web/.turbo
	@echo "✓ Cleaned. Run \`make install\` to set up again."
