# GitHub Action Setup

Use the GitHub Action when you want Repo Preflight to run as part of a repository workflow.

## Basic setup

1. Add a workflow file under `.github/workflows/` in the repository you want to scan.
2. Check out the repository.
3. Reference the Action with `camirian/repo-preflight-drift-scanner@main`. Pin to a published release tag instead once one is available.
4. Choose a profile: `strict`, `docs`, `dora-ai-readiness`, or `public-export`.
5. Save Markdown, JSON, HTML, or SARIF reports as needed.

Pin to a specific release tag when one is published; otherwise `@main` tracks the current default branch.

## Recommended settings

For normal pull-request checks, use `strict`. It is the default release-discipline profile for code and release artifacts.

```yaml
with:
  repo: "."
  profile: strict
```

For documentation-heavy repositories, samples, or user instructions where unchecked boxes and example claims would create noise, use `docs`. Treat it as a low-noise documentation pass, not a release gate for code or public artifacts.

```yaml
with:
  repo: "."
  profile: docs
```

For AI-assisted repositories that need DORA AI capability evidence, use `dora-ai-readiness`. It checks only for documented AI stance, data boundary, AI-accessible context, version-control and rollback path, small-batch delivery, user or user focus, and internal-platform verification.

This profile is part of the v0.5 candidate. Use it from the local package Action path or a ref that explicitly includes v0.5 candidate code until a v0.5 tag is published.

```yaml
- uses: ./
  with:
    repo: "."
    profile: dora-ai-readiness
    out-md: dora-ai-readiness.md
    out-json: dora-ai-readiness.json
    out-sarif: dora-ai-readiness.sarif
```

This profile emits one DORA finding per capability: an info finding when evidence is found, or a blocker when evidence is missing. See [DORA AI readiness](../dora-ai-readiness.md) for the full capability list and non-certification boundaries.

For a repository, template, package, Action, or downloadable product that will become public, use `public-export` with `paranoid: true`. This adds public-export hygiene checks and privacy-first report handling.

```yaml
with:
  repo: "."
  profile: public-export
  paranoid: true
```

For an old repository with known drift, start with report-only mode by setting `fail-on-blockers: false`, then move to blocking mode after the known findings are fixed or accepted. If you save a prior JSON report as a baseline, you can instead set `baseline-json` and `fail-on-new-blockers-only: true` to fail only when new blocker findings appear.

## Inputs to know

- `repo`: path to scan, usually `.`
- `profile`: `strict`, `docs`, `dora-ai-readiness`, or `public-export`
- `paranoid`: privacy-first path and evidence handling
- `out-md`: Markdown report path
- `out-json`: JSON report path. Automation consumers should validate it with the version-pinned schema artifact described in [JSON report schema](../report-schema.md).
- `out-html`: optional HTML report path
- `out-sarif`: optional SARIF report path
- `baseline-json`: optional prior JSON report path for before/after diffing
- `fail-on-new-blockers-only`: with `baseline-json`, fail only when blocker findings are new versus the baseline
- `fail-on-blockers`: whether blocker findings fail the workflow

## user note

The Action is useful when the user wants the same deterministic preflight behavior to run repeatedly without manually invoking the local CLI. A clean Action run is not proof that a repository is secure, compliant, correct, DORA-certified, DORA-mature, or ready to ship; it only means the selected profile did not find the specific documentation or release-discipline problems it checks for.
