<!--
Foresight per-story PR template. See CONTRIBUTING.md and CLAUDE.md for the full
workflow. Every section below is required unless explicitly marked N/A with a reason.
-->

## Story

<!-- The story ID from PLAN.md, e.g. E2.S1. Link the section: -->
**Story ID:** `<E#.S#>` — [link to PLAN.md section](../blob/develop/PLAN.md#)

## Summary

<!-- 1-3 sentences. What does this PR change and why does it matter? -->

## Implementation Steps

<!--
Bulleted, ordered list of what was actually built. One bullet per
discrete change; reference file paths where relevant.
-->

- [ ] …
- [ ] …

## Validation Steps

<!--
How was the change verified? Include exact commands run locally and
their results. Anything that depends on infra (compose up, AWS, etc.)
should be called out.
-->

- [ ] `pytest` — *paste result summary*
- [ ] Coverage — *paste % or "N/A: see exemption below"*
- [ ] Manual smoke checks — *list each*

## Test Coverage

<!--
Required: state coverage % for files touched in this PR, OR
state "N/A" with an explicit exemption reason. The 80% gate from
CLAUDE.md only applies to PRs containing testable code.
-->

**Coverage:** <!-- e.g. "84% on services/api/routers/forecasts.py" or "N/A — pure docs/infra story, see exemption below" -->

**Exemption (if N/A):** <!-- delete if not applicable -->

## Acceptance Criteria

<!--
Copy the acceptance criteria for this story from PLAN.md and check
each one off here. PRs that don't satisfy every criterion are not
ready for UAT.
-->

- [ ] …
- [ ] …

## Reviewer Checklist

- [ ] **PR base is `develop`, not `main`** *(GitHub defaults to `main`; verify the base before merging)*
- [ ] Branch name is `feature/<story-id>-<slug>`
- [ ] Single commit (or will be after squash merge)
- [ ] Commit message follows the markdown convention (see `CONTRIBUTING.md`)
- [ ] No secrets, `.env` files, or large binaries committed
- [ ] No `--no-verify`, no force-pushes to shared branches
- [ ] `PLAN.md` and/or `README.md` updates queued for the documentation phase

## Linked Issues / Artifacts

<!-- Optional: links to related issues, ADRs, design docs, screenshots, etc. -->

---

_This PR is opened for **User Acceptance Testing (UAT)**. Do **not** merge until the user has explicitly approved._
