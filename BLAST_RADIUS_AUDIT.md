# Repo Preflight Drift Scanner Blast Radius Audit

Status: draft

## System Under Test

Local deterministic repo scanner.

## What Can Go Wrong

- The scanner may read or print secret contents.
- The scanner may overclaim as a security or compliance tool.
- The scanner may flag too many false positives.
- The scanner may miss important release risks.
- The scanner may mutate scanned files accidentally.

## Prohibited Claims

Do not claim:

- Security scanner.
- Compliance scanner.
- Secret scanner.
- Vulnerability scanner.
- Production readiness guarantee.
- Replacement of human code review.
- Replacement of legal, security, compliance, or safety review.

## Excluded Data

Do not read or print:

- `.env` contents.
- Private keys.
- Tokens.
- Credentials.
- Customer data.
- Employer data.
- Regulated data.

## Stop Conditions

Block release if:

- Any secret-bearing file content is printed.
- The scanner modifies the scanned repo.
- Reports contain private data from forbidden files.
- The product copy implies security/compliance coverage.

## Current Mitigations

- Filename-level secret detection only.
- Text extensions allowlist.
- Size limit before reading.
- Local read-only scanner.
- No network or dependencies.

## Residual Risk

The scanner is a release-discipline tool. It does not prove security, correctness, or compliance.
