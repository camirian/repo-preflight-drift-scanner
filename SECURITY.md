# Security Policy

## Scope

Repo Preflight Drift Scanner is a deterministic preflight utility for release discipline.

It is not a security scanner, compliance scanner, vulnerability scanner, secret scanner, or substitute for human review.

## Data Handling

The scanner is designed to:

- run locally or inside the caller's GitHub Actions runner
- avoid external network calls
- avoid reading known secret-bearing filenames
- report secret-bearing filenames without printing their contents
- write reports only to caller-provided output paths

## Reporting Issues

Open a GitHub issue for:

- false positives that make reports noisy
- missing high-value checks
- report rendering bugs
- GitHub Action behavior bugs

Do not paste real secrets, private keys, tokens, regulated data, customer data, or employer data into issues.

## Private Data Guidance

When using the scanner on private repositories:

- upload reports only as private artifacts
- review report evidence snippets before sharing externally
- prefer `fail-on-blockers: false` for first-time scans
- treat SARIF upload as public to repository collaborators

## Supported Versions

Use the latest tagged release.
