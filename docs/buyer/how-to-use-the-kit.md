# How To Use The Kit

This kit is for developers and founders who use AI coding agents and need a small, repeatable release check before publishing work.

## Recommended workflow

```text
1. Build with your AI coding agent.
2. Run your normal tests and project checks.
3. Run Repo Preflight.
4. Read the blocker list.
5. Fix or consciously accept each finding.
6. Re-run before merge, demo, or public export.
```

## Profiles

### strict

Use this before a merge, demo, handoff, or release artifact.

```bash
python3 repo_preflight.py --repo . --profile strict
```

### docs

Use this when scanning template-heavy documentation where unchecked boxes, sample claims, and old generated reports would create too much noise.

```bash
python3 repo_preflight.py --repo . --profile docs
```

### public-export

Use this before publishing a repository, package, GitHub Action, template, or downloadable product.

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid
```

## Report outputs

- Markdown: human-readable fix list.
- JSON: machine-readable results for automation or baselines. See [JSON report schema](../report-schema.md).
- HTML: shareable local report.
- SARIF: code-scanning compatible format.

## Rule packs

Use JSON rule packs with `--config` to add team-specific terms, generated directories, exclusions, and required process-file labels. See [rule packs](../rule-packs.md) for supported keys and merge behavior.

## Baseline diff

After a known report is saved, compare a future run against it:

```bash
python3 repo_preflight.py \
  --repo . \
  --baseline-json previous/REPO_PREFLIGHT_REPORT.json \
  --out-json REPO_PREFLIGHT_REPORT.json
```

This helps separate new drift from already-known drift.

## Privacy mode

For reports that may leave your machine or private repository:

```bash
python3 repo_preflight.py --repo . --paranoid --path-mode basename --no-evidence
```

Use the redaction option when a term should never appear in evidence snippets.

## Buyer rule

Do not treat this kit as proof that a repository is safe. Treat it as a fast, deterministic preflight for obvious release-discipline failures.
