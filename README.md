# Repo Preflight Drift Scanner

Status: public GitHub Action and local CLI

Repo Preflight Drift Scanner is a deterministic local CLI and GitHub Action for AI-assisted development workflows.

Use it before merge, demo, release, or public export.

It answers one practical question before you merge, demo, or publish:

```text
Is this repo carrying obvious release blockers, risky claims, private-publication surfaces, or AI-process drift?
```

It produces Markdown, JSON, HTML, and SARIF reports covering:

- missing process files
- unchecked release gates
- risky public claims
- secret-bearing filenames
- generated artifacts
- open work and draft-content drift signals
- public-export hygiene for public repos and packages

See [docs/report-schema.md](docs/report-schema.md) for the JSON report schema and [docs/sarif-output.md](docs/sarif-output.md) for SARIF behavior.

## Quick Start

GitHub Action:

```yaml
- uses: camirian/repo-preflight-drift-scanner@v0.3.3
  with:
    repo: "."
    profile: public-export
    paranoid: true
```

Local CLI:

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid
```

## Python Support

The local CLI and verifier support Python 3.10 through 3.13.

## Install In GitHub Actions

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
      - uses: camirian/repo-preflight-drift-scanner@v0.3.3
        with:
          repo: "."
          profile: public-export
          paranoid: true
          out-html: REPO_PREFLIGHT_REPORT.html
          out-sarif: REPO_PREFLIGHT_REPORT.sarif
```

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

- `strict`: normal release-discipline checks before merge, demo, handoff, or release artifact.
- `docs`: low-noise scans for template-heavy documentation, sample reports, and buyer instructions.
- `public-export`: checks before publishing a repo, package, Action, template, or downloadable product; use paranoid mode when reports may leave a private workspace.

CLI examples:

```bash
python3 repo_preflight.py --repo . --profile strict
python3 repo_preflight.py --repo . --profile docs
python3 repo_preflight.py --repo . --profile public-export --paranoid
```

GitHub Action input examples:

```yaml
with:
  repo: "."
  profile: strict
```

```yaml
with:
  repo: "."
  profile: docs
```

```yaml
with:
  repo: "."
  profile: public-export
  paranoid: true
```

See [docs/buyer/how-to-use-the-kit.md](docs/buyer/how-to-use-the-kit.md) for profile selection guidance.

## Rule Packs

Rule packs are JSON files passed with `--config`.

```bash
python3 repo_preflight.py --repo . --config configs/founder-strict.json
```

See [docs/rule-packs.md](docs/rule-packs.md) for supported keys, merge behavior, and a compact config example.

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
      - uses: camirian/repo-preflight-drift-scanner@v0.3.3
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

## 60-Second Demo

1. Run the scanner against the synthetic sample:

   ```bash
   python3 repo_preflight.py --repo examples/sample-repo --include-fixtures
   ```

2. The scanner blocks the repo because it contains missing process docs, unchecked gates, risky claims, generated artifacts, and drift markers.
3. Open `REPO_PREFLIGHT_REPORT.md` to see the fix list.
4. Run against your repo with `--profile public-export --paranoid` before publishing.

The scanner is intentionally conservative. It is designed to make obvious release blockers visible before they become public cleanup work.

## Verify

```bash
python3 verify_scanner.py
```

## Boundary

This is not a security scanner, compliance scanner, vulnerability scanner, or replacement for human review.

It is a deterministic preflight report generator for release discipline.
