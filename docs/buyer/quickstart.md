# Quickstart: AI Agent Repo Preflight Kit

Use this kit before you merge, demo, publish, or sell code produced with heavy AI assistance.

It answers one narrow question:

```text
Is this repository carrying obvious release blockers, process drift, risky public claims, or private-publication hygiene problems?
```

## 1. Run the local demo

```bash
python3 repo_preflight.py \
  --repo examples/sample-repo \
  --include-fixtures \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html \
  --out-sarif REPO_PREFLIGHT_REPORT.sarif
```

The sample repository intentionally fails. Open `REPO_PREFLIGHT_REPORT.md` or `REPO_PREFLIGHT_REPORT.html` to inspect the report.

## 2. Scan your repository

```bash
python3 repo_preflight.py \
  --repo /path/to/your/repo \
  --profile strict \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html
```

## 3. Scan before public release

```bash
python3 repo_preflight.py \
  --repo /path/to/your/repo \
  --profile public-export \
  --paranoid \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html \
  --out-sarif REPO_PREFLIGHT_REPORT.sarif
```

Use `--paranoid` before sharing reports outside a private workspace. It suppresses evidence snippets and reduces path detail.

## 4. Interpret the decision

- `READY`: no blockers detected by this deterministic preflight.
- `BLOCKED`: one or more blocker findings require review before release.

A clean report does not prove a repository is secure, compliant, correct, or production-ready. It only means this preflight did not find the specific release-discipline problems it checks for.
