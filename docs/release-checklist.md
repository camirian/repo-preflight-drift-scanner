# Release Checklist

Use this release checklist before creating a buyer ZIP or publishing a new tag.

## Product boundary

Confirm the product is positioned as a deterministic repo preflight kit.

Confirm the product is not positioned as a security scanner.

Confirm the product is not positioned as a compliance scanner.

Confirm no copy claims that the tool makes code safe, correct, or ready for production use.

## Local verification

Run `make test` and confirm it passes.

Run `make demo` and confirm it produces Markdown, JSON, HTML, and SARIF reports.

Run `make package` and confirm it creates `release/ai-agent-repo-preflight-kit-v0.4.zip`.

Inspect the ZIP and confirm it excludes `.git`, caches, generated reports, and private planning notes.

## Buyer package

Confirm buyer quickstart exists.

Confirm local CLI setup guide exists.

Confirm GitHub Action setup guide exists.

Confirm limitations document exists.

Confirm sample report walkthrough exists.

Confirm buyer license exists.

## Listing readiness

Confirm landing-page copy exists.

Confirm Payhip listing copy exists.

Confirm Gumroad listing copy exists.

Confirm product title is consistent.

Confirm product promise is concrete and bounded.

Confirm price target is selected.

## Final acceptance

A buyer should be able to understand, run, and package the tool without contacting the seller.
