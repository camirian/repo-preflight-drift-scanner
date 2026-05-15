# What This Is Not

This kit is deliberately narrow.

It is **not**:

- a security scanner
- a vulnerability scanner
- a compliance scanner
- a license scanner
- a static analyzer for program correctness
- a guarantee that a repository is safe
- a replacement for tests, code review, threat modeling, or release engineering

## What it does check

It checks deterministic release-discipline signals such as:

- missing process files
- unchecked release gates
- risky public claims
- secret-bearing filenames
- generated artifacts
- open work and draft-content drift markers
- public-export hygiene for repositories and downloadable packages

## Correct mental model

Use this kit as a preflight checklist with executable checks.

```text
It does not certify the aircraft.
It checks whether obvious preflight items were ignored.
```

## Claim boundary

Safe claim:

> This kit helps surface obvious process drift before you publish AI-assisted code.

Unsafe claim pattern:

> This kit guarantees that AI-generated code is safe or fully ready to ship.

Do not use unsafe guarantee-style claims in product pages, README files, listings, or customer-facing material.
