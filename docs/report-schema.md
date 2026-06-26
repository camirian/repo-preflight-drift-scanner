# JSON Report Schema

Repo Preflight writes JSON reports for automation, baselines, and downstream review tools.

The report is a deterministic preflight output for release-discipline signals. It is not a security scanner, compliance scanner, vulnerability scanner, or replacement for human review.

## Machine-readable schema artifact

The machine-readable JSON Schema artifact for report consumers is expected at:

```text
docs/report.schema.json
```

Use that artifact as the validation contract for reports produced with `--out-json`. This page explains the same contract in human-readable form and describes the compatibility boundaries that automation should rely on.

Recommended automation flow:

1. Generate a JSON report with `--out-json`.
2. Read `schema_version` from the report before applying strict parsing logic.
3. Validate the report against `docs/report.schema.json` from the same released kit version when the artifact is available.
4. Gate on `decision` for coarse pass/fail behavior.
5. Use `counts` and `findings[*].code` for dashboards, trend reporting, routing, and baseline workflows.

Consumers should vendor or pin the schema artifact with the scanner version they run. Do not fetch an unpinned schema from a different branch or release and assume it describes the report you just produced.

## Compatibility boundaries

For reports with the same major `schema_version`, automation may assume:

- Required top-level fields documented here keep their meaning.
- `decision` remains the coarse automation gate and is `READY` or `BLOCKED`.
- `counts.blocker`, `counts.warning`, and `counts.info` remain integer finding totals.
- `findings` remains an array of finding objects.
- `findings[*].level` remains one of `blocker`, `warning`, or `info`.
- `findings[*].code` remains the preferred stable grouping key for automation.

Consumers must allow:

- Additional top-level fields.
- Additional fields inside nested objects.
- New finding `code` values.
- New profile names.
- Optional privacy-sensitive fields such as `line` or `evidence` to be missing, null, empty, truncated, redacted, or path-reduced depending on CLI options.

A future major `schema_version` may change required fields, field meanings, enum values, or baseline matching behavior. Treat that as a contract break and require an explicit consumer update.

This schema does not define the Markdown, HTML, or SARIF report formats. SARIF has its own compatibility surface; see [SARIF output](sarif-output.md).

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
- `profile`: string. The selected profile, such as `strict`, `docs`, `dora-ai-readiness`, or `public-export`.
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

## DORA AI readiness findings

When `profile` is `dora-ai-readiness`, the report uses the same top-level schema and finding shape as other profiles.

The profile emits one DORA-specific finding for each capability:

- Evidence found: `level` is `info`, `code` is `dora_<capability>_evidence`, and the finding points to the first detected evidence location.
- Evidence missing: `level` is `blocker`, `code` is `missing_dora_<capability>`, and the message describes the missing documentation evidence.

Current capability code names are `ai_stance`, `data_boundary`, `ai_accessible_context`, `version_control`, `small_batches`, `user_focus`, and `internal_platform`.

For this profile, `decision: "READY"` means no DORA documentation-evidence blocker was emitted. It is not a certification of DORA maturity, DORA metric performance, security, compliance, correctness, model safety, or production readiness.

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
