# Source Boundary Policy

This repository separates committed source from generated output. `AGENTS.md`
requires that generated reports, release ZIPs, and scratch outputs stay out of
git source unless they are deliberate release artifacts.

## What the policy enforces

A path tracked by git is treated as a disallowed artifact when either:

- any path segment is a generated, cache, or release directory
  (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `node_modules`,
  `dist`, `build`, `release`); or
- the file is a generated report — its basename is `report` or ends with
  `_report` and its suffix is `.md`, `.json`, `.html`, or `.sarif`.

Everything else (the CLI, the verifier, docs, configs, examples, the JSON
schema) is allowed source.

The synthetic fixture tree under `examples/sample-repo` is exempt: it
intentionally ships generated-artifact paths (such as a `dist/` file) so the
demo scan can flag them for users.

## How it is checked

`verify_scanner.py` exposes a pure classifier, `is_disallowed_tracked_artifact`,
and a `verify_source_boundary` check wired into the main verification run. The
check does two things:

1. Asserts the classifier flags a set of synthetic disallowed paths and allows a
   set of known source paths, so the guard demonstrably fails on a bad input
   rather than passing only because the tree happens to be clean.
2. Runs `git ls-files` and fails if any real tracked path is classified as a
   disallowed artifact.

Run it with `python3 verify_scanner.py`.

## Why this is not redundant with `.gitignore`

`.gitignore` prevents accidental staging, but it does not stop a force-add
(`git add -f`) and it only covers patterns already listed. The boundary check
runs against the actual tracked file set, so it also catches force-added output
and artifact types not yet present in `.gitignore`. The two layers reinforce
each other: `.gitignore` is the default guard, and this check is the asserted
backstop.

## Scope and follow-up

This policy covers git-tracked source only. Reconciling the same boundary
against extracted release-package contents is a separate follow-up; the release
package already has its own manifest boundary check in `verify_scanner.py`.
