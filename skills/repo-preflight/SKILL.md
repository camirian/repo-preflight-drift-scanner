---
name: repo-preflight
description: Run deterministic repository preflight checks before merge, handoff, demo, release, or public export. Use when asked to check repo drift, release blockers, risky public claims, publication boundaries, or documented AI-readiness. The scanner result must remain authoritative for its own findings.
license: See repository license
compatibility: Requires Python 3.10-3.13 and access to the repo-preflight-drift-scanner CLI/package. Publishing, configuration weakening, or external upload requires separate approval.
---

# Repo Preflight

## Objective

Use `repo-preflight-drift-scanner` as a deterministic gate. The model may explain findings and propose repairs; it must not rewrite the scanner's decision.

## Choose the profile

Use the target repository's own rules first. If no repository-specific profile is mandated:

- `strict` — ordinary merge/handoff/demo/release readiness;
- `public-export` — before public repository/package/template/report export; prefer `--paranoid` when reports may leave a private workspace;
- `dora-ai-readiness` — documented AI-assisted-development capability evidence only;
- `docs` — documentation/template-heavy surfaces when that profile matches the question.

Do not use `dora-ai-readiness` as a substitute for `strict` or `public-export` when release/public-surface checks are required.

## Run

Invoke the installed/scoped scanner against the target repo. A canonical checkout invocation is:

```bash
python3 repo_preflight.py --repo . --profile strict
```

If the scanner lives elsewhere, use the repository's documented install/entrypoint and point `--repo` at the target. Do not hardcode a private absolute path in reusable instructions.

Prefer JSON output when another agent/loop needs to consume findings programmatically.

## Interpret results

Preserve:

- profile;
- exit status;
- decision;
- blocker/warning/info counts;
- finding IDs/severity;
- report paths;
- any configured baseline/privacy mode.

If the scanner cannot run, report it as unavailable/error. Do not infer a clean result.

## Repair behavior

If the user authorized fixes:

1. classify findings by scope and required authority;
2. fix only findings within the authorized task;
3. do not weaken rules/config merely to force a pass;
4. run repository-specific focused/full checks required by `AGENTS.md`;
5. rerun the scanner;
6. preserve unresolved findings and explain them.

If a finding requires product judgment, publication authority, permission expansion, or a policy exception, stop for the required human decision.

## Evidence boundary

Do not collapse scanner output with other evidence classes. Keep separate:

- scanner/preflight findings;
- unit/integration/CI results;
- browser/user-flow evidence;
- independent review;
- human release approval.

## No-publish boundary

This skill never authorizes:

- release/tag creation;
- deployment;
- repository visibility changes;
- uploading reports externally;
- public posting;
- changing scanner policy to make a release pass.

Those require a separate explicit action under the target repository's rules.

## Completion

The task is complete when the current scanner result is recorded accurately, authorized repairs have been rechecked, and every remaining blocker/unknown/human decision is explicit.
