# Public History Risk

Status: release gate documentation, filename-only audit facts

This document records public-history risk that must be resolved before any additional public tag, public release, package upload, or paid/customer-facing artifact distribution.

## Known Filename-Only Fact

- `examples/sample-repo/credentials.json` appears in old Git history.
- This is a filename-only fact. No historical contents are asserted here.
- Do not inspect, print, restore, or quote historical contents from that path as part of routine release review.
- The repository is already public, so this is an existing public-history exposure rather than a pre-publication-only concern.

## Release Gate

Before any additional tag, release, upload, public promotion, or buyer package distribution, the owner must either:

- Accept the filename-only history risk in the release notes, including the reason it is acceptable for the intended distribution boundary.
- Remediate the history before additional distribution, then verify that public refs, tags, release artifacts, and uploaded packages no longer expose the filename.

If there is any chance the historical file contained real credentials, rotate or revoke the relevant credentials before additional distribution. Treat rotation/revocation as separate from Git history cleanup.

## Safe Filename-Only Audit Commands

These commands list paths and counts only. They do not print historical file contents.

```bash
git rev-list --count HEAD
git log --all --name-only --pretty=format: | sed '/^$/d' | sort -u
git log --all --name-only --pretty=format: | sed '/^$/d' | sort -u | rg '(^|/)credentials\.json$|(^|/)\.env($|\.)|\.pem$|\.key$|\.p12$'
git log --all --name-status --pretty=format:'commit %H' -- examples/sample-repo/credentials.json
```

Do not use commands that print blob contents, such as `git show <rev>:examples/sample-repo/credentials.json`, unless the owner explicitly authorizes a secret-handling review in a controlled environment.

## Remediation Options

For a not-yet-public repository, prefer publishing from a clean single-commit history that contains only the approved release boundary. For this already-public repository, remediation requires a deliberate cleanup plan for existing public refs and any downstream copies that are within owner control.

If preserving history is required, use a deliberate history-rewrite process such as `git filter-repo` or BFG, then verify every public ref, tag, release artifact, and package upload target after cleanup. Do not force-push, delete remote refs, or rewrite public history without explicit owner approval.

## Acceptance Evidence

Record the final owner decision in the relevant release notes before additional distribution:

- Accepted risk, with distribution boundary and rationale.
- Remediated history, with filename-only audit output after cleanup.
- Credentials rotated or revoked if the historical file may have contained real credentials.
