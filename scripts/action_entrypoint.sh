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
fail_on_blockers="${INPUT_FAIL_ON_BLOCKERS:-true}"

args=(
  --repo "$repo"
  --profile "$profile"
  --out-md "$out_md"
  --out-json "$out_json"
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
