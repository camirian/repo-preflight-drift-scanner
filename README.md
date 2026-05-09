# Repo Preflight Drift Scanner

Status: local v0

Repo Preflight Drift Scanner is a local CLI and GitHub Action for AI-assisted development workflows.

It produces Markdown, JSON, HTML, and SARIF reports covering:

- missing process files
- unchecked release gates
- risky public claims
- secret-bearing filenames
- generated artifacts
- open work and draft-content drift signals

## Local Run

```bash
python3 repo_preflight.py \
  --repo . \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json \
  --out-html REPO_PREFLIGHT_REPORT.html \
  --out-sarif REPO_PREFLIGHT_REPORT.sarif
```

Profiles:

```bash
python3 repo_preflight.py --repo . --profile strict
python3 repo_preflight.py --repo . --profile docs
```

Use `strict` for release artifacts. Use `docs` when scanning template-heavy documentation where unchecked boxes, claim examples, and old generated artifacts would create noise.

## Rule Packs

Rule packs are JSON files passed with `--config`.

```bash
python3 repo_preflight.py --repo . --config configs/founder-strict.json
```

Included examples:

- [configs/founder-strict.json](configs/founder-strict.json)
- [configs/team-policy.json](configs/team-policy.json)

## Baseline Diff

Compare a new run against a previous JSON report:

```bash
python3 repo_preflight.py \
  --repo . \
  --baseline-json previous/REPO_PREFLIGHT_REPORT.json \
  --out-json REPO_PREFLIGHT_REPORT.json
```

## Privacy Controls

Use paranoid mode before sharing reports outside a private repo:

```bash
python3 repo_preflight.py \
  --repo . \
  --paranoid \
  --out-md REPO_PREFLIGHT_REPORT.md \
  --out-json REPO_PREFLIGHT_REPORT.json
```

Privacy-related options:

- `--paranoid`: basename-only paths and no evidence snippets
- `--no-evidence`: omit evidence snippets
- `--max-evidence-chars 80`: shorten evidence snippets
- `--redact-pattern REGEX`: redact matching evidence text
- `--path-mode relative|basename|hash`: control path detail in reports

## GitHub Action

```yaml
name: Repo Preflight

on:
  pull_request:
  workflow_dispatch:

jobs:
  repo-preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: your-org/repo-preflight-drift-scanner@v0
        with:
          repo: "."
          profile: strict
          out-html: REPO_PREFLIGHT_REPORT.html
          out-sarif: REPO_PREFLIGHT_REPORT.sarif
```

See [examples/github-action.yml](examples/github-action.yml) for a fuller workflow that uploads reports as artifacts.

## Demo

```bash
python3 repo_preflight.py \
  --repo examples/sample-repo \
  --include-fixtures \
  --out-md REPORT.md \
  --out-json REPORT.json \
  --out-html REPORT.html \
  --out-sarif REPORT.sarif
```

The synthetic sample intentionally blocks so users can inspect the report format without using private project data.

## Verify

```bash
python3 verify_scanner.py
```

## Boundary

This is not a security scanner, compliance scanner, vulnerability scanner, or replacement for human review.

It is a deterministic preflight report generator for release discipline.
