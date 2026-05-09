# Repo Preflight Drift Scanner Demo

This demo shows the scanner catching release blockers in a synthetic repository.

## Local Run

```bash
python3 repo_preflight.py \
  --repo examples/sample-repo \
  --include-fixtures \
  --out-md REPORT.md \
  --out-json REPORT.json \
  --out-html REPORT.html \
  --out-sarif REPORT.sarif
```

Expected result:

```text
Repo preflight found blockers.
```

The report marks the sample repository as blocked because it has missing process files, unchecked release gates, risky public wording, a secret-bearing filename, generated artifacts, and draft-content drift signals.

## Rule-Pack Run

```bash
python3 repo_preflight.py \
  --repo examples/sample-repo \
  --include-fixtures \
  --config configs/founder-strict.json \
  --out-md RULE_PACK_REPORT.md \
  --out-json RULE_PACK_REPORT.json
```

## Clean Self-Scan

```bash
python3 repo_preflight.py --repo . --out-md SELF_REPORT.md --out-json SELF_REPORT.json
```

Expected result:

```text
Repo preflight ready.
```

The self-scan demonstrates that the tool can grade its own product folder cleanly after generated reports and fixture paths are excluded by default.

## GitHub Action Use

Copy [examples/github-action.yml](examples/github-action.yml) into `.github/workflows/repo-preflight.yml` in a repository that should be checked on pull requests.

The action writes:

- `REPO_PREFLIGHT_REPORT.md`
- `REPO_PREFLIGHT_REPORT.json`
- `REPO_PREFLIGHT_REPORT.html`
- `REPO_PREFLIGHT_REPORT.sarif`

The workflow fails when blocker findings exist unless `fail-on-blockers` is set to `false`.

## Boundary

This is a local preflight utility. It does not replace review and does not claim security, compliance, or vulnerability coverage.
