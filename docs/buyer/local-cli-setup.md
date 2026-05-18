# Local CLI Setup

Use the local CLI when you want a private, deterministic scan without granting repository access to any external service.

## Requirements

- Python 3.10 through 3.13
- A local copy of the repository you want to scan
- No API keys
- No network calls required by the scanner itself

## Run against the included sample

```bash
python3 repo_preflight.py \
  --repo examples/sample-repo \
  --include-fixtures \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html \
  --out-sarif REPO_PREFLIGHT_REPORT.sarif
```

The sample intentionally returns a blocked decision so you can inspect the report format.

## Run against your own repository

```bash
python3 repo_preflight.py --repo /path/to/your/repo --profile strict
```

## Public export scan

Before publishing a repo, package, template, or Action:

```bash
python3 repo_preflight.py \
  --repo /path/to/your/repo \
  --profile public-export \
  --paranoid \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html
```

## Exit behavior

The scanner exits nonzero when blocker findings are present. That makes it usable in local release scripts and CI gates.

## Privacy behavior

Use `--paranoid` when a report may be shared outside your private workspace. It removes evidence snippets and uses lower-detail paths.
