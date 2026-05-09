# Verification Plan

Status: draft

## Commands

```bash
python3 verify_scanner.py
```

Expected:

```text
Repo preflight scanner verification passed.
```

## Acceptance Criteria

- Markdown report exists.
- JSON report exists.
- Scanner exits non-zero for synthetic blockers.
- Secret-bearing filename is detected.
- Secret file contents are not printed.
- Unchecked checklist item is detected.
- Risky public claim is detected.
- Cache directory is detected.
- Strict self-scan of the scanner product folder returns READY.
- Docs-profile scan of the opportunity-board area returns READY with low noise.
- JSON reports include profile, decision, counts, and findings.
- Composite GitHub Action metadata exists.
- Action shell entrypoint runs locally in report-only mode and writes Markdown/JSON reports.
