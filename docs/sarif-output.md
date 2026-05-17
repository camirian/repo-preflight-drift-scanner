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
- Each finding `code` maps to the SARIF `ruleId`.
- SARIF rules are grouped by finding `code`.
- Finding messages map to SARIF result messages.
- Finding line numbers map to `region.startLine` when a line is available.

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

Evidence snippets are not included in current SARIF results. If reports may leave a private workspace, use `--paranoid` and review the generated SARIF artifact before uploading or sharing it.

## Consumer Notes

- Treat SARIF as a review aid, not proof that the repository is secure, compliant, vulnerability-free, correct, or ready to ship.
- Treat `ruleId` values as the stable finding-code grouping surface.
- Expect new finding codes or rules to be additive over time.
- Pair SARIF with the JSON report when automation needs counts, decision status, baseline diffs, or full report metadata.
