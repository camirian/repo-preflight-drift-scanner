# Mission/source-fidelity preflight

`repo_preflight.py` answers release-hygiene questions. `mission_preflight.py` answers a different question:

> Is user-visible implementation explicitly traceable to an originating mission/source/owner decision, or has the repository become internally consistent around an invented specification?

The check is deterministic and local. It does **not** use an LLM and does not semantically certify that a cited requirement is correct.

## Why this exists

AI-assisted projects can accumulate code, tests, ADRs, and documentation quickly. If the governing specification drifts, those artifacts can verify the wrong product extremely well. A green suite is verification, not validation.

The mission preflight therefore requires an explicit repository contract.

## Required repository files

```text
AGENTS.md
.mission/owner_constraints.json
.mission/features.json
```

`owner_constraints.json` must include at least:

```json
{
  "objective": "Preserve the user's intended job while modernizing implementation.",
  "default_invention_budget": 0,
  "derived_analysis_may_authorize_user_behavior": false,
  "canonical_agent_doctrine": "AGENTS.md",
  "tool_specific_instructions_may_override_agents": false,
  "product_roots": ["src"],
  "protected_mission_paths": ["AGENTS.md", ".mission"]
}
```

Optional arrays can customize evidence vocabulary:

- `allowed_change_classes`
- `primary_source_kinds`
- `user_confirmation_kinds`
- `owner_authorization_kinds`

## Feature trace format

```json
{
  "features": [
    {
      "id": "F-001",
      "class": "mirror",
      "user_visible": true,
      "changes_default_workflow": false,
      "source_evidence": [
        {"kind": "primary_artifact", "ref": "source-system/report/page-1"}
      ],
      "implementation_paths": ["src/report.py"]
    }
  ]
}
```

Supported default classes:

- `mirror`
- `defect_fix`
- `augmentation`
- `infrastructure`
- `research`

## Blocking rules

The preflight blocks when it sees:

- missing/invalid mission files;
- missing canonical agent doctrine;
- tool-specific instructions explicitly allowed to override the canonical doctrine;
- derived analysis allowed to authorize user-visible behavior;
- mirrored/fixed user behavior without primary source/user-confirmed evidence;
- derived-analysis-only user-visible behavior;
- zero-budget augmentation without owner authorization;
- default-workflow augmentation without user/domain confirmation;
- product code with no feature trace;
- mission-contract and product behavior changes in the same branch, when the Git base is available.

## Run

```bash
python3 mission_preflight.py --repo /path/to/repo
python3 verify_mission_preflight.py
```

Set `--base-ref` or `MISSION_BASE_REF` when the comparison base is not `origin/main`.

## What this proves

It proves that the repository has explicit mission/source governance and that its declared product files are structurally traceable under that contract.

It **does not** prove that the cited source actually means what the implementation claims. That remains a validation task for the owner/user/domain expert and primary artifact oracle.
