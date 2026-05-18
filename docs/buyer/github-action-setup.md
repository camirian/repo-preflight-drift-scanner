# GitHub Action Setup

Use the GitHub Action when you want Repo Preflight to run as part of a repository workflow.

## Basic setup

1. Add a workflow file under `.github/workflows/` in the repository you want to scan.
2. Check out the repository.
3. Run `camirian/repo-preflight-drift-scanner@v0.3.3`.
4. Choose a profile: `strict`, `docs`, or `public-export`.
5. Save Markdown, JSON, HTML, or SARIF reports as needed.

Use the latest published Action tag unless your release package explicitly includes a newer tag.

## Recommended settings

For normal pull-request checks, use `strict`. It is the default release-discipline profile for code and release artifacts.

```yaml
with:
  repo: "."
  profile: strict
```

For documentation-heavy repositories, samples, or buyer instructions where unchecked boxes and example claims would create noise, use `docs`. Treat it as a low-noise documentation pass, not a release gate for code or public artifacts.

```yaml
with:
  repo: "."
  profile: docs
```

For a repository, template, package, Action, or downloadable product that will become public, use `public-export` with `paranoid: true`. This adds public-export hygiene checks and privacy-first report handling.

```yaml
with:
  repo: "."
  profile: public-export
  paranoid: true
```

For an old repository with known drift, start with report-only mode by setting `fail-on-blockers: false`, then move to blocking mode after the known findings are fixed or accepted.

## Inputs to know

- `repo`: path to scan, usually `.`
- `profile`: `strict`, `docs`, or `public-export`
- `paranoid`: privacy-first path and evidence handling
- `out-md`: Markdown report path
- `out-json`: JSON report path
- `out-html`: optional HTML report path
- `out-sarif`: optional SARIF report path
- `fail-on-blockers`: whether blocker findings fail the workflow

## Buyer note

The Action is useful when the buyer wants the same deterministic preflight behavior to run repeatedly without manually invoking the local CLI. A clean Action run is not proof that a repository is secure, compliant, correct, or ready to ship; it only means the selected profile did not find the specific release-discipline problems it checks for.
