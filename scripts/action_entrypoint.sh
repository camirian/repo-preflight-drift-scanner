#!/usr/bin/env bash
set +e

repo="${INPUT_REPO:-.}"
profile="${INPUT_PROFILE:-strict}"
out_md="${INPUT_OUT_MD:-REPO_PREFLIGHT_REPORT.md}"
out_json="${INPUT_OUT_JSON:-REPO_PREFLIGHT_REPORT.json}"
out_html="${INPUT_OUT_HTML:-}"
out_sarif="${INPUT_OUT_SARIF:-}"
baseline_json="${INPUT_BASELINE_JSON:-}"
config="${INPUT_CONFIG:-}"
include_fixtures="${INPUT_INCLUDE_FIXTURES:-false}"
github_annotations="${INPUT_GITHUB_ANNOTATIONS:-true}"
paranoid="${INPUT_PARANOID:-false}"
no_evidence="${INPUT_NO_EVIDENCE:-false}"
max_evidence_chars="${INPUT_MAX_EVIDENCE_CHARS:-180}"
path_mode="${INPUT_PATH_MODE:-relative}"
redact_pattern="${INPUT_REDACT_PATTERN:-}"
fail_on_blockers="${INPUT_FAIL_ON_BLOCKERS:-true}"

args=(
  --repo "$repo"
  --profile "$profile"
  --out-md "$out_md"
  --out-json "$out_json"
  --max-evidence-chars "$max_evidence_chars"
  --path-mode "$path_mode"
)

if [ -n "$out_html" ]; then
  args+=(--out-html "$out_html")
fi

if [ -n "$out_sarif" ]; then
  args+=(--out-sarif "$out_sarif")
fi

if [ -n "$baseline_json" ]; then
  args+=(--baseline-json "$baseline_json")
fi

if [ -n "$config" ]; then
  args+=(--config "$config")
fi

if [ "$include_fixtures" = "true" ]; then
  args+=(--include-fixtures)
fi

if [ "$github_annotations" = "true" ]; then
  args+=(--github-annotations)
fi

if [ "$paranoid" = "true" ]; then
  args+=(--paranoid)
fi

if [ "$no_evidence" = "true" ]; then
  args+=(--no-evidence)
fi

if [ -n "$redact_pattern" ]; then
  args+=(--redact-pattern "$redact_pattern")
fi

python3 "$GITHUB_ACTION_PATH/repo_preflight.py" "${args[@]}"
status=$?

echo "Markdown report: $out_md"
echo "JSON report: $out_json"
if [ -n "$out_html" ]; then
  echo "HTML report: $out_html"
fi
if [ -n "$out_sarif" ]; then
  echo "SARIF report: $out_sarif"
fi

if [ "$status" -ne 0 ] && [ "$fail_on_blockers" = "true" ]; then
  exit "$status"
fi

exit 0
