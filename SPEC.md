# Repo Preflight Drift Scanner Specification

Status: draft local executable spec

## Purpose

Build a small executable tool that scans a repository and produces a preflight/drift report for AI-assisted development work.

This must be software, not another template bundle.

## User

Primary user:

- Developer using AI coding agents.
- Technical founder reviewing an AI-built repo.
- Maintainer who wants a fast pre-release sanity check.

## Goal

```text
repo path -> deterministic local scanner -> Markdown/JSON report with findings and release decision
```

Distribution path:

```text
CLI first -> composite GitHub Action -> CI artifact reports
```

## Non-Goals

Do not:

- Claim security scanning.
- Claim compliance coverage.
- Call external APIs.
- Read secrets or print secret contents.
- Modify the scanned repo.
- Replace human review.
- Depend on a SaaS account.

## Data Boundary

Allowed:

- File names.
- Text content from ordinary source and documentation files.
- Synthetic sample repos.
- This repo's non-secret docs for internal testing.

Forbidden:

- `.env` contents.
- Private keys.
- Credential files.
- Binary blobs.
- Build artifacts too large to inspect safely.
- Employer, customer, regulated, or sensitive data.

## Runtime Boundary

Version 0:

- Python standard library only.
- Local filesystem only.
- No network.
- No dependencies.
- Read-only scan.
- GitHub Action wrapper must call the same local scanner, not a separate implementation.

## Functional Requirements

The scanner must:

- Accept a repo path.
- Produce a Markdown report.
- Produce a JSON report.
- Detect missing process files such as README, spec, verification plan, and release checklist.
- Detect risky public claims in product/docs copy.
- Detect common secret-bearing filenames without reading their contents.
- Detect unchecked release/preflight checklist items.
- Detect generated artifacts and cache directories.
- Detect likely AI/process drift terms such as open work markers and vague draft-content signals.
- Support a strict profile and a docs profile to reduce template/checklist/report false positives.
- Return non-zero exit code when blocker-level findings exist.
- Provide a composite GitHub Action with report-only mode and fail-on-blockers mode.

## Finding Levels

- `blocker`: should block release.
- `warning`: needs review.
- `info`: useful context.

## Verification Requirements

Use a synthetic sample repo with:

- Missing verification plan.
- Unchecked pre-release checklist item.
- Risky claim in README.
- Secret-bearing filename.
- Cache directory.

Expected:

- Scanner reports blocker findings.
- Scanner does not print secret file contents.
- Scanner writes Markdown and JSON reports.
- Scanner exits non-zero for blockers.
- GitHub Action entrypoint can run locally in report-only mode and generate the same report shape.

## Monetization Hypothesis

Free version:

- Local CLI scan.
- Markdown/JSON report.
- Basic rule set.

Potential paid expansion:

- GitHub Action.
- CI annotations.
- Rule packs.
- Team/project profiles.
- Before/after report diff.
- HTML report.
- Hosted dashboard.

## Stop Conditions

Stop if:

- The tool is just a wrapper around static templates.
- It requires account setup before producing value.
- It reads or prints secrets.
- It needs a meeting to explain.
- It cannot produce a useful report in under one minute.
