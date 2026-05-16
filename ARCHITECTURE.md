# Architecture

Status: current architecture summary and guardrails

## System Shape

```text
repo_preflight.py
  -> scans local repository files
  -> applies built-in profiles and optional JSON rule packs
  -> writes Markdown, JSON, optional HTML, optional SARIF
  -> optionally emits GitHub workflow annotations

action.yml
  -> composite GitHub Action metadata
  -> invokes scripts/action_entrypoint.sh
  -> calls the same repo_preflight.py implementation
```

There is one scanner implementation. The GitHub Action is a wrapper, not a second scan engine.

## Components

- `repo_preflight.py`: dependency-free CLI, rule definitions, scan traversal, finding generation, report rendering, baseline diffing, privacy controls, and exit decision.
- `scripts/action_entrypoint.sh`: translates Action inputs into CLI flags and handles report-only versus fail-on-blockers behavior.
- `action.yml`: public Action interface, inputs, outputs, metadata, and composite run step.
- `verify_scanner.py`: executable regression suite for CLI behavior, Action entrypoint behavior, report outputs, baseline diffing, privacy mode, public-export self-scan, docs profile, and Python compilation.
- `configs/`: example rule packs for founder/team policy tuning.
- `examples/sample-repo/`: synthetic blocked fixture used for demos and verification.
- `docs/buyer/`: buyer-facing setup and usage documentation included in the v0.4 package.
- `scripts/package_release.sh`: creates the v0.4 buyer artifact boundary.

## Data Flow

1. User provides a repository path and scan options.
2. Scanner walks allowed text files and selected path metadata.
3. Scanner skips default excluded directories, generated reports, caches, and lockfiles unless explicitly included.
4. Findings are normalized into level, code, path, message, and optional evidence.
5. Reports are rendered from the same finding set.
6. Exit status is derived from blocker findings unless Action report-only mode suppresses failure.

## Runtime Constraints

- Python standard library only.
- No network calls.
- Read-only scan of the target repo.
- Deterministic output for the same inputs, files, and configuration.
- Secret-bearing filenames may be flagged, but secret contents must not be read or printed.

## Profile Model

- `strict`: default release-oriented profile.
- `docs`: low-noise profile for documentation-heavy scans.
- `public-export`: conservative profile for public repos, packages, and upload readiness.

Profiles select check families. Rule packs extend or override lists such as risky claims, drift markers, secret-bearing filenames, generated directories, and exclusions.

## Reporting Model

- Markdown: human review and local handoff.
- JSON: automation, baseline diffing, and verifier assertions.
- HTML: shareable local report.
- SARIF: code scanning compatible output for CI surfaces.
- GitHub annotations: workflow log visibility when enabled.

## Key Invariants

- CLI and Action must produce the same finding semantics.
- Generated reports are outputs and should not become required source files.
- Buyer package must be verified as an extracted artifact, not only as a source tree.
- New checks should be deterministic, explainable, and covered by verifier assertions or fixtures.
