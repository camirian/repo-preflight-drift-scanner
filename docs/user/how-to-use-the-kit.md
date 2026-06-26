# How To Use The Kit

This kit is for developers and founders who use AI coding agents and need a small, repeatable release check before publishing work.

## Recommended workflow

```text
1. Build with your AI coding agent.
2. Run your normal tests and project checks.
3. Run Repo Preflight.
4. Read the blocker list.
5. Fix or consciously accept each finding.
6. Re-run before merge, demo, or public export.
```

## Profiles

List the available local CLI profiles without running a scan:

```bash
python3 repo_preflight.py --list-profiles
```

### strict

Use `strict` for normal release-discipline checks before a merge, demo, handoff, or internal release artifact. It checks process files, unchecked release gates, risky public claims, generated artifacts, and AI/process drift markers. It does not add the extra public-publication checks from `public-export`.

```bash
python3 repo_preflight.py --repo . --profile strict
```

```yaml
with:
  repo: "."
  profile: strict
```

### docs

Use `docs` when scanning template-heavy documentation, sample reports, or user instructions where unchecked boxes, sample claims, and old generated artifacts would create too much noise. It is a low-noise documentation pass, not a release gate for code or public artifacts.

```bash
python3 repo_preflight.py --repo . --profile docs
```

```yaml
with:
  repo: "."
  profile: docs
```

### dora-ai-readiness

Use `dora-ai-readiness` when a team wants to know whether an AI-assisted repo has documented evidence for the seven DORA AI capability surfaces: AI stance, data boundary, AI-accessible context, version-control and rollback path, small-batch delivery, user or user focus, and internal-platform verification.

```bash
python3 repo_preflight.py --repo . --profile dora-ai-readiness --out-md dora-ai-readiness.md
```

```bash
python3 repo_preflight.py \
  --repo . \
  --profile dora-ai-readiness \
  --out-md dora-ai-readiness.md \
  --out-json dora-ai-readiness.json \
  --out-sarif dora-ai-readiness.sarif
```

```yaml
with:
  repo: "."
  profile: dora-ai-readiness
  out-md: dora-ai-readiness.md
  out-json: dora-ai-readiness.json
```

This profile checks for explicit documentation evidence. It emits one DORA finding per capability: an info finding when evidence is found, or a blocker when evidence is missing. It does not certify DORA maturity, DORA metric performance, security, compliance, governance approval, model safety, production readiness, public-export safety, or secret hygiene.

See the profile guide in [../dora-ai-readiness-profile.md](../dora-ai-readiness-profile.md) for the SDLC boundary and evidence-term rules.

### fieldheld-portfolio

Use `fieldheld-portfolio` for AI-assisted repositories that need documentation-evidence checks. It combines AI capability documentation-evidence checks (AI stance, data boundary, rollback path, small-batch delivery, user or buyer focus, and verification evidence) with standard release-discipline blockers (missing process files, unchecked gates, risky public claims, secret-bearing filenames, and generated artifacts).

```bash
python3 repo_preflight.py \
  --repo . \
  --profile fieldheld-portfolio \
  --config configs/fieldheld-portfolio.json
```

```yaml
with:
  repo: "."
  profile: fieldheld-portfolio
  config: configs/fieldheld-portfolio.json
```

This profile is documentation-evidence and release-discipline only. It does not certify or guarantee DORA maturity, compliance, security, or production readiness.

### public-export

Use `public-export` before publishing a repository, package, GitHub Action, template, or downloadable product. It includes the `strict` checks and adds public-export hygiene checks for private planning paths, tracked report outputs, tracked secret-bearing filenames, high-confidence secret literals, and sensitive public-export terms. Use `--paranoid` or `paranoid: true` when the report may leave a private workspace.

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid
```

```yaml
with:
  repo: "."
  profile: public-export
  paranoid: true
```

Profile selection is about scan intent, not proof of safety. A clean report only means this deterministic preflight did not find the specific release-discipline problems it checks for.

## Report outputs

- Markdown: human-readable fix list.
- JSON: machine-readable results for automation or baselines. See [JSON report schema](../report-schema.md) for the `docs/report.schema.json` artifact path, validation flow, and compatibility boundaries.
- HTML: shareable local report.
- SARIF: code-scanning compatible format for CI review surfaces. See [SARIF output](../sarif-output.md).

## Rule packs

Use JSON rule packs with `--config` to add team-specific terms, generated directories, exclusions, and required process-file labels. See [rule packs](../rule-packs.md) for supported keys and merge behavior.

## Baseline diff

After a known report is saved, compare a future run against it:

```bash
python3 repo_preflight.py \
  --repo . \
  --baseline-json previous/REPO_PREFLIGHT_REPORT.json \
  --out-json REPO_PREFLIGHT_REPORT.json
```

This helps separate new drift from already-known drift.

For a legacy repository with accepted existing blockers, use the baseline-aware gate to fail only when a blocker is new versus the saved baseline:

```bash
python3 repo_preflight.py \
  --repo . \
  --baseline-json previous/REPO_PREFLIGHT_REPORT.json \
  --fail-on-new-blockers-only
```

This does not change the report `decision`; it only changes the CLI exit gate. Keep baseline privacy options consistent between runs, because path and evidence changes can affect finding matching.

## Privacy mode

For reports that may leave your machine or private repository:

```bash
python3 repo_preflight.py --repo . --paranoid --path-mode basename --no-evidence
```

Use the redaction option when a term should never appear in evidence snippets.

## user rule

Do not treat this kit as proof that a repository is safe. Treat it as a fast, deterministic preflight for obvious release-discipline failures.
