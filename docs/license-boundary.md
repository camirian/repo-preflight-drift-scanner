# License Boundary

Status: release-gate documentation, not legal advice

This document records the current license boundary facts for release review. It does not modify `LICENSE`, `buyer-license.txt`, package contents, or any granted permissions.

## Current Fact Pattern

- The root repository contains `LICENSE`, which is an MIT license for the repository source and associated documentation.
- The generated buyer ZIP includes `buyer-license.txt`.
- The buyer ZIP is currently built by `scripts/package_release.sh` and includes buyer-useful files plus `buyer-license.txt`.
- The release criteria require the buyer artifact boundary to be checked separately from the source tree.
- The current source-license and buyer-ZIP-license boundary needs an explicit owner decision before any paid listing, public package upload, public tag, release, or additional public promotion.

## Decision Required Before Paid Or Public Release

Before paid release or additional public distribution, the owner must decide whether the intended distribution model is:

- Open-source repository distribution under the root MIT license.
- Paid buyer ZIP distribution under `buyer-license.txt`, recognizing that buyer terms may not restrict rights already granted for public MIT-licensed copies of the same files.
- A dual-distribution model with a clearly documented boundary between source availability and buyer artifact terms.
- A different model that requires updating the source license, buyer license, package contents, or release plan.

This decision should be recorded in the release notes or release checklist before paid release or additional distribution. If there is any uncertainty about enforceability, compatibility, or customer-facing wording, get qualified legal review; this document is an engineering release-control note only.

## Acceptance Checklist

Before paid release or additional public distribution, confirm each item is complete:

- Owner has reviewed the root MIT license and `buyer-license.txt` together.
- Owner has decided whether to keep the source repository public as-is, change the release boundary, or alter the paid ZIP model before offering the package.
- Owner has decided whether the buyer ZIP may contain files that are also available from the MIT-licensed repository.
- Owner has decided whether the paid listing copy, buyer docs, and package contents accurately describe the license boundary.
- Any required legal review is complete or explicitly waived by the owner.
- The release notes record the final owner decision before paid release or additional public distribution.
- No paid upload, tag, release, or additional public listing proceeds while this checklist is unresolved.

## Verification Commands

Confirm the source license and buyer license files exist:

```bash
test -f LICENSE
test -f buyer-license.txt
```

Build the buyer ZIP and confirm it includes `buyer-license.txt`:

```bash
bash scripts/package_release.sh v0.4
python3 -m zipfile -l release/ai-agent-repo-preflight-kit-v0.4.zip | rg 'buyer-license\.txt'
```

Run release-boundary checks:

```bash
python3 verify_scanner.py
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
```

The public-export scan checks release hygiene. It does not decide license compatibility or replace owner/legal review.
