# `docs/`

Project documentation that doesn't belong in `README.md`, `CONTRIBUTING.md`, or `PLAN.md`.

| Subdir | Contents |
|---|---|
| `adr/` | Architecture Decision Records (E1.S6). Each ADR documents a load-bearing decision and the alternatives considered. |
| `journeys/` *(future)* | End-to-end user-journey docs (E10) — Onboard, Daily Check-in, Reorder Triggered. |
| `api/` *(future)* | API conventions and schema reference (E3). |

## Writing an ADR

Use `_template.md` (added in E1.S6) and number sequentially: `0001-<slug>.md`. Once an ADR is **Accepted**, it stays put — superseding it requires a new ADR that marks the old one `Superseded by ADR-NNNN`.

The bar: if the answer to a design question would surprise a future contributor, it deserves an ADR.
