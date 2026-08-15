#!/usr/bin/env python3
"""Deterministic repository mission/source-fidelity preflight.

This companion to repo_preflight.py checks a failure class that ordinary release
hygiene cannot detect: a repository can be clean, well tested, and still implement
the wrong product. The scanner validates explicit mission/source/feature trace
structure. It does not use an LLM and does not semantically certify requirements.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import subprocess
import sys


DEFAULT_ALLOWED_CLASSES = {"mirror", "defect_fix", "augmentation", "infrastructure", "research"}
DEFAULT_PRIMARY_SOURCE_KINDS = {
    "primary_artifact",
    "source_system",
    "workbook",
    "user_confirmed",
    "joseph_confirmed",
}
DEFAULT_USER_CONFIRMATION_KINDS = {"user_confirmed", "joseph_confirmed", "domain_confirmed"}
DEFAULT_OWNER_AUTH_KINDS = {"owner_explicit"}
DERIVED_KINDS = {"derived_analysis"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", ".venv", "venv"}
SKIP_SUFFIXES = {".md", ".txt", ".lock", ".map"}


class MissionError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MissionError(f"missing required mission file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise MissionError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MissionError(f"mission file must contain a JSON object: {path}")
    return value


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or path.startswith(pattern.rstrip("/") + "/") for pattern in patterns)


def product_files(root: Path, product_roots: list[str]) -> set[str]:
    found: set[str] = set()
    for root_name in product_roots:
        base = root / root_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(root).parts
            if any(part in SKIP_DIRS for part in rel_parts):
                continue
            rel = path.relative_to(root).as_posix()
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            found.add(rel)
    return found


def changed_files(root: Path, base_ref: str) -> set[str] | None:
    if not (root / ".git").exists():
        return None
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", base_ref],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        output = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=root,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return {line.strip() for line in output.splitlines() if line.strip()}


def string_set(value: object, default: set[str], label: str) -> set[str]:
    if value is None:
        return set(default)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise MissionError(f"{label} must be a non-empty-string array")
    return set(value)


def validate(root: Path, base_ref: str = "origin/main") -> tuple[int, int]:
    mission_dir = root / ".mission"
    constraints = load_json(mission_dir / "owner_constraints.json")
    feature_doc = load_json(mission_dir / "features.json")

    objective = constraints.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        raise MissionError("owner_constraints.json requires a non-empty objective")

    budget = constraints.get("default_invention_budget")
    if not isinstance(budget, int) or budget < 0:
        raise MissionError("default_invention_budget must be an integer >= 0")

    if constraints.get("derived_analysis_may_authorize_user_behavior") is not False:
        raise MissionError("derived_analysis_may_authorize_user_behavior must be false")

    doctrine = constraints.get("canonical_agent_doctrine", "AGENTS.md")
    if not isinstance(doctrine, str) or not doctrine:
        raise MissionError("canonical_agent_doctrine must be a non-empty path")
    if not (root / doctrine).is_file():
        raise MissionError(f"canonical agent doctrine is missing: {doctrine}")

    if constraints.get("tool_specific_instructions_may_override_agents") is True:
        raise MissionError("tool-specific instructions must not be allowed to override canonical agent doctrine")

    allowed_classes = string_set(constraints.get("allowed_change_classes"), DEFAULT_ALLOWED_CLASSES, "allowed_change_classes")
    primary_kinds = string_set(constraints.get("primary_source_kinds"), DEFAULT_PRIMARY_SOURCE_KINDS, "primary_source_kinds")
    user_confirmation_kinds = string_set(
        constraints.get("user_confirmation_kinds"), DEFAULT_USER_CONFIRMATION_KINDS, "user_confirmation_kinds"
    )
    owner_auth_kinds = string_set(constraints.get("owner_authorization_kinds"), DEFAULT_OWNER_AUTH_KINDS, "owner_authorization_kinds")

    features = feature_doc.get("features")
    if not isinstance(features, list):
        raise MissionError(".mission/features.json must contain a features array")

    ids: set[str] = set()
    covered_paths: set[str] = set()
    for index, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            raise MissionError(f"feature #{index} is not an object")
        feature_id = feature.get("id")
        if not isinstance(feature_id, str) or not feature_id or feature_id in ids:
            raise MissionError(f"feature #{index} has missing or duplicate id: {feature_id!r}")
        ids.add(feature_id)

        change_class = feature.get("class")
        if change_class not in allowed_classes:
            raise MissionError(f"{feature_id}: invalid class {change_class!r}")

        evidence = feature.get("source_evidence", [])
        implementation_paths = feature.get("implementation_paths", [])
        if not isinstance(evidence, list) or not isinstance(implementation_paths, list):
            raise MissionError(f"{feature_id}: source_evidence and implementation_paths must be arrays")

        kinds: set[str] = set()
        for item in evidence:
            if not isinstance(item, dict) or not item.get("kind") or not item.get("ref"):
                raise MissionError(f"{feature_id}: every evidence item needs kind and ref")
            kinds.add(str(item["kind"]))

        user_visible = bool(feature.get("user_visible"))
        if user_visible and change_class in {"mirror", "defect_fix"} and not (kinds & primary_kinds):
            raise MissionError(f"{feature_id}: mirrored/fixed user behavior requires primary source or user-confirmed evidence")
        if user_visible and kinds and kinds <= DERIVED_KINDS:
            raise MissionError(f"{feature_id}: derived analysis alone cannot authorize user-visible behavior")
        if user_visible and not kinds:
            raise MissionError(f"{feature_id}: user-visible behavior has no source evidence")

        if user_visible and change_class == "augmentation":
            if budget == 0 and not (kinds & owner_auth_kinds):
                raise MissionError(f"{feature_id}: zero invention budget requires explicit owner authorization for augmentation")
            if feature.get("changes_default_workflow") is True and not (kinds & user_confirmation_kinds):
                raise MissionError(f"{feature_id}: default workflow changes require user/domain confirmation")

        for path in implementation_paths:
            if not isinstance(path, str) or not path:
                raise MissionError(f"{feature_id}: invalid implementation path")
            covered_paths.add(path)

    roots = constraints.get("product_roots", [])
    if not isinstance(roots, list) or not all(isinstance(item, str) and item for item in roots):
        raise MissionError("product_roots must be an array of non-empty paths")
    implementation = product_files(root, roots)
    uncovered = sorted(path for path in implementation if not matches_any(path, list(covered_paths)))
    if uncovered:
        raise MissionError("product implementation exists without originating feature trace: " + ", ".join(uncovered[:8]))

    changed = changed_files(root, base_ref)
    if changed is not None:
        protected = constraints.get("protected_mission_paths", [doctrine, ".mission"])
        if not isinstance(protected, list) or not all(isinstance(item, str) and item for item in protected):
            raise MissionError("protected_mission_paths must be an array of paths")
        changed_mission = [path for path in changed if matches_any(path, protected)]
        changed_product = [
            path for path in changed if any(path == product_root or path.startswith(product_root.rstrip("/") + "/") for product_root in roots)
        ]
        if changed_mission and changed_product:
            raise MissionError("mission contract and product behavior changed in the same branch; split the changes")

    return len(features), len(implementation)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic mission/source-fidelity repository preflight")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--base-ref", default=os.environ.get("MISSION_BASE_REF", "origin/main"))
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    try:
        feature_count, product_count = validate(root, args.base_ref)
    except MissionError as exc:
        print(f"MISSION PREFLIGHT BLOCKED: {exc}")
        return 1

    print(f"MISSION PREFLIGHT READY: {feature_count} feature record(s), {product_count} traced product file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
