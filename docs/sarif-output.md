# SARIF Output

Repo Preflight can write a SARIF report when `--out-sarif` is provided.

```bash
python3 repo_preflight.py \
  --repo . \
  --profile public-export \
  --paranoid \
  --out-sarif REPO_PREFLIGHT_REPORT.sarif
```

SARIF output is intended for CI review surfaces, artifact upload, and code-scanning style review. It is another view of the scanner's deterministic release-discipline findings. It does not make security, compliance, vulnerability, or readiness claims.

## Format

- The SARIF payload uses version `2.1.0`.
- The scanner emits one SARIF run named `Repo Preflight Drift Scanner`.
- Each scanner finding becomes one SARIF result.
- Each finding `code` maps to the SARIF result `ruleId`.
- The SARIF rule list contains one rule per finding `code`; each rule uses the finding code for both `id` and `name`.
- Finding messages map to `result.message.text`.
- Finding paths map to `result.locations[].physicalLocation.artifactLocation.uri` after report path privacy options are applied.
- Finding line numbers map to `result.locations[].physicalLocation.region.startLine` when a line is available.

Use `ruleId` as the scanner finding-code field when reviewing SARIF results. For example, a scanner finding with code `missing_process_file` is emitted as a SARIF result with `ruleId: "missing_process_file"` and is grouped under the SARIF rule with `id: "missing_process_file"`.

## Level Mapping

Scanner finding levels map to SARIF levels as follows:

| Scanner level | SARIF level |
| --- | --- |
| `blocker` | `error` |
| `warning` | `warning` |
| `info` | `note` |

Use scanner levels and finding codes for release policy decisions. Use SARIF levels for CI review presentation.

## Privacy Behavior

SARIF is written from the same report findings used for Markdown, JSON, and HTML output after report privacy options are applied.

Result location paths reflect the selected path privacy behavior:

- `--path-mode relative` keeps relative report paths.
- `--path-mode basename` keeps only file basenames.
- `--path-mode hash` writes hashed path labels.
- `--paranoid` uses basename paths unless another `--path-mode` is explicitly selected.

Evidence snippets are not included in current SARIF results.

Privacy limits:

- SARIF result locations use the same post-privacy finding paths as the other report formats, but path privacy does not prove that an artifact is safe to publish.
- The SARIF run includes `originalUriBaseIds.ROOTPATH` derived from the scanned repository root. That can expose the local absolute repository path even when result locations use basename or hashed labels.
- Hashed path labels reduce readable path detail; they are not a security boundary or anonymization guarantee.
- Finding messages and rule IDs can still reveal project structure, workflow names, or release-process details.

If reports may leave a private workspace, use `--paranoid`, consider `--path-mode hash` when basename paths are still too revealing, and review the generated SARIF artifact before uploading or sharing it.

## Consumer Notes

- Treat SARIF as a review aid, not proof that the repository is secure, compliant, vulnerability-free, correct, or ready to ship.
- Treat `ruleId` values as the stable finding-code grouping surface.
- Expect new finding codes or rules to be additive over time.
- Pair SARIF with the JSON report when automation needs counts, decision status, baseline diffs, or full report metadata.
