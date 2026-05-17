# Rule Packs

Rule packs are JSON config files passed with `--config`. They let a team add project-specific release-discipline checks without changing scanner code.

Use the profile that matches the scan intent, then add the rule pack:

- `strict`: normal release-discipline checks before merge, demo, handoff, or release artifact.
- `docs`: low-noise documentation scans where templates, examples, unchecked boxes, and old reports would otherwise distract from doc review.
- `public-export`: public-publication checks before publishing a repository, package, Action, template, or downloadable product.

```bash
python3 repo_preflight.py --repo . --profile strict --config configs/team-policy.json
```

`--config` may be repeated. Files are loaded in the order provided.

```bash
python3 repo_preflight.py \
  --repo . \
  --profile public-export \
  --paranoid \
  --config configs/founder-strict.json \
  --config configs/team-policy.json
```

## Merge behavior

List keys are additive with the built-in defaults. Adding `risky_claims`, `drift_markers`, `secret_filenames`, `generated_dirs`, `excluded_dirs`, or `excluded_files` extends the default set; it does not replace it.

`required_process_files` is merged by label. A label present in a rule pack overrides that label's candidate paths. Labels not mentioned in the rule pack keep their default behavior.

Supported top-level keys:

- `risky_claims`
- `drift_markers`
- `secret_filenames`
- `generated_dirs`
- `excluded_dirs`
- `excluded_files`
- `required_process_files`

Unknown keys are rejected.

## Compact example

```json
{
  "required_process_files": {
    "VERIFICATION_PLAN": ["VERIFICATION_PLAN.md", "docs/verification.md"],
    "OWNERSHIP": ["CODEOWNERS", ".github/CODEOWNERS"]
  },
  "risky_claims": ["enterprise ready", "zero risk"],
  "drift_markers": ["temporary workaround"],
  "secret_filenames": [".npmrc"],
  "generated_dirs": ["coverage", "reports"],
  "excluded_dirs": [".venv"],
  "excluded_files": ["package-lock.json"]
}
```

In this example, the `VERIFICATION_PLAN` label uses the listed candidates instead of the default candidates. The new `OWNERSHIP` label is also required. The list entries are added to the defaults.

## Verification command

Use a local scan to confirm a rule pack parses and produces the expected findings:

```bash
python3 repo_preflight.py --repo . --profile strict --config configs/team-policy.json
```

For a documentation-heavy repo or docs-only package area, use the low-noise docs profile:

```bash
python3 repo_preflight.py --repo . --profile docs --config configs/team-policy.json
```

For a public-export check, keep the normal privacy controls:

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid --config configs/team-policy.json
```

In GitHub Actions, pass the same profile intent and one rule-pack path through `config`:

```yaml
with:
  repo: "."
  profile: strict
  config: configs/team-policy.json
```

```yaml
with:
  repo: "."
  profile: docs
  config: configs/team-policy.json
```

```yaml
with:
  repo: "."
  profile: public-export
  paranoid: true
  config: configs/team-policy.json
```

## Boundary

Rule packs tune deterministic preflight checks. They are not a security policy, compliance policy, vulnerability scanner, guarantee of readiness, or replacement for human review.
