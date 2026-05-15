# Release Checklist

Use this checklist before creating a buyer ZIP or publishing a new tag.

## Product boundary

- [ ] The product is positioned as a deterministic repo preflight kit.
- [ ] The product is not positioned as a security scanner.
- [ ] The product is not positioned as a compliance scanner.
- [ ] No copy claims that the tool guarantees safe, correct, or production-ready code.

## Local verification

- [ ] `make test` passes.
- [ ] `make demo` produces Markdown, JSON, HTML, and SARIF reports.
- [ ] `make package` creates `release/ai-agent-repo-preflight-kit-v0.4.zip`.
- [ ] The ZIP excludes `.git`, caches, generated reports, and private planning notes.

## Buyer package

- [ ] Buyer quickstart exists.
- [ ] Local CLI setup guide exists.
- [ ] GitHub Action setup guide exists.
- [ ] Limitations document exists.
- [ ] Sample report walkthrough exists.
- [ ] Buyer license exists.

## Listing readiness

- [ ] Landing-page copy exists.
- [ ] Payhip listing copy exists.
- [ ] Gumroad listing copy exists.
- [ ] Product title is consistent.
- [ ] Product promise is concrete and bounded.
- [ ] Price target is selected.

## Final acceptance

A buyer should be able to understand, run, and package the tool without contacting the seller.
