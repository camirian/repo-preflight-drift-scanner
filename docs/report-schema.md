# JSON Report Schema

Repo Preflight writes JSON reports for automation, baselines, and downstream review tools.

The report is a deterministic preflight output for release-discipline signals. It is not a security scanner, compliance scanner, vulnerability scanner, or replacement for human review.

## Top-level object

```json
{
  "schema_version": "1.0",
  "repo": ".",
  "profile": "public-export",
  "decision": "READY",
  "counts": {
    "blocker": 0,
    "warning": 0,
    "info": 0
  },
  "findings": [],
  "baseline_diff": {
    "new": 0,
    "resolved": 0,
    "new_findings": [],
    "resolved_findings": []
  }
}
```

Fields:

- `schema_version`: string. JSON report schema version for automation consumers.
- `repo`: string. The repository path passed to `--repo`.
- `profile`: string. The selected profile, such as `strict`, `docs`, or `public-export`.
- `decision`: string. `READY` when no blocker findings are present, otherwise `BLOCKED`.
- `counts`: object. Finding totals by level.
- `findings`: array. The current finding list after report privacy options are applied.
- `baseline_diff`: object, optional. Present only when `--baseline-json` is supplied.

## Counts

```json
{
  "blocker": 0,
  "warning": 0,
  "info": 0
}
```

Fields:

- `blocker`: integer. Number of blocker findings.
- `warning`: integer. Number of warning findings.
- `info`: integer. Number of info findings.

## Finding

```json
{
  "level": "blocker",
  "code": "missing_process_file",
  "path": ".",
  "message": "Missing process file: README",
  "line": null,
  "evidence": null
}
```

Fields:

- `level`: string. One of `blocker`, `warning`, or `info`.
- `code`: string. Stable finding code for automation and grouping.
- `path`: string. Report path after `--path-mode` or `--paranoid` handling.
- `message`: string. Human-readable finding message.
- `line`: integer or null, optional for consumers. Present when a finding maps to a specific line.
- `evidence`: string or null, optional for consumers. Evidence text may be omitted under privacy options.

Privacy behavior:

- `--paranoid` uses basename-only paths and omits evidence snippets.
- `--no-evidence` omits evidence snippets.
- `--max-evidence-chars` truncates evidence snippets.
- `--redact-pattern` replaces matching evidence text with `[REDACTED]`.
- `--path-mode basename|hash` reduces path detail before the JSON report is written.

When evidence is omitted by privacy options, consumers should treat missing, null, or empty evidence as equivalent to "not included in this report."

## Baseline diff

`baseline_diff` is present only when the run includes `--baseline-json`.

```json
{
  "new": 1,
  "resolved": 2,
  "new_findings": [],
  "resolved_findings": []
}
```

Fields:

- `new`: integer. Number of findings present in the current report but absent from the baseline.
- `resolved`: integer. Number of findings present in the baseline but absent from the current report.
- `new_findings`: array of finding objects. Findings counted by `new`.
- `resolved_findings`: array of finding objects. Findings counted by `resolved`.

Baseline matching uses finding content after report privacy options are applied. If privacy settings differ between the baseline and current run, paths or evidence may change enough to affect the diff.

## Consumer notes

- Treat unknown future fields as additive.
- Use `schema_version` before relying on report structure in automation.
- Do not treat `READY` as proof that a repository is secure, compliant, correct, or ready to ship.
- Use `decision` for coarse gating and `counts` plus `findings[*].code` for reporting or dashboards.
