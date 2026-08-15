#!/usr/bin/env python3
"""Adversarial self-test for mission_preflight.py."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from mission_preflight import MissionError, validate


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def base_constraints() -> dict:
    return {
        "objective": "Preserve the user's intended job while modernizing implementation.",
        "default_invention_budget": 0,
        "derived_analysis_may_authorize_user_behavior": False,
        "canonical_agent_doctrine": "AGENTS.md",
        "tool_specific_instructions_may_override_agents": False,
        "product_roots": ["src"],
        "protected_mission_paths": ["AGENTS.md", ".mission"],
    }


def seed(root: Path, features: list[dict] | None = None) -> None:
    (root / "AGENTS.md").write_text("# Canonical mission doctrine\n", encoding="utf-8")
    write_json(root / ".mission" / "owner_constraints.json", base_constraints())
    write_json(root / ".mission" / "features.json", {"features": features or []})


def expect_block(label: str, setup) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup(root)
        try:
            validate(root)
        except MissionError:
            return
        raise AssertionError(f"{label}: expected MissionError")


def expect_ready(label: str, setup) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        setup(root)
        try:
            validate(root)
        except MissionError as exc:
            raise AssertionError(f"{label}: unexpected block: {exc}") from exc


def main() -> int:
    expect_ready("empty governed repo", lambda root: seed(root))

    def untraced(root: Path) -> None:
        seed(root)
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")

    expect_block("untraced product file", untraced)

    def derived_only(root: Path) -> None:
        seed(
            root,
            [
                {
                    "id": "F1",
                    "class": "mirror",
                    "user_visible": True,
                    "source_evidence": [{"kind": "derived_analysis", "ref": "agent design"}],
                    "implementation_paths": [],
                }
            ],
        )

    expect_block("derived-only mirror", derived_only)

    def augmentation_without_owner(root: Path) -> None:
        seed(
            root,
            [
                {
                    "id": "F1",
                    "class": "augmentation",
                    "user_visible": True,
                    "source_evidence": [{"kind": "primary_artifact", "ref": "source"}],
                    "implementation_paths": [],
                }
            ],
        )

    expect_block("unauthorized augmentation", augmentation_without_owner)

    def workflow_change_without_user(root: Path) -> None:
        seed(
            root,
            [
                {
                    "id": "F1",
                    "class": "augmentation",
                    "user_visible": True,
                    "changes_default_workflow": True,
                    "source_evidence": [{"kind": "owner_explicit", "ref": "owner approval"}],
                    "implementation_paths": [],
                }
            ],
        )

    expect_block("workflow change without user confirmation", workflow_change_without_user)

    def traced_mirror(root: Path) -> None:
        seed(
            root,
            [
                {
                    "id": "F1",
                    "class": "mirror",
                    "user_visible": True,
                    "source_evidence": [{"kind": "primary_artifact", "ref": "source artifact section A"}],
                    "implementation_paths": ["src/app.py"],
                }
            ],
        )
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("print('mirrored')\n", encoding="utf-8")

    expect_ready("traced mirror", traced_mirror)

    print("MISSION PREFLIGHT SELF-TEST PASS: 6 adversarial/positive cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
