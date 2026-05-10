# `scripts/`

Operator and developer scripts that don't belong in `Makefile` targets directly. Examples (future):

- One-off data backfills and migrations.
- Local cluster bootstrapping helpers (`compose-up.sh` wrapper).
- Seed-data generators with non-trivial logic.

Conventions:
- Bash or Python only; if a script grows past ~100 lines, it usually belongs inside the `foresight` package as a proper module with an entrypoint.
- Every script must include a `--help` flag and exit non-zero on error.
- Scripts that touch AWS use the same `AWS_PROFILE` resolution as `foresight.settings` and refuse to run against `prod` without an explicit `FORESIGHT_ENV=prod` env var.
