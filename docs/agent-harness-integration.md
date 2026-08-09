# Agent Harness Integration

**Status:** integration guidance; scanner behavior remains deterministic  
**Baseline:** 2026-08-09

## Purpose

`repo-preflight-drift-scanner` should be easy to invoke from modern coding-agent harnesses without becoming dependent on any one model, provider, IDE, or runtime.

The scanner remains a deterministic CLI/GitHub Action. Agent runtimes such as Codex, OpenCode, goose, Claude Code, Cline, or a custom Workbench may **invoke** it, parse its machine-readable results, and surface its findings. They must not reinterpret a blocked result as a pass.

## Architectural role

```text
agent / harness
     |
     | shell/tool/MCP wrapper
     v
repo-preflight-drift-scanner
     |
     +-> Markdown report
     +-> JSON report
     +-> HTML report
     +-> SARIF
     +-> process exit code
     |
     v
agent may explain/remediate findings
     |
     v
scanner reruns independently
```

The LLM is **not** the grader.

## Why this boundary matters

Agent systems are increasingly adding:

- `AGENTS.md` repository instructions;
- Agent Skills;
- MCP tools;
- autonomous loops;
- browser/computer use;
- parallel worktrees/subagents;
- model/provider routing;
- automated PR/release workflows.

Those features increase throughput, but they also increase the chance that stale process files, risky claims, generated artifacts, public/private drift, or missing AI-readiness documentation survive until release.

This scanner is valuable because its decision is inspectable and repeatable regardless of which model produced the repository change.

## Supported invocation pattern

From the target repository, call the scanner using the repository's chosen installation method. The canonical local CLI shape remains:

```bash
python3 repo_preflight.py --repo . --profile strict
```

When running the scanner from a separate checkout/package, point `--repo` at the target repository explicitly.

Do not hardcode a private absolute path in reusable agent instructions.

## Profile selection for agents

### `strict`

Use before:

- merge readiness;
- handoff;
- demo;
- ordinary release review;
- an agent claims a bounded implementation task is complete.

### `public-export`

Use before:

- making a repository public;
- publishing a package/template/skill;
- sharing generated reports outside a private workspace;
- producing public demonstration artifacts.

Prefer `--paranoid` for external/public reports when evidence snippets or detailed paths are unnecessary.

### `dora-ai-readiness`

Use when assessing whether an AI-assisted repository **documents** the expected capability surfaces. It is not a replacement for release/public-surface checks and does not certify DORA maturity or production readiness.

### `docs`

Use for documentation/template-heavy repositories when strict-mode findings would be predictably noisy and the docs profile matches the intended question.

## Agent-facing output contract

A harness integration should preserve at least:

- selected profile;
- scanner version/commit when available;
- target repository identity/path in a privacy-appropriate form;
- exit code;
- decision/blocker count;
- warning/info counts;
- finding IDs;
- finding severity;
- path/evidence subject to configured privacy mode;
- report artifact paths;
- whether a baseline comparison was used.

Prefer JSON/SARIF for machine consumption. Markdown/HTML are human-facing views.

## Fail-closed integration rules

An agent or harness must **not**:

- change a scanner blocker into a warning because the model disagrees;
- suppress a finding without an explicit scanner-supported baseline/configuration rule;
- infer `PASS` because only part of the scanner ran;
- substitute an LLM review when the deterministic scanner is available and required;
- delete failed reports before rerunning;
- rewrite the scanner's decision in a UI without preserving the original machine result.

If the scanner itself fails to run, represent that state as unavailable/error, not clean.

## Recommended skill/tool layering

### Skill

A portable Agent Skill can teach an agent **when** to run the scanner, how to choose a profile, and how to interpret results.

### Tool

The deterministic CLI remains the actual checker.

### Loop

A higher-level repair loop may use:

```text
preflight scan
   -> blockers?
       yes -> bounded remediation
             -> rerun preflight
       no  -> DONE
   -> budget exhausted / product decision -> NEEDS_HUMAN_DECISION
```

The loop must preserve the original findings and set a repair budget. Do not allow the agent to tune scanner rules merely to force a pass.

## Example bounded release-repair loop

1. Run `strict` profile.
2. Parse deterministic findings.
3. Classify each as:
   - directly repairable within current task scope;
   - requires owner/product decision;
   - expected legacy finding covered by an existing approved baseline;
   - tool/configuration error.
