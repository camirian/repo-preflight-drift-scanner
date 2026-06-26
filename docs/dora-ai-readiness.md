# DORA AI Readiness

The `dora-ai-readiness` profile checks whether an AI-assisted repository contains explicit documentation evidence for seven DORA AI capability surfaces.

It is a deterministic documentation-evidence scan. It does not certify DORA maturity, security, compliance, governance approval, model safety, deployment safety, or production readiness.

## When To Use It

Use this profile when a team wants a repeatable answer to:

```text
Does this repo document the basic AI-assisted delivery practices a reviewer would expect to see?
```

Run it before an internal review, user handoff, AI-workflow audit, or roadmap checkpoint. It is not a substitute for tests, security review, legal review, privacy review, model evaluation, or human judgment.

## What It Checks

The profile looks for one documented evidence surface for each capability:

| Capability | Expected evidence |
| --- | --- |
| AI stance | What AI may do, what requires human review, and what AI must not do. |
| Data boundary | Allowed sources, forbidden data, freshness ownership, retention boundaries, secrets, or private-data limits. |
| AI-accessible context | Docs, schemas, examples, runbooks, evidence packs, `AGENTS.md`, or other context that agents can safely use. |
| Version control and rollback | Commit discipline, review path, rollback path, release manifest, changelog, or pre-release handling. |
| Small batches | Small independently useful slices, acceptance criteria, next slice, or kill criteria. |
| User or user focus | Primary user, user, customer, job-to-be-done, success signal, or feedback signal. |
| Internal platform path | Repeatable setup, quickstart, verification command, release path, or handoff path. |

The scanner searches text-like files for configured terms associated with each capability. It reports the first evidence location it finds for each capability.

## CLI Examples

Write Markdown and JSON reports:

```bash
python3 repo_preflight.py \
  --repo . \
  --profile dora-ai-readiness \
  --out-md dora-ai-readiness.md \
  --out-json dora-ai-readiness.json
```

Use privacy-first output before sharing a report outside a private workspace:

```bash
python3 repo_preflight.py \
  --repo . \
  --profile dora-ai-readiness \
  --paranoid \
  --out-md dora-ai-readiness.md \
  --out-json dora-ai-readiness.json
```

Add SARIF for CI review surfaces:

```bash
python3 repo_preflight.py \
  --repo . \
  --profile dora-ai-readiness \
  --out-sarif dora-ai-readiness.sarif
```

## GitHub Action Example

The `dora-ai-readiness` profile is part of the v0.5 candidate. Until a v0.5 tag is published, use the local Action path in this repository or a branch/ref that explicitly includes the profile.

```yaml
name: DORA AI Readiness

on:
  pull_request:
  workflow_dispatch:

jobs:
  dora-ai-readiness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./
        with:
          repo: "."
          profile: dora-ai-readiness
          out-md: dora-ai-readiness.md
          out-json: dora-ai-readiness.json
          out-sarif: dora-ai-readiness.sarif
```

## Output Behavior

The profile emits one DORA-specific finding per capability:

- Evidence found: `info` finding with code `dora_<capability>_evidence`.
- Evidence missing: `blocker` finding with code `missing_dora_<capability>`.

Current capability code names are:

- `ai_stance`
- `data_boundary`
- `ai_accessible_context`
- `version_control`
- `small_batches`
- `user_focus`
- `internal_platform`

The overall decision is `READY` only when no blocker findings are present. For this profile, `READY` means all seven documentation-evidence surfaces were detected. It does not mean the documentation is complete, correct, adopted, independently validated, or sufficient for production use.

## Boundaries

This profile does not check source-code correctness, runtime behavior, deployment safety, model quality, security vulnerabilities, privacy compliance, legal compliance, operational maturity, or actual DORA metric performance.

Use `strict` for normal release-discipline checks. Use `public-export --paranoid` before publishing a repository, package, template, Action, or downloadable product.
