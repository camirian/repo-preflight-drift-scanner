#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-v0.4}"
PACKAGE_NAME="ai-agent-repo-preflight-kit-${VERSION}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="${ROOT_DIR}/release"
STAGE_DIR="${RELEASE_DIR}/${PACKAGE_NAME}"
ZIP_PATH="${RELEASE_DIR}/${PACKAGE_NAME}.zip"

copy_if_present() {
  local src="$1"
  local dst="$2"
  if [[ -e "${ROOT_DIR}/${src}" ]]; then
    mkdir -p "$(dirname "${STAGE_DIR}/${dst}")"
    cp -R "${ROOT_DIR}/${src}" "${STAGE_DIR}/${dst}"
  fi
}

rm -rf "${STAGE_DIR}" "${ZIP_PATH}"
mkdir -p "${STAGE_DIR}"

copy_if_present README.md README.md
copy_if_present repo_preflight.py repo_preflight.py
copy_if_present action.yml action.yml
copy_if_present scripts/action_entrypoint.sh scripts/action_entrypoint.sh
copy_if_present configs configs
copy_if_present examples examples
copy_if_present docs/buyer docs/buyer
copy_if_present docs/release-checklist.md release-checklist.md
copy_if_present buyer-license.txt buyer-license.txt

cat > "${STAGE_DIR}/README-for-buyers.md" <<'EOF'
# AI Agent Repo Preflight Kit

Start here:

1. Read `docs/buyer/quickstart.md`.
2. Run the local demo against `examples/sample-repo`.
3. Run `repo_preflight.py` against your own repository.
4. For GitHub Actions, copy the workflow from `docs/buyer/github-action-setup.md`.

This package is a deterministic preflight kit for AI-assisted repositories. It is not a vulnerability scanner, compliance scanner, or replacement for human review.
EOF

find "${STAGE_DIR}" \
  -name '.git' -o \
  -name '__pycache__' -o \
  -name '.pytest_cache' -o \
  -name '.mypy_cache' -o \
  -name '.ruff_cache' -o \
  -name 'REPO_PREFLIGHT_REPORT.*' -o \
  -name 'REPORT.*' \
  | while read -r path; do rm -rf "$path"; done

python3 - <<PY
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
root = Path(r"${STAGE_DIR}")
zip_path = Path(r"${ZIP_PATH}")
with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            zf.write(path, path.relative_to(root.parent))
print(zip_path)
PY