4. Repair only authorized, in-scope findings.
5. Run relevant repository tests/checks.
6. Rerun scanner.
7. Stop when:
   - scanner has no required blockers -> `DONE`;
   - unresolved blocker needs owner judgment -> `NEEDS_HUMAN_DECISION`;
   - retry budget expires -> `BUDGET_EXHAUSTED`;
   - scanner cannot execute reliably -> `BLOCKED`.

## OpenCode integration

OpenCode can execute shell/custom tools and supports portable Agent Skills. A minimal integration can therefore use:

- a `.agents/skills` skill explaining profile/decision behavior;
- shell execution of the scanner;
- JSON output for structured interpretation;
- normal OpenCode permission rules for command execution.

No OpenCode plugin or fork is required for the first useful integration.

If a future Workbench wants richer display, use a thin tool wrapper that returns the scanner's JSON result without altering semantics.

## goose integration

goose can invoke local tools/extensions and supports reusable recipes/skills. The same principle applies:

- keep scanner semantics in this repository;
- put orchestration/UX in the harness;
- pass machine-readable results back to the agent/operator;
- preserve blocked/unavailable states.

Do not maintain separate goose-specific scanner logic unless a measured protocol incompatibility requires a small adapter.

## Codex/other coding agents

Any agent with bounded shell access can invoke the deterministic CLI. Repository-level `AGENTS.md` can state that the scanner is a required gate for a particular release/public workflow; a portable skill can hold reusable usage guidance.

Do not put this entire integration document into every repository's `AGENTS.md`. Keep project maps concise and load the detailed integration only when relevant.

## Browser-capable agent workflows

Browser automation can help validate a running product, but it does not replace this scanner.

Use separate evidence:

```text
repo preflight      -> repository/process/public-surface evidence
unit/integration CI -> code behavior evidence
browser/Playwright  -> user-flow/runtime UI evidence
human review        -> product/publication judgment
```

A harness should display these evidence classes separately rather than collapsing them into one “verified” badge.

## Multi-agent workflows

For parallel agents/worktrees:

- run focused checks inside each lane as appropriate;
- run final preflight on the integration/release candidate, not merely on each isolated branch;
- avoid agents modifying scanner configuration concurrently with the work being judged unless that config change is itself the explicit task;
- independent reviewers should inspect scanner findings but not silently override them.

## Integration with `ai-builder-verification-kit`

The two tools are complementary:

- `repo-preflight-drift-scanner` inspects an actual repository/release surface for deterministic drift findings;
- `ai-builder-verification-kit` evaluates structured project descriptions and verification/readiness evidence under its own deterministic decision rules.

A Workbench may invoke both and present both outputs. Do not merge their decisions into a new opaque LLM-generated score.

## Integration with `ai-scaffolding-engineering`

`ai-scaffolding-engineering` can use this scanner in controlled experiments involving:

- agent-ready repository structure;
- public-release discipline;
- accumulated process drift;
- prompt vs. skill vs. deterministic-tool comparisons;
- loop repair behavior.

Course claims should report the scanner version/config and preserve failed runs.

## Public distribution opportunity

This scanner is already a public deterministic artifact and can be part of a broader open agent-engineering ecosystem without being absorbed into a monolithic Workbench.

High-value public additions can include:

- a portable Agent Skill;
- concise install/use recipes for major harnesses;
- synthetic examples;
- stable JSON schema documentation;
- versioned sample loop specifications;
- compatibility smoke tests.

Avoid marketing it as an autonomous safety/compliance agent. Its strength is that it does a narrow, inspectable job consistently.

## Security/privacy guidance for agent invocation

- Prefer least-privilege read access when scanning.
- Do not expose unrelated home directories or credentials merely so an agent can run preflight.
- Use `--paranoid`, `--no-evidence`, redaction patterns, or reduced path detail before reports leave a private workspace.
- Treat report artifacts as potentially sensitive until reviewed.
- Never allow a browser-enabled or network-enabled agent to upload scanner reports automatically without explicit authorization.

## Future compatibility tests

A small public compatibility matrix could eventually record:

| Client/harness | Skill discovered | CLI invoked | JSON parsed | Blocker preserved | Tested version/date |
|---|---|---|---|---|---|
| Codex | TBD | TBD | TBD | TBD | TBD |
| OpenCode | TBD | TBD | TBD | TBD | TBD |
| goose | TBD | TBD | TBD | TBD | TBD |
| Claude Code | TBD | TBD | TBD | TBD | TBD |

Do not fill this table from documentation claims alone. Record only observed runs.

## Core principle

> The agent may propose the fix. The deterministic tool decides whether its own checks now pass. The human retains release/publication authority.
