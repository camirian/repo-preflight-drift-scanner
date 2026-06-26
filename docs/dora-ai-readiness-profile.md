# DORA AI Readiness Profile

Status: active profile guide

## Purpose

The `dora-ai-readiness` profile checks whether a repo has explicit local evidence for the seven DORA AI capability surfaces:

- AI stance
- data boundary
- AI-accessible context
- version control and rollback
- small batches
- user or user focus
- internal platform path

It is an evidence profile. It does not certify maturity, security, compliance, public-export safety, secret hygiene, or production readiness.

## SDLC Boundary

The profile is aligned to the Codex workstation SDLC in `codex-workstation-config/codex/AGENTS.md`.

The profile should count phrases that indicate real operating discipline, such as:

- `human review`
- `allowed working surface`
- `forbidden data`
- `artifact boundary audit`
- `public-surface audit`
- `remote preservation`
- `git ls-remote`
- `protected branch`
- `pre-push guard`
- `rollback notes`
- `risk tier`
- `acceptance criteria`
- `verification path`
- `maintenance impact`
- `explicit user approval`
- `github preservation audit`

The profile should avoid broad one-word evidence such as `commit`, `verify`, `setup`, `customer`, or `secrets`. Those words can appear in ordinary prose without proving a DORA capability exists.

## Separation From Safety Profiles

Use this profile when the question is:

```text
Does this repo document the delivery-system evidence needed for AI-assisted work?
```

Use `strict` or `public-export` when the question is:

```text
Is this repo safe enough for merge, handoff, package creation, publication, or customer delivery?
```

The DORA profile intentionally skips secret-bearing filename blockers so local virtual environments and intentional fixtures do not become false readiness blockers. Secret-bearing filename checks remain active in `strict` and `public-export`.

## Verification

Run the verifier after changing the profile, evidence terms, skip behavior, output schema, or fixtures:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/repo-preflight-pycache python3 verify_scanner.py
```

The verifier includes a DORA-ready fixture with an intentional `credentials.json` file. The DORA scan must not read or print that file content, and it must not block the evidence profile because of the filename alone.

## Portfolio Use

For a portfolio baseline, run:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/repo-preflight-pycache python3 repo_preflight.py --repo <repo> --profile dora-ai-readiness --out-md dora-ai-readiness.md --out-json dora-ai-readiness.json
```

Then use strict or public-export checks separately for release, publication, or customer-artifact decisions.
