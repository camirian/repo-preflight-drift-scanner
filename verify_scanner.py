#!/usr/bin/env python3
"""Verify the repo preflight drift scanner."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)


def require(condition: bool, message: str) -> bool:
    if not condition:
        print(message)
        return False
    return True


def make_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "sample-repo"
    shutil.copytree(ROOT / "examples/sample-repo", fixture_repo)
    (fixture_repo / "credentials.json").write_text('{"fixture": true}\n', encoding="utf-8")
    return fixture_repo


def make_rule_pack_fixture(tmpdir: str) -> tuple[Path, Path]:
    fixture_repo = Path(tmpdir) / "rule-pack-repo"
    fixture_repo.mkdir()
    for name in ["README.md", "SPEC.md", "VERIFICATION_PLAN.md", "PRE_RELEASE_CHECKLIST.md"]:
        (fixture_repo / name).write_text(f"# {name}\n\nBaseline process file.\n", encoding="utf-8")
    (fixture_repo / "README.md").write_text(
        "# Rule Pack Fixture\n\n"
        "This file contains launch unicorn language.\n"
        "We should ask investor later before release.\n",
        encoding="utf-8",
    )
    (fixture_repo / "custom.secret").write_text("DO_NOT_LEAK_RULE_PACK_SECRET\n", encoding="utf-8")
    (fixture_repo / "artifact-cache").mkdir()
    (fixture_repo / "artifact-cache" / "generated.txt").write_text("generated\n", encoding="utf-8")
    (fixture_repo / "ignored-zone").mkdir()
    (fixture_repo / "ignored-zone" / "README.md").write_text("launch unicorn\n", encoding="utf-8")
    (fixture_repo / "ignored.md").write_text("launch unicorn\n", encoding="utf-8")

    config_path = Path(tmpdir) / "rule-pack.json"
    config_path.write_text(
        json.dumps(
            {
                "required_process_files": {"CUSTOM_GATE": ["CUSTOM_GATE.md"]},
                "risky_claims": ["launch unicorn"],
                "drift_markers": ["ask investor later"],
                "public_sensitive_term_allowlist": ["caa" + "ren"],
                "secret_filenames": ["custom.secret"],
                "generated_dirs": ["artifact-cache"],
                "excluded_dirs": ["ignored-zone"],
                "excluded_files": ["ignored.md"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture_repo, config_path


def make_docs_heavy_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "docs-heavy-repo"
    fixture_repo.mkdir()
    (fixture_repo / "README.md").write_text(
        "# Docs Heavy Fixture\n\n"
        "This project is production " "ready and replaces human " "review.\n"
        "TO" "DO: replace " "this with final release language.\n",
        encoding="utf-8",
    )
    (fixture_repo / "SPEC.md").write_text("# Spec\n\nPlace" "holder architecture notes.\n", encoding="utf-8")
    (fixture_repo / "VERIFICATION_PLAN.md").write_text(
        "# Verification Plan\n\n- [" " ] Verify report outputs.\n",
        encoding="utf-8",
    )
    (fixture_repo / "PRE_RELEASE_CHECKLIST.md").write_text(
        "# Pre-Release Checklist\n\n- [" " ] Human release review completed.\n",
        encoding="utf-8",
    )
    (fixture_repo / "docs").mkdir()
    (fixture_repo / "docs" / "GUIDE.md").write_text(
        "# Guide\n\nFIX" "ME: T" "BD after launch.\n",
        encoding="utf-8",
    )
    (fixture_repo / "dist").mkdir()
    (fixture_repo / "dist" / "generated.txt").write_text("generated\n", encoding="utf-8")
    return fixture_repo


def make_public_export_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "public-export-repo"
    fixture_repo.mkdir()
    for name in ["README.md", "SPEC.md", "VERIFICATION_PLAN.md", "PRE_RELEASE_CHECKLIST.md"]:
        (fixture_repo / name).write_text(f"# {name}\n\nRelease gate complete.\n", encoding="utf-8")
    (fixture_repo / "PRODUCT_LISTING.md").write_text(
        "# Product Listing\n\nBuyer-facing listing draft.\n",
        encoding="utf-8",
    )
    (fixture_repo / "private-notes").mkdir()
    (fixture_repo / "private-notes" / "notes.md").write_text(
        "# Notes\n\nInternal export " "control reminder.\n",
        encoding="utf-8",
    )
    (fixture_repo / "src.py").write_text(
        'TOKEN_EXAMPLE = "ghp_' "abcdefghijklmnopqrstuvwx" '"\n',
        encoding="utf-8",
    )
    return fixture_repo


def run_profile_scan(repo: Path, profile: str, tmpdir: str, stem: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    out_md = Path(tmpdir) / f"{stem}.md"
    out_json = Path(tmpdir) / f"{stem}.json"
    out_html = Path(tmpdir) / f"{stem}.html"
    out_sarif = Path(tmpdir) / f"{stem}.sarif"
    result = run(
        [
            sys.executable,
            "repo_preflight.py",
            "--repo",
            str(repo),
            "--profile",
            profile,
            "--out-md",
            str(out_md),
            "--out-json",
            str(out_json),
            "--out-html",
            str(out_html),
            "--out-sarif",
            str(out_sarif),
        ]
    )
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    return result, {
        "json": payload,
        "markdown": out_md.read_text(encoding="utf-8"),
        "html": out_html.read_text(encoding="utf-8"),
        "sarif": json.loads(out_sarif.read_text(encoding="utf-8")),
    }


def require_output_format_compatibility(reports: dict, profile: str) -> bool:
    payload = reports["json"]
    markdown = reports["markdown"]
    html_report = reports["html"]
    sarif_payload = reports["sarif"]
    findings = payload["findings"]
    counts = payload["counts"]
    sarif_results = sarif_payload["runs"][0]["results"]

    checks = [
        (payload.get("schema_version") == "1.0", "Expected JSON schema_version 1.0."),
        (payload["profile"] == profile, f"Expected JSON profile {profile}."),
        (f"Profile: `{profile}`" in markdown, f"Expected Markdown profile {profile}."),
        (f"<code>{profile}</code>" in html_report, f"Expected HTML profile {profile}."),
        (f"Decision: {payload['decision']}" in markdown, "Expected Markdown decision to match JSON."),
        (f"<p><strong>Decision:</strong> {payload['decision']}</p>" in html_report, "Expected HTML decision to match JSON."),
        (f"- Blockers: {counts['blocker']}" in markdown, "Expected Markdown blocker count to match JSON."),
        (f"- Warnings: {counts['warning']}" in markdown, "Expected Markdown warning count to match JSON."),
        (f"- Info: {counts['info']}" in markdown, "Expected Markdown info count to match JSON."),
        (len(sarif_results) == len(findings), "Expected SARIF result count to match JSON findings."),
    ]
    for condition, message in checks:
        if not require(condition, message):
            return False

    json_codes = {finding["code"] for finding in findings}
    sarif_codes = {result["ruleId"] for result in sarif_results}
    if not require(sarif_codes == json_codes, "Expected SARIF rule IDs to match JSON finding codes."):
        return False
    return True


def require_json_report_contract(payload: dict) -> bool:
    required_top_level = {"schema_version", "repo", "profile", "decision", "counts", "findings"}
    missing_top_level = sorted(required_top_level - payload.keys())
    if missing_top_level:
        print("JSON report missing required fields:")
        for field in missing_top_level:
            print(f"- {field}")
        return False
    if not require(payload["schema_version"] == "1.0", "Expected JSON report schema_version 1.0."):
        return False
    if not require(payload["decision"] in {"READY", "BLOCKED"}, "Expected JSON report decision enum."):
        return False
    if not require(set(payload["counts"]) >= {"blocker", "warning", "info"}, "Expected JSON report count keys."):
        return False
    if not require(all(isinstance(payload["counts"][level], int) and payload["counts"][level] >= 0 for level in ["blocker", "warning", "info"]), "Expected JSON report counts to be non-negative integers."):
        return False
    for finding in payload["findings"]:
        missing_finding_fields = sorted({"level", "code", "path", "message"} - finding.keys())
        if missing_finding_fields:
            print("JSON report finding missing required fields:")
            for field in missing_finding_fields:
                print(f"- {field}")
            return False
        if not require(finding["level"] in {"blocker", "warning", "info"}, "Expected JSON finding level enum."):
            return False
    if "baseline_diff" in payload:
        baseline_diff = payload["baseline_diff"]
        if not require(
            set(baseline_diff) >= {"new", "resolved", "new_findings", "resolved_findings"},
            "Expected baseline_diff contract fields.",
        ):
            return False
    return True


def verify_json_schema_artifact() -> bool:
    schema_path = ROOT / "docs" / "report.schema.json"
    if not require(schema_path.is_file(), "Expected machine-readable report schema artifact."):
        return False
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required_top_level = {"schema_version", "repo", "profile", "decision", "counts", "findings"}
    if not require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "Expected draft 2020-12 JSON Schema."):
        return False
    if not require(schema.get("type") == "object", "Expected report schema object root."):
        return False
    if not require(set(schema.get("required", [])) >= required_top_level, "Expected report schema required top-level fields."):
        return False
    properties = schema.get("properties", {})
    if not require(properties.get("schema_version", {}).get("const") == "1.0", "Expected report schema version const."):
        return False
    if not require(properties.get("decision", {}).get("enum") == ["READY", "BLOCKED"], "Expected report decision enum."):
        return False
    defs = schema.get("$defs", {})
    counts_required = set(defs.get("counts", {}).get("required", []))
    finding_required = set(defs.get("finding", {}).get("required", []))
    baseline_required = set(defs.get("baseline_diff", {}).get("required", []))
    if not require(counts_required >= {"blocker", "warning", "info"}, "Expected counts schema required fields."):
        return False
    if not require(finding_required >= {"level", "code", "path", "message"}, "Expected finding schema required fields."):
        return False
    if not require(
        baseline_required >= {"new", "resolved", "new_findings", "resolved_findings"},
        "Expected baseline diff schema required fields.",
    ):
        return False
    return True


def verify_profile_and_output_coverage() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_heavy_repo = make_docs_heavy_fixture(tmpdir)
        strict_result, strict_reports = run_profile_scan(docs_heavy_repo, "strict", tmpdir, "strict-docs-heavy")
        docs_result, docs_reports = run_profile_scan(docs_heavy_repo, "docs", tmpdir, "docs-docs-heavy")

        if strict_result.returncode == 0:
            print("Expected strict docs-heavy fixture scan to find blockers.")
            print(strict_result.stdout)
            print(strict_result.stderr)
            return False
        if docs_result.returncode != 0:
            print("Expected docs profile docs-heavy fixture scan to pass.")
            print(docs_result.stdout)
            print(docs_result.stderr)
            return False
        if not require_output_format_compatibility(strict_reports, "strict"):
            return False
        if not require_output_format_compatibility(docs_reports, "docs"):
            return False

        strict_counts = strict_reports["json"]["counts"]
        docs_counts = docs_reports["json"]["counts"]
        strict_total = sum(strict_counts.values())
        docs_total = sum(docs_counts.values())
        if not require(docs_total < strict_total, "Expected docs profile to stay lower-noise than strict."):
            return False
        if not require(docs_counts == {"blocker": 0, "warning": 0, "info": 0}, "Expected docs profile to suppress docs-heavy noise."):
            return False
        strict_codes = {finding["code"] for finding in strict_reports["json"]["findings"]}
        expected_strict_codes = {
            "risky_public_claim",
            "drift_marker",
            "unchecked_release_gate",
            "generated_artifact_dir",
        }
        missing_strict_codes = sorted(expected_strict_codes - strict_codes)
        if missing_strict_codes:
            print("Missing expected strict docs-heavy finding codes:")
            for code in missing_strict_codes:
                print(f"- {code}")
            return False

        public_export_repo = make_public_export_fixture(tmpdir)
        strict_clean_result, strict_clean_reports = run_profile_scan(
            public_export_repo,
            "strict",
            tmpdir,
            "strict-public-export",
        )
        public_export_result, public_export_reports = run_profile_scan(
            public_export_repo,
            "public-export",
            tmpdir,
            "public-export",
        )
        if strict_clean_result.returncode != 0:
            print("Expected strict public-export fixture baseline to pass.")
            print(strict_clean_result.stdout)
            print(strict_clean_result.stderr)
            return False
        if public_export_result.returncode == 0:
            print("Expected public-export fixture scan to remain conservative and block.")
            print(public_export_result.stdout)
            print(public_export_result.stderr)
            return False
        if not require_output_format_compatibility(strict_clean_reports, "strict"):
            return False
        if not require_output_format_compatibility(public_export_reports, "public-export"):
            return False

        public_export_codes = {finding["code"] for finding in public_export_reports["json"]["findings"]}
        expected_public_export_codes = {
            "private_publication_surface",
            "public_sensitive_term",
            "github_token_literal",
        }
        missing_public_export_codes = sorted(expected_public_export_codes - public_export_codes)
        if missing_public_export_codes:
            print("Missing expected public-export conservative finding codes:")
            for code in missing_public_export_codes:
                print(f"- {code}")
            return False
        if not require(
            sum(public_export_reports["json"]["counts"].values()) > sum(strict_clean_reports["json"]["counts"].values()),
            "Expected public-export profile to be more conservative than strict on public-export fixture.",
        ):
            return False
    return True


def verify_cli_error_handling() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_repo = Path(tmpdir) / "ready-repo"
        fixture_repo.mkdir()
        for name in ["README.md", "SPEC.md", "VERIFICATION_PLAN.md", "PRE_RELEASE_CHECKLIST.md"]:
            (fixture_repo / name).write_text(f"# {name}\n", encoding="utf-8")

        cases = []
        invalid_json = Path(tmpdir) / "invalid.json"
        invalid_json.write_text("{not json\n", encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(invalid_json),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )

        unknown_key = Path(tmpdir) / "unknown-key.json"
        unknown_key.write_text('{"unknown": []}\n', encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(unknown_key),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        bad_list = Path(tmpdir) / "bad-list.json"
        bad_list.write_text('{"risky_claims": "not-a-list"}\n', encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(bad_list),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        bad_required = Path(tmpdir) / "bad-required.json"
        bad_required.write_text('{"required_process_files": []}\n', encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(bad_required),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        empty_term = Path(tmpdir) / "empty-term.json"
        empty_term.write_text('{"risky_claims": [""]}\n', encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(empty_term),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        empty_label = Path(tmpdir) / "empty-label.json"
        empty_label.write_text('{"required_process_files": {"": ["README.md"]}}\n', encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(empty_label),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        empty_candidates = Path(tmpdir) / "empty-candidates.json"
        empty_candidates.write_text('{"required_process_files": {"README": []}}\n', encoding="utf-8")
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--config",
                str(empty_candidates),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--redact-pattern",
                "[",
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--baseline-json",
                str(Path(tmpdir) / "missing-baseline.json"),
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )
        cases.append(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--fail-on-new-blockers-only",
                "--out-md",
                "VERIFY_ERROR_REPORT.md",
                "--out-json",
                "VERIFY_ERROR_REPORT.json",
            ]
        )

        for command in cases:
            result = run(command)
            if result.returncode != 2:
                print("Expected CLI error case to exit 2.")
                print(result.stdout)
                print(result.stderr)
                return False
            if "Repo preflight error:" not in result.stderr:
                print("Expected concise CLI error prefix.")
                print(result.stdout)
                print(result.stderr)
                return False
    return True


def verify_cli_profile_discovery() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_md = Path(tmpdir) / "REPO_PREFLIGHT_REPORT.md"
        out_json = Path(tmpdir) / "REPO_PREFLIGHT_REPORT.json"
        result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(Path(tmpdir) / "missing-repo"),
                "--out-md",
                str(out_md),
                "--out-json",
                str(out_json),
                "--list-profiles",
            ]
        )
        if result.returncode != 0:
            print("Expected --list-profiles to exit 0.")
            print(result.stdout)
            print(result.stderr)
            return False
        expected_lines = [
            "Available profiles:",
            "  docs: Low-noise checks for template-heavy documentation, sample reports, and user instructions.",
            "  dora-ai-readiness: Documentation evidence checks for seven DORA AI capability surfaces.",
            "  fieldheld-portfolio: AI capability and release-discipline checks for Fieldheld portfolio repos.",
            "  public-export: Publication-safety checks before sharing a repo, package, Action, template, or product.",
            "  strict: Normal release-discipline checks before merge, demo, handoff, or release artifact.",
        ]
        for line in expected_lines:
            if line not in result.stdout:
                print(f"Expected --list-profiles output line: {line}")
                print(result.stdout)
                print(result.stderr)
                return False
        if result.stderr:
            print("Expected --list-profiles to avoid stderr output.")
            print(result.stdout)
            print(result.stderr)
            return False
        if out_md.exists() or out_json.exists():
            print("Expected --list-profiles to exit without writing scan reports.")
            return False
    return True


def make_dora_ready_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "dora-ready-repo"
    fixture_repo.mkdir()
    (fixture_repo / "README.md").write_text(
        "# DORA Ready Fixture\n\n"
        "## AI Stance\n"
        "LLMs may summarize docs and draft implementation notes, but human review is required before release.\n\n"
        "## Data Boundary\n"
        "Allowed data is synthetic examples and public docs. Forbidden data includes secrets and private data.\n\n"
        "## AI-Accessible Context\n"
        "Agents may use AGENTS.md, schemas, examples, and this docs index as context.\n\n"
        "## Version Control And Rollback\n"
        "Use small commits with a documented rollback path and release manifest.\n\n"
        "## Small Batches\n"
        "The next slice has acceptance criteria and kill criteria before implementation.\n\n"
        "## User Focus\n"
        "Primary user is an AI-assisted builder; the user success signal is a clear ship/hold decision.\n\n"
        "## Internal Platform\n"
        "Quickstart and verification command: python3 repo_preflight.py --profile dora-ai-readiness.\n",
        encoding="utf-8",
    )
    (fixture_repo / "AGENTS.md").write_text("# Agent Context\n\nFollow the README boundaries.\n", encoding="utf-8")
    (fixture_repo / "credentials.json").write_text("DO_NOT_LEAK_DORA_FIXTURE_SECRET\n", encoding="utf-8")
    return fixture_repo


def make_dora_weak_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "dora-weak-repo"
    fixture_repo.mkdir()
    (fixture_repo / "README.md").write_text(
        "# DORA Weak Fixture\n\n"
        "This repo uses AI to move fast.\n",
        encoding="utf-8",
    )
    return fixture_repo


def verify_dora_ai_readiness_profile() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        ready_repo = make_dora_ready_fixture(tmpdir)
        weak_repo = make_dora_weak_fixture(tmpdir)

        ready_result, ready_reports = run_profile_scan(ready_repo, "dora-ai-readiness", tmpdir, "dora-ready")
        weak_result, weak_reports = run_profile_scan(weak_repo, "dora-ai-readiness", tmpdir, "dora-weak")

        if ready_result.returncode != 0:
            print("Expected DORA-ready fixture to pass.")
            print(ready_result.stdout)
            print(ready_result.stderr)
            return False
        if weak_result.returncode == 0:
            print("Expected DORA-weak fixture to block.")
            print(weak_result.stdout)
            print(weak_result.stderr)
            return False
        if not require_output_format_compatibility(ready_reports, "dora-ai-readiness"):
            return False
        if not require_output_format_compatibility(weak_reports, "dora-ai-readiness"):
            return False

        ready_payload = ready_reports["json"]
        weak_payload = weak_reports["json"]
        if "DO_NOT_LEAK_DORA_FIXTURE_SECRET" in json.dumps(ready_payload):
            print("DORA-ready secret-bearing fixture content leaked into report.")
            return False
        ready_codes = {finding["code"] for finding in ready_payload["findings"]}
        weak_codes = {finding["code"] for finding in weak_payload["findings"]}
        expected_ready_codes = {
            "dora_ai_stance_evidence",
            "dora_data_boundary_evidence",
            "dora_ai_accessible_context_evidence",
            "dora_version_control_evidence",
            "dora_small_batches_evidence",
            "dora_user_focus_evidence",
            "dora_internal_platform_evidence",
        }
        expected_weak_codes = {
            "missing_dora_ai_stance",
            "missing_dora_data_boundary",
            "missing_dora_ai_accessible_context",
            "missing_dora_version_control",
            "missing_dora_small_batches",
            "missing_dora_user_focus",
            "missing_dora_internal_platform",
        }
        missing_ready_codes = sorted(expected_ready_codes - ready_codes)
        if missing_ready_codes:
            print("Missing expected DORA evidence finding codes:")
            for code in missing_ready_codes:
                print(f"- {code}")
            return False
        missing_weak_codes = sorted(expected_weak_codes - weak_codes)
        if missing_weak_codes:
            print("Missing expected DORA missing-evidence finding codes:")
            for code in missing_weak_codes:
                print(f"- {code}")
            return False
        if not require(ready_payload["decision"] == "READY", "Expected DORA-ready decision to be READY."):
            return False
        if not require(weak_payload["decision"] == "BLOCKED", "Expected DORA-weak decision to be BLOCKED."):
            return False
    return True


def verify_dora_ai_readiness_action() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        ready_repo = make_dora_ready_fixture(tmpdir)
        weak_repo = make_dora_weak_fixture(tmpdir)

        cases = [
            ("ready", ready_repo, "READY"),
            ("weak", weak_repo, "BLOCKED"),
        ]
        for stem, repo, expected_decision in cases:
            out_json = Path(tmpdir) / f"dora-action-{stem}.json"
            action_env = os.environ.copy()
            action_env.update(
                {
                    "GITHUB_ACTION_PATH": str(ROOT),
                    "INPUT_REPO": str(repo),
                    "INPUT_PROFILE": "dora-ai-readiness",
                    "INPUT_OUT_MD": str(Path(tmpdir) / f"dora-action-{stem}.md"),
                    "INPUT_OUT_JSON": str(out_json),
                    "INPUT_OUT_HTML": str(Path(tmpdir) / f"dora-action-{stem}.html"),
                    "INPUT_OUT_SARIF": str(Path(tmpdir) / f"dora-action-{stem}.sarif"),
                    "INPUT_GITHUB_ANNOTATIONS": "false",
                    "INPUT_FAIL_ON_BLOCKERS": "false",
                }
            )
            action_result = subprocess.run(
                ["bash", "scripts/action_entrypoint.sh"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=action_env,
            )
            if action_result.returncode != 0:
                print(f"Expected DORA {stem} action smoke to exit 0 in report-only mode.")
                print(action_result.stdout)
                print(action_result.stderr)
                return False

            payload = json.loads(out_json.read_text(encoding="utf-8"))
            if not require(
                payload["profile"] == "dora-ai-readiness",
                f"Expected DORA {stem} action report profile to be dora-ai-readiness.",
            ):
                return False
            if not require(
                payload["decision"] == expected_decision,
                f"Expected DORA {stem} action report decision to be {expected_decision}.",
            ):
                return False
    return True


def run_fieldheld_scan(repo: Path, tmpdir: str, stem: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    out_md = Path(tmpdir) / f"{stem}.md"
    out_json = Path(tmpdir) / f"{stem}.json"
    out_html = Path(tmpdir) / f"{stem}.html"
    out_sarif = Path(tmpdir) / f"{stem}.sarif"
    result = run(
        [
            sys.executable,
            "repo_preflight.py",
            "--repo",
            str(repo),
            "--profile",
            "fieldheld-portfolio",
            "--config",
            "configs/fieldheld-portfolio.json",
            "--out-md",
            str(out_md),
            "--out-json",
            str(out_json),
            "--out-html",
            str(out_html),
            "--out-sarif",
            str(out_sarif),
        ]
    )
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    return result, {
        "json": payload,
        "markdown": out_md.read_text(encoding="utf-8"),
        "html": out_html.read_text(encoding="utf-8"),
        "sarif": json.loads(out_sarif.read_text(encoding="utf-8")),
    }


def make_fieldheld_ready_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "fieldheld-ready-repo"
    fixture_repo.mkdir()

    (fixture_repo / "README.md").write_text(
        "# Fieldheld Ready Fixture\n\n"
        "## AI Stance\n"
        "LLMs may draft code, but human review is required. This ai-assisted process ensures human review is followed.\n\n"
        "## Data Boundary\n"
        "Allowed data is restricted to synthetic test examples. Forbidden data includes production credentials and PII.\n\n"
        "## Rollback Path\n"
        "We maintain a clear version control branch with rollback notes and protective branches.\n\n"
        "## Small-Batch Delivery\n"
        "We deliver in small-batch slices with explicit acceptance criteria.\n\n"
        "## User or Buyer Focus\n"
        "Primary user is the internal developer, and our success signal is the verification gate passing.\n\n"
        "## Verification Evidence\n"
        "Run the verification command: python3 repo_preflight.py to get verification evidence.\n",
        encoding="utf-8",
    )
    (fixture_repo / "SPEC.md").write_text("# Spec\n\nDesign specifications.\n", encoding="utf-8")
    (fixture_repo / "VERIFICATION_PLAN.md").write_text("# Verification Plan\n\n[x] Checklist completed.\n", encoding="utf-8")
    (fixture_repo / "PRE_RELEASE_CHECKLIST.md").write_text("# Pre-release Checklist\n\n[x] Check done.\n", encoding="utf-8")

    return fixture_repo


def make_fieldheld_weak_fixture(tmpdir: str) -> Path:
    fixture_repo = Path(tmpdir) / "fieldheld-weak-repo"
    fixture_repo.mkdir()

    (fixture_repo / "README.md").write_text(
        "# Fieldheld Weak Fixture\n\n"
        "This project has achieved dora-mature status and compliance approved status.\n",
        encoding="utf-8",
    )
    (fixture_repo / "VERIFICATION_PLAN.md").write_text("# Verification Plan\n\n- [ ] Unchecked box!\n", encoding="utf-8")
    (fixture_repo / "PRE_RELEASE_CHECKLIST.md").write_text("# Pre-release Checklist\n\n- [ ] Another unchecked box.\n", encoding="utf-8")

    return fixture_repo


def verify_fieldheld_portfolio_profile() -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        ready_repo = make_fieldheld_ready_fixture(tmpdir)
        weak_repo = make_fieldheld_weak_fixture(tmpdir)

        ready_result, ready_reports = run_fieldheld_scan(ready_repo, tmpdir, "fieldheld-ready")
        weak_result, weak_reports = run_fieldheld_scan(weak_repo, tmpdir, "fieldheld-weak")

        if ready_result.returncode != 0:
            print("Expected Fieldheld-ready fixture to pass.")
            print(ready_result.stdout)
            print(ready_result.stderr)
            return False
        if weak_result.returncode == 0:
            print("Expected Fieldheld-weak fixture to block.")
            print(weak_result.stdout)
            print(weak_result.stderr)
            return False

        if not require_output_format_compatibility(ready_reports, "fieldheld-portfolio"):
            return False
        if not require_output_format_compatibility(weak_reports, "fieldheld-portfolio"):
            return False

        ready_payload = ready_reports["json"]
        weak_payload = weak_reports["json"]

        ready_codes = {finding["code"] for finding in ready_payload["findings"]}
        weak_codes = {finding["code"] for finding in weak_payload["findings"]}

        expected_ready_codes = {
            "fieldheld_ai_stance_evidence",
            "fieldheld_data_boundary_evidence",
            "fieldheld_rollback_path_evidence",
            "fieldheld_small_batch_delivery_evidence",
            "fieldheld_user_buyer_focus_evidence",
            "fieldheld_verification_evidence",
        }

        expected_weak_codes = {
            "missing_fieldheld_ai_stance",
            "missing_fieldheld_data_boundary",
            "missing_fieldheld_rollback_path",
            "missing_fieldheld_small_batch_delivery",
            "missing_fieldheld_user_buyer_focus",
            "missing_fieldheld_verification",
            "missing_process_file",
            "unchecked_release_gate",
            "risky_public_claim",
        }

        missing_ready_codes = sorted(expected_ready_codes - ready_codes)
        if missing_ready_codes:
            print("Missing expected Fieldheld evidence finding codes:")
            for code in missing_ready_codes:
                print(f"- {code}")
            return False

        missing_weak_codes = sorted(expected_weak_codes - weak_codes)
        if missing_weak_codes:
            print("Missing expected Fieldheld missing-evidence/blocker finding codes:")
            for code in missing_weak_codes:
                print(f"- {code}")
            return False

        if not require(ready_payload["decision"] == "READY", "Expected Fieldheld-ready decision to be READY."):
            return False
        if not require(weak_payload["decision"] == "BLOCKED", "Expected Fieldheld-weak decision to be BLOCKED."):
            return False

    return True


def copy_for_package_verification(dst: Path) -> None:
    ignored_dirs = {
        ".git",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "release",
    }

    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignored_dirs}

    shutil.copytree(ROOT, dst, ignore=ignore)


def verify_release_package_boundary() -> bool:
    version = "verify-boundary"
    package_name = f"ai-agent-repo-preflight-kit-{version}"
    required_files = {
        "README-for-users.md",
        "README.md",
        "SPEC.md",
        "VERIFICATION_PLAN.md",
        "PRE_RELEASE_CHECKLIST.md",
        "SECURITY.md",
        "BLAST_RADIUS_AUDIT.md",
        "Makefile",
        "verify_scanner.py",
        "repo_preflight.py",
        "action.yml",
        "scripts/action_entrypoint.sh",
        "scripts/package_release.sh",
        "configs/founder-strict.json",
        "configs/team-policy.json",
        "configs/fieldheld-portfolio.json",
        "docs/dora-ai-readiness.md",
        "docs/dora-ai-readiness-profile.md",
        "docs/report-schema.md",
        "docs/report.schema.json",
        "docs/rule-packs.md",
        "docs/sarif-output.md",
        "docs/user/quickstart.md",
        "docs/user/local-cli-setup.md",
        "docs/user/github-action-setup.md",
        "docs/user/how-to-use-the-kit.md",
        "docs/user/sample-report-walkthrough.md",
        "docs/user/what-this-is-not.md",
        "examples/github-action.yml",
        "examples/fieldheld-github-action.yml",
        "examples/sample-repo/README.md",
        "examples/sample-repo/SPEC.md",
        "examples/sample-repo/PRE_RELEASE_CHECKLIST.md",
        "examples/sample-repo/app.py",
        "examples/sample-repo/dist/generated.txt",
    }
    forbidden_exact = {
        "release-checklist.md",
        "docs/release-checklist.md",
    }
    report_suffixes = {".md", ".json", ".html", ".sarif"}

    with tempfile.TemporaryDirectory() as tmpdir:
        package_root = Path(tmpdir) / "package-root"
        copy_for_package_verification(package_root)

        package_result = subprocess.run(
            ["bash", "scripts/package_release.sh", version],
            cwd=package_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if package_result.returncode != 0:
            print("Expected package script to build user ZIP.")
            print(package_result.stdout)
            print(package_result.stderr)
            return False

        zip_path = package_root / "release" / f"{package_name}.zip"
        if not require(zip_path.is_file(), "Expected user ZIP to be created."):
            return False
        first_digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()

        repeat_package_result = subprocess.run(
            ["bash", "scripts/package_release.sh", version],
            cwd=package_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if repeat_package_result.returncode != 0:
            print("Expected repeated package script run to build user ZIP.")
            print(repeat_package_result.stdout)
            print(repeat_package_result.stderr)
            return False
        second_digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        if not require(first_digest == second_digest, "Expected user ZIP builds to be reproducible."):
            return False

        with ZipFile(zip_path) as zf:
            manifest = sorted(name for name in zf.namelist() if not name.endswith("/"))
            prefix = f"{package_name}/"
            non_deterministic_timestamps = sorted(
                info.filename
                for info in zf.infolist()
                if not info.is_dir() and info.date_time != (1980, 1, 1, 0, 0, 0)
            )
            if non_deterministic_timestamps:
                print("user ZIP files have non-deterministic timestamps:")
                for path in non_deterministic_timestamps:
                    print(f"- {path}")
                return False
            executable_members = {
                PurePosixPath(info.filename).as_posix().removeprefix(prefix)
                for info in zf.infolist()
                if not info.is_dir() and ((info.external_attr >> 16) & 0o111)
            }
            if not require(
                "scripts/action_entrypoint.sh" in executable_members,
                "Expected packaged action entrypoint to preserve executable mode.",
            ):
                return False

            for name in manifest:
                parts = PurePosixPath(name).parts
                if name.startswith("/") or ".." in parts:
                    print(f"Unsafe ZIP member path: {name}")
                    return False
                if ".git" in parts:
                    print(f"Unexpected .git content in user ZIP: {name}")
                    return False

            if not require(
                all(name.startswith(prefix) for name in manifest),
                "Expected all ZIP members under package directory.",
            ):
                return False

            packaged_files = {name.removeprefix(prefix) for name in manifest}
            missing_files = sorted(required_files - packaged_files)
            if missing_files:
                print("Missing required internal QA package files:")
                for path in missing_files:
                    print(f"- {path}")
                return False

            forbidden_files = sorted(
                path
                for path in packaged_files
                if path in forbidden_exact or path.startswith("docs/marketing/")
            )
            if forbidden_files:
                print("Seller/admin files leaked into internal QA package:")
                for path in forbidden_files:
                    print(f"- {path}")
                return False

            generated_reports = sorted(
                path
                for path in packaged_files
                if PurePosixPath(path).suffix in report_suffixes
                and (
                    PurePosixPath(path).name.startswith("REPORT.")
                    or PurePosixPath(path).name.startswith("REPO_PREFLIGHT_REPORT.")
                    or PurePosixPath(path).name.startswith("VERIFY_")
                )
            )
            if generated_reports:
                print("Generated report files leaked into internal QA package:")
                for path in generated_reports:
                    print(f"- {path}")
                return False

            extract_root = Path(tmpdir) / "extracted"
            zf.extractall(extract_root)

        extracted_package = extract_root / package_name
        demo_result = subprocess.run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                "examples/sample-repo",
                "--include-fixtures",
                "--out-md",
                "REPO_PREFLIGHT_REPORT.md",
                "--out-json",
                "REPO_PREFLIGHT_REPORT.json",
                "--out-html",
                "REPO_PREFLIGHT_REPORT.html",
                "--out-sarif",
                "REPO_PREFLIGHT_REPORT.sarif",
            ],
            cwd=extracted_package,
            check=False,
            capture_output=True,
            text=True,
        )
        if demo_result.returncode == 0:
            print("Expected extracted sample CLI demo to find blockers.")
            print(demo_result.stdout)
            print(demo_result.stderr)
            return False

        expected_reports = [
            "REPO_PREFLIGHT_REPORT.md",
            "REPO_PREFLIGHT_REPORT.json",
            "REPO_PREFLIGHT_REPORT.html",
            "REPO_PREFLIGHT_REPORT.sarif",
        ]
        missing_reports = [
            path for path in expected_reports if not (extracted_package / path).is_file()
        ]
        if missing_reports:
            print("Extracted CLI demo did not produce expected reports:")
            for path in missing_reports:
                print(f"- {path}")
            return False

        demo_payload = json.loads((extracted_package / "REPO_PREFLIGHT_REPORT.json").read_text(encoding="utf-8"))
        if not require_json_report_contract(demo_payload):
            return False
        if not require(demo_payload["decision"] == "BLOCKED", "Expected extracted CLI demo report to be BLOCKED."):
            return False

        extracted_dora_repo = make_dora_ready_fixture(tmpdir)
        extracted_dora_result = subprocess.run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(extracted_dora_repo),
                "--profile",
                "dora-ai-readiness",
                "--out-md",
                "EXTRACTED_DORA_REPORT.md",
                "--out-json",
                "EXTRACTED_DORA_REPORT.json",
            ],
            cwd=extracted_package,
            check=False,
            capture_output=True,
            text=True,
        )
        if extracted_dora_result.returncode != 0:
            print("Expected extracted package DORA-ready scan to pass.")
            print(extracted_dora_result.stdout)
            print(extracted_dora_result.stderr)
            return False
        extracted_dora_payload = json.loads((extracted_package / "EXTRACTED_DORA_REPORT.json").read_text(encoding="utf-8"))
        if not require_json_report_contract(extracted_dora_payload):
            return False
        if not require(
            extracted_dora_payload["profile"] == "dora-ai-readiness",
            "Expected extracted DORA report profile.",
        ):
            return False
        if not require(extracted_dora_payload["decision"] == "READY", "Expected extracted DORA report to be READY."):
            return False
        extracted_dora_codes = {finding["code"] for finding in extracted_dora_payload["findings"]}
        expected_extracted_dora_codes = {
            "dora_ai_stance_evidence",
            "dora_data_boundary_evidence",
            "dora_ai_accessible_context_evidence",
            "dora_version_control_evidence",
            "dora_small_batches_evidence",
            "dora_user_focus_evidence",
            "dora_internal_platform_evidence",
        }
        missing_extracted_dora_codes = sorted(expected_extracted_dora_codes - extracted_dora_codes)
        if missing_extracted_dora_codes:
            print("Missing expected extracted DORA evidence finding codes:")
            for code in missing_extracted_dora_codes:
                print(f"- {code}")
            return False

        extracted_dora_self_result = subprocess.run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                ".",
                "--profile",
                "dora-ai-readiness",
                "--out-md",
                "EXTRACTED_DORA_SELF_REPORT.md",
                "--out-json",
                "EXTRACTED_DORA_SELF_REPORT.json",
            ],
            cwd=extracted_package,
            check=False,
            capture_output=True,
            text=True,
        )
        if extracted_dora_self_result.returncode != 0:
            print("Expected extracted package DORA self-scan to pass.")
            print(extracted_dora_self_result.stdout)
            print(extracted_dora_self_result.stderr)
            return False
        for report_path in ["EXTRACTED_DORA_SELF_REPORT.md", "EXTRACTED_DORA_SELF_REPORT.json"]:
            if not require(
                (extracted_package / report_path).is_file(),
                f"Expected extracted DORA self-scan report: {report_path}",
            ):
                return False
        extracted_dora_self_payload = json.loads(
            (extracted_package / "EXTRACTED_DORA_SELF_REPORT.json").read_text(encoding="utf-8")
        )
        if not require_json_report_contract(extracted_dora_self_payload):
            return False
        if not require(extracted_dora_self_payload["repo"] == ".", "Expected extracted DORA self-scan repo path."):
            return False
        if not require(
            extracted_dora_self_payload["profile"] == "dora-ai-readiness",
            "Expected extracted DORA self-scan profile.",
        ):
            return False
        if not require(
            extracted_dora_self_payload["decision"] == "READY",
            "Expected extracted DORA self-scan to be READY.",
        ):
            return False
        if not require(
            extracted_dora_self_payload["counts"] == {"blocker": 0, "warning": 0, "info": 7},
            "Expected extracted DORA self-scan counts.",
        ):
            return False
        extracted_dora_self_codes = {finding["code"] for finding in extracted_dora_self_payload["findings"]}
        if not require(
            extracted_dora_self_codes == expected_extracted_dora_codes,
            "Expected extracted DORA self-scan to report exactly the seven evidence codes.",
        ):
            return False

        extracted_action_env = os.environ.copy()
        extracted_action_env.update(
            {
                "GITHUB_ACTION_PATH": str(extracted_package),
                "INPUT_REPO": "examples/sample-repo",
                "INPUT_OUT_MD": "EXTRACTED_ACTION_REPORT.md",
                "INPUT_OUT_JSON": "EXTRACTED_ACTION_REPORT.json",
                "INPUT_INCLUDE_FIXTURES": "true",
                "INPUT_GITHUB_ANNOTATIONS": "false",
                "INPUT_FAIL_ON_BLOCKERS": "false",
            }
        )
        extracted_action_result = subprocess.run(
            ["bash", str(extracted_package / "scripts/action_entrypoint.sh")],
            cwd=extracted_package,
            check=False,
            capture_output=True,
            text=True,
            env=extracted_action_env,
        )
        if extracted_action_result.returncode != 0:
            print("Expected extracted action entrypoint to run through bash in report-only mode.")
            print(extracted_action_result.stdout)
            print(extracted_action_result.stderr)
            return False
        extracted_action_payload = json.loads((extracted_package / "EXTRACTED_ACTION_REPORT.json").read_text(encoding="utf-8"))
        if not require_json_report_contract(extracted_action_payload):
            return False
        if not require(
            extracted_action_payload["decision"] == "BLOCKED",
            "Expected extracted action entrypoint report to be BLOCKED.",
        ):
            return False

    return True


# Source-boundary policy: paths that must never be tracked in git source because
# they are generated reports, build/cache output, or release artifacts. This
# complements .gitignore by also catching force-added files and artifact types
# not yet listed there. See docs/source-boundary.md.
DISALLOWED_TRACKED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "release",
}

DISALLOWED_REPORT_SUFFIXES = {".md", ".json", ".html", ".sarif"}


def is_disallowed_tracked_artifact(rel_path: str) -> bool:
    """Return True if a git-tracked relative path is a generated/release artifact.

    Pure function: takes a POSIX-style relative path string and returns a bool.
    Disallowed when any path segment is a generated/cache/release directory, or
    when the file is a generated report (basename stem ends with ``_report`` or
    equals ``report``) with a report suffix. The synthetic fixture tree under
    ``examples/sample-repo`` is exempt: it intentionally ships generated-artifact
    paths so the demo can flag them.
    """
    posix = PurePosixPath(rel_path)
    if posix.parts[:2] == ("examples", "sample-repo"):
        return False
    parts = posix.parts
    if any(part in DISALLOWED_TRACKED_DIRS for part in parts):
        return True
    name = PurePosixPath(rel_path).name
    stem, _, suffix = name.rpartition(".")
    suffix = f".{suffix.lower()}" if stem else ""
    stem = stem.lower()
    if suffix in DISALLOWED_REPORT_SUFFIXES and (stem == "report" or stem.endswith("_report")):
        return True
    return False


def verify_source_boundary() -> bool:
    # Positive case: the classifier must flag disallowed artifacts so the guard
    # can fail rather than passing vacuously on an already-clean tree.
    disallowed_samples = [
        "REPORT.json",
        "VERIFY_SELF_REPORT.md",
        "release/ai-agent-repo-preflight-kit-v0.5.zip",
        "src/__pycache__/mod.cpython-312.pyc",
        "build/output.txt",
    ]
    for sample in disallowed_samples:
        if not require(
            is_disallowed_tracked_artifact(sample),
            f"Expected classifier to flag disallowed artifact: {sample}",
        ):
            return False

    allowed_samples = [
        "repo_preflight.py",
        "docs/source-boundary.md",
        "docs/report.schema.json",
        "configs/team-policy.json",
        "examples/sample-repo/app.py",
        # Fixture tree is exempt even though it intentionally ships dist output.
        "examples/sample-repo/dist/generated.txt",
    ]
    for sample in allowed_samples:
        if not require(
            not is_disallowed_tracked_artifact(sample),
            f"Expected classifier to allow source file: {sample}",
        ):
            return False

    # Real-tree case: no disallowed artifact may be tracked in git source.
    listing = run(["git", "ls-files"])
    if listing.returncode != 0:
        # Not a git checkout (e.g. extracted package). Boundary is enforced at
        # source; skip silently rather than fail.
        return True
    tracked = [line for line in listing.stdout.splitlines() if line]
    offenders = sorted(path for path in tracked if is_disallowed_tracked_artifact(path))
    if offenders:
        print("Disallowed generated/release artifacts are tracked in git source:")
        for path in offenders:
            print(f"- {path}")
        return False
    return True


def main() -> int:
    action_metadata = (ROOT / "action.yml").read_text(encoding="utf-8")
    if not require("using: composite" in action_metadata, "Expected composite action metadata."):
        return 1
    if not require("scripts/action_entrypoint.sh" in action_metadata, "Expected action to use tested shell entrypoint."):
        return 1
    if not require('run: bash "$GITHUB_ACTION_PATH/scripts/action_entrypoint.sh"' in action_metadata, "Expected action to invoke entrypoint through bash."):
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_repo = make_fixture(tmpdir)

        result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--out-md",
                "REPORT.md",
                "--out-json",
                "REPORT.json",
                "--out-html",
                "REPORT.html",
                "--out-sarif",
                "REPORT.sarif",
                "--include-fixtures",
                "--github-annotations",
            ]
        )
        if result.returncode == 0:
            print("Expected blockers, but scanner exited ready.")
            return 1
        if "Repo preflight found blockers." not in result.stdout:
            print("Expected blocker message missing.")
            print(result.stdout)
            print(result.stderr)
            return 1

        markdown = (ROOT / "REPORT.md").read_text(encoding="utf-8")
        payload = json.loads((ROOT / "REPORT.json").read_text(encoding="utf-8"))
        sarif_payload = json.loads((ROOT / "REPORT.sarif").read_text(encoding="utf-8"))
        html_report = (ROOT / "REPORT.html").read_text(encoding="utf-8")

        required_codes = {
            "missing_process_file",
            "secret_bearing_filename",
            "unchecked_release_gate",
            "risky_public_claim",
            "generated_artifact_dir",
            "drift_marker",
        }
        found_codes = {finding["code"] for finding in payload["findings"]}
        missing_codes = sorted(required_codes - found_codes)
        if missing_codes:
            print("Missing expected finding codes:")
            for code in missing_codes:
                print(f"- {code}")
            return 1

        if payload.get("schema_version") != "1.0":
            print("Expected JSON schema_version 1.0.")
            return 1
        if not require_json_report_contract(payload):
            return 1
        if payload["decision"] != "BLOCKED" or payload["profile"] != "strict" or "Decision: BLOCKED" not in markdown:
            print("Expected BLOCKED decision.")
            return 1
        if payload["counts"]["blocker"] < 1 or payload["counts"]["warning"] < 1:
            print("Expected blocker and warning counts in JSON report.")
            return 1
        if sarif_payload["version"] != "2.1.0" or not sarif_payload["runs"][0]["results"]:
            print("Expected SARIF report with results.")
            return 1
        if "<html" not in html_report or "Repo Preflight Report" not in html_report:
            print("Expected HTML report.")
            return 1
        if "::error" not in result.stderr or "::warning" not in result.stderr:
            print("Expected GitHub annotation output.")
            return 1

        leaked_markers = ["DO_NOT_READ_THIS_SECRET"]
        for marker in leaked_markers:
            if marker in markdown or marker in json.dumps(payload):
                print(f"Secret marker leaked into report: {marker}")
                return 1

        action_env = os.environ.copy()
        action_env.update(
            {
                "GITHUB_ACTION_PATH": str(ROOT),
                "INPUT_REPO": str(fixture_repo),
                "INPUT_PROFILE": "strict",
                "INPUT_OUT_MD": "VERIFY_ACTION_REPORT.md",
                "INPUT_OUT_JSON": "VERIFY_ACTION_REPORT.json",
                "INPUT_OUT_HTML": "VERIFY_ACTION_REPORT.html",
                "INPUT_OUT_SARIF": "VERIFY_ACTION_REPORT.sarif",
                "INPUT_CONFIG": "configs/founder-strict.json",
                "INPUT_INCLUDE_FIXTURES": "true",
                "INPUT_GITHUB_ANNOTATIONS": "true",
                "INPUT_FAIL_ON_BLOCKERS": "false",
            }
        )
        action_result = subprocess.run(
            ["bash", "scripts/action_entrypoint.sh"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=action_env,
        )
        if action_result.returncode != 0:
            print("Expected action entrypoint report-only mode to exit 0.")
            print(action_result.stdout)
            print(action_result.stderr)
            return 1
        action_payload = json.loads((ROOT / "VERIFY_ACTION_REPORT.json").read_text(encoding="utf-8"))
        if not require(action_payload["decision"] == "BLOCKED", "Expected action-style fixture scan to produce BLOCKED report."):
            return 1

        fail_action_env = os.environ.copy()
        fail_action_env.update(
            {
                "GITHUB_ACTION_PATH": str(ROOT),
                "INPUT_REPO": str(fixture_repo),
                "INPUT_OUT_MD": str(Path(tmpdir) / "VERIFY_ACTION_FAIL_REPORT.md"),
                "INPUT_OUT_JSON": str(Path(tmpdir) / "VERIFY_ACTION_FAIL_REPORT.json"),
                "INPUT_INCLUDE_FIXTURES": "true",
                "INPUT_GITHUB_ANNOTATIONS": "false",
                "INPUT_FAIL_ON_BLOCKERS": "true",
            }
        )
        fail_action_result = subprocess.run(
            ["bash", "scripts/action_entrypoint.sh"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=fail_action_env,
        )
        if fail_action_result.returncode == 0:
            print("Expected action entrypoint fail-on-blockers mode to exit non-zero.")
            print(fail_action_result.stdout)
            print(fail_action_result.stderr)
            return 1
        fail_action_payload = json.loads((Path(tmpdir) / "VERIFY_ACTION_FAIL_REPORT.json").read_text(encoding="utf-8"))
        if not require(
            fail_action_payload["decision"] == "BLOCKED",
            "Expected fail-on-blockers action scan to produce BLOCKED report.",
        ):
            return 1

        baseline_aware_action_env = os.environ.copy()
        baseline_aware_action_env.update(
            {
                "GITHUB_ACTION_PATH": str(ROOT),
                "INPUT_REPO": str(fixture_repo),
                "INPUT_OUT_MD": str(Path(tmpdir) / "VERIFY_ACTION_BASELINE_AWARE_REPORT.md"),
                "INPUT_OUT_JSON": str(Path(tmpdir) / "VERIFY_ACTION_BASELINE_AWARE_REPORT.json"),
                "INPUT_BASELINE_JSON": str(ROOT / "REPORT.json"),
                "INPUT_FAIL_ON_NEW_BLOCKERS_ONLY": "true",
                "INPUT_INCLUDE_FIXTURES": "true",
                "INPUT_GITHUB_ANNOTATIONS": "false",
                "INPUT_FAIL_ON_BLOCKERS": "true",
            }
        )
        baseline_aware_action_result = subprocess.run(
            ["bash", "scripts/action_entrypoint.sh"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=baseline_aware_action_env,
        )
        if baseline_aware_action_result.returncode != 0:
            print("Expected baseline-aware action gate to pass with identical baseline.")
            print(baseline_aware_action_result.stdout)
            print(baseline_aware_action_result.stderr)
            return 1
        if "Repo preflight found blockers already present in baseline." not in baseline_aware_action_result.stdout:
            print("Expected baseline-aware action gate to report existing blockers.")
            print(baseline_aware_action_result.stdout)
            print(baseline_aware_action_result.stderr)
            return 1

        baseline_missing_blocker = Path(tmpdir) / "baseline-missing-blocker.json"
        baseline_missing_warning = Path(tmpdir) / "baseline-missing-warning.json"
        baseline_without_blocker = json.loads(json.dumps(payload))
        baseline_without_warning = json.loads(json.dumps(payload))
        first_blocker = next(
            index for index, finding in enumerate(baseline_without_blocker["findings"]) if finding["level"] == "blocker"
        )
        first_warning = next(
            index for index, finding in enumerate(baseline_without_warning["findings"]) if finding["level"] == "warning"
        )
        del baseline_without_blocker["findings"][first_blocker]
        del baseline_without_warning["findings"][first_warning]
        baseline_missing_blocker.write_text(json.dumps(baseline_without_blocker, indent=2) + "\n", encoding="utf-8")
        baseline_missing_warning.write_text(json.dumps(baseline_without_warning, indent=2) + "\n", encoding="utf-8")

        baseline_aware_new_blocker_env = baseline_aware_action_env.copy()
        baseline_aware_new_blocker_env.update(
            {
                "INPUT_OUT_MD": str(Path(tmpdir) / "VERIFY_ACTION_NEW_BLOCKER_REPORT.md"),
                "INPUT_OUT_JSON": str(Path(tmpdir) / "VERIFY_ACTION_NEW_BLOCKER_REPORT.json"),
                "INPUT_BASELINE_JSON": str(baseline_missing_blocker),
                "INPUT_FAIL_ON_BLOCKERS": "true",
            }
        )
        baseline_aware_new_blocker_result = subprocess.run(
            ["bash", "scripts/action_entrypoint.sh"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=baseline_aware_new_blocker_env,
        )
        if baseline_aware_new_blocker_result.returncode == 0:
            print("Expected baseline-aware action gate to fail on a new blocker.")
            print(baseline_aware_new_blocker_result.stdout)
            print(baseline_aware_new_blocker_result.stderr)
            return 1
        if "Repo preflight found new blockers." not in baseline_aware_new_blocker_result.stdout:
            print("Expected baseline-aware action gate to report new blockers.")
            print(baseline_aware_new_blocker_result.stdout)
            print(baseline_aware_new_blocker_result.stderr)
            return 1

        baseline_aware_report_only_env = baseline_aware_new_blocker_env.copy()
        baseline_aware_report_only_env.update(
            {
                "INPUT_OUT_MD": str(Path(tmpdir) / "VERIFY_ACTION_NEW_BLOCKER_REPORT_ONLY.md"),
                "INPUT_OUT_JSON": str(Path(tmpdir) / "VERIFY_ACTION_NEW_BLOCKER_REPORT_ONLY.json"),
                "INPUT_FAIL_ON_BLOCKERS": "false",
            }
        )
        baseline_aware_report_only_result = subprocess.run(
            ["bash", "scripts/action_entrypoint.sh"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=baseline_aware_report_only_env,
        )
        if baseline_aware_report_only_result.returncode != 0:
            print("Expected baseline-aware action report-only mode to mask new-blocker failure.")
            print(baseline_aware_report_only_result.stdout)
            print(baseline_aware_report_only_result.stderr)
            return 1

        local_action_dir = Path(tmpdir) / "local-action-cwd"
        local_action_dir.mkdir()
        local_action_env = os.environ.copy()
        local_action_env.pop("GITHUB_ACTION_PATH", None)
        local_action_env.update(
            {
                "INPUT_REPO": str(fixture_repo),
                "INPUT_OUT_MD": str(ROOT / "VERIFY_LOCAL_ACTION_REPORT.md"),
                "INPUT_OUT_JSON": str(ROOT / "VERIFY_LOCAL_ACTION_REPORT.json"),
                "INPUT_OUT_HTML": str(ROOT / "VERIFY_LOCAL_ACTION_REPORT.html"),
                "INPUT_OUT_SARIF": str(ROOT / "VERIFY_LOCAL_ACTION_REPORT.sarif"),
                "INPUT_INCLUDE_FIXTURES": "true",
                "INPUT_GITHUB_ANNOTATIONS": "false",
                "INPUT_FAIL_ON_BLOCKERS": "false",
            }
        )
        local_action_result = subprocess.run(
            ["bash", str(ROOT / "scripts/action_entrypoint.sh")],
            cwd=local_action_dir,
            check=False,
            capture_output=True,
            text=True,
            env=local_action_env,
        )
        if local_action_result.returncode != 0:
            print("Expected local action entrypoint without GITHUB_ACTION_PATH to exit 0 in report-only mode.")
            print(local_action_result.stdout)
            print(local_action_result.stderr)
            return 1
        local_action_payload = json.loads((ROOT / "VERIFY_LOCAL_ACTION_REPORT.json").read_text(encoding="utf-8"))
        if not require(local_action_payload["decision"] == "BLOCKED", "Expected local action entrypoint fixture scan to block."):
            return 1
        for path in [
            ROOT / "VERIFY_LOCAL_ACTION_REPORT.md",
            ROOT / "VERIFY_LOCAL_ACTION_REPORT.json",
            ROOT / "VERIFY_LOCAL_ACTION_REPORT.html",
            ROOT / "VERIFY_LOCAL_ACTION_REPORT.sarif",
        ]:
            if not require(path.is_file(), f"Expected local action report output: {path.name}"):
                return 1

        baseline_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--out-md",
                "VERIFY_BASELINE_REPORT.md",
                "--out-json",
                "VERIFY_BASELINE_REPORT.json",
                "--baseline-json",
                "REPORT.json",
                "--include-fixtures",
            ]
        )
        if baseline_result.returncode == 0:
            print("Expected baseline fixture scan to remain blocked.")
            return 1
        baseline_payload = json.loads((ROOT / "VERIFY_BASELINE_REPORT.json").read_text(encoding="utf-8"))
        if not require_json_report_contract(baseline_payload):
            return 1
        if not require(baseline_payload["baseline_diff"]["new"] == 0, "Expected no new findings against identical baseline."):
            return 1

        baseline_aware_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--out-md",
                "VERIFY_BASELINE_AWARE_REPORT.md",
                "--out-json",
                "VERIFY_BASELINE_AWARE_REPORT.json",
                "--baseline-json",
                "REPORT.json",
                "--fail-on-new-blockers-only",
                "--include-fixtures",
            ]
        )
        if baseline_aware_result.returncode != 0:
            print("Expected baseline-aware gate to pass with identical baseline.")
            print(baseline_aware_result.stdout)
            print(baseline_aware_result.stderr)
            return 1
        if "Repo preflight found blockers already present in baseline." not in baseline_aware_result.stdout:
            print("Expected baseline-aware gate to report existing blockers.")
            print(baseline_aware_result.stdout)
            print(baseline_aware_result.stderr)
            return 1

        baseline_aware_new_blocker_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--out-md",
                "VERIFY_BASELINE_NEW_BLOCKER_REPORT.md",
                "--out-json",
                "VERIFY_BASELINE_NEW_BLOCKER_REPORT.json",
                "--baseline-json",
                str(baseline_missing_blocker),
                "--fail-on-new-blockers-only",
                "--include-fixtures",
            ]
        )
        if baseline_aware_new_blocker_result.returncode == 0:
            print("Expected baseline-aware gate to fail on a new blocker.")
            print(baseline_aware_new_blocker_result.stdout)
            print(baseline_aware_new_blocker_result.stderr)
            return 1
        baseline_aware_new_blocker_payload = json.loads(
            (ROOT / "VERIFY_BASELINE_NEW_BLOCKER_REPORT.json").read_text(encoding="utf-8")
        )
        if not require(
            any(finding["level"] == "blocker" for finding in baseline_aware_new_blocker_payload["baseline_diff"]["new_findings"]),
            "Expected baseline-aware report to include a new blocker.",
        ):
            return 1

        baseline_aware_new_warning_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--out-md",
                "VERIFY_BASELINE_NEW_WARNING_REPORT.md",
                "--out-json",
                "VERIFY_BASELINE_NEW_WARNING_REPORT.json",
                "--baseline-json",
                str(baseline_missing_warning),
                "--fail-on-new-blockers-only",
                "--include-fixtures",
            ]
        )
        if baseline_aware_new_warning_result.returncode != 0:
            print("Expected baseline-aware gate to pass on a new non-blocker only.")
            print(baseline_aware_new_warning_result.stdout)
            print(baseline_aware_new_warning_result.stderr)
            return 1
        baseline_aware_new_warning_payload = json.loads(
            (ROOT / "VERIFY_BASELINE_NEW_WARNING_REPORT.json").read_text(encoding="utf-8")
        )
        if not require(
            all(finding["level"] != "blocker" for finding in baseline_aware_new_warning_payload["baseline_diff"]["new_findings"]),
            "Expected new warning baseline report to have no new blockers.",
        ):
            return 1

        paranoid_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(fixture_repo),
                "--out-md",
                "VERIFY_PARANOID_REPORT.md",
                "--out-json",
                "VERIFY_PARANOID_REPORT.json",
                "--paranoid",
                "--redact-pattern",
                "release ready",
                "--include-fixtures",
            ]
        )
        if paranoid_result.returncode == 0:
            print("Expected paranoid fixture scan to remain blocked.")
            return 1
        paranoid_payload = json.loads((ROOT / "VERIFY_PARANOID_REPORT.json").read_text(encoding="utf-8"))
        if not require(
            all(finding.get("evidence") is None for finding in paranoid_payload["findings"]),
            "Expected paranoid report to omit evidence.",
        ):
            return 1
        if not require(
            all("/" not in finding["path"] for finding in paranoid_payload["findings"] if finding["path"] != "."),
            "Expected paranoid report to suppress directory paths.",
        ):
            return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        rule_pack_repo, rule_pack_config = make_rule_pack_fixture(tmpdir)
        rule_pack_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(rule_pack_repo),
                "--config",
                str(rule_pack_config),
                "--out-md",
                "VERIFY_RULE_PACK_REPORT.md",
                "--out-json",
                "VERIFY_RULE_PACK_REPORT.json",
            ]
        )
        if rule_pack_result.returncode == 0:
            print("Expected custom rule-pack fixture to produce blockers.")
            return 1
        rule_pack_payload = json.loads((ROOT / "VERIFY_RULE_PACK_REPORT.json").read_text(encoding="utf-8"))
        rule_pack_codes = {finding["code"] for finding in rule_pack_payload["findings"]}
        expected_rule_pack_codes = {
            "missing_process_file",
            "risky_public_claim",
            "drift_marker",
            "secret_bearing_filename",
            "generated_artifact_dir",
        }
        missing_rule_pack_codes = sorted(expected_rule_pack_codes - rule_pack_codes)
        if missing_rule_pack_codes:
            print("Missing expected custom rule-pack finding codes:")
            for code in missing_rule_pack_codes:
                print(f"- {code}")
            return 1
        rule_pack_paths = {finding["path"] for finding in rule_pack_payload["findings"]}
        if any(path.startswith("ignored-zone/") or path == "ignored.md" for path in rule_pack_paths):
            print("Expected configured excluded paths to be skipped.")
            return 1
        if "DO_NOT_LEAK_RULE_PACK_SECRET" in json.dumps(rule_pack_payload):
            print("Custom secret-bearing file content leaked into rule-pack report.")
            return 1

        identity_repo = Path(tmpdir) / "identity-profile-repo"
        identity_repo.mkdir()
        for name in ["SPEC.md", "VERIFICATION_PLAN.md", "PRE_RELEASE_CHECKLIST.md"]:
            (identity_repo / name).write_text(f"# {name}\n\nBaseline process file.\n", encoding="utf-8")
        public_identity = "Caa" + "ren Amirian"
        (identity_repo / "README.md").write_text(f"# {public_identity}\n\nPublic profile README.\n", encoding="utf-8")
        (identity_repo / "LICENSE").write_text(f"Copyright (c) 2026 {public_identity}\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=identity_repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "add", "."], cwd=identity_repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.com",
                "commit",
                "-m",
                "fixture",
            ],
            cwd=identity_repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        identity_config = Path(tmpdir) / "identity-rule-pack.json"
        identity_config.write_text(
            json.dumps(
                {"public_sensitive_term_allowlist": ["caa" + "ren", "caa" + "ren amirian"]},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        identity_result = run(
            [
                sys.executable,
                "repo_preflight.py",
                "--repo",
                str(identity_repo),
                "--profile",
                "public-export",
                "--config",
                str(identity_config),
                "--out-md",
                "VERIFY_IDENTITY_PROFILE_REPORT.md",
                "--out-json",
                "VERIFY_IDENTITY_PROFILE_REPORT.json",
            ]
        )
        if identity_result.returncode != 0:
            print("Expected identity profile allowlist scan to pass.")
            return 1

    self_result = run(
        [
            sys.executable,
            "repo_preflight.py",
            "--repo",
            ".",
            "--out-md",
            "VERIFY_SELF_REPORT.md",
            "--out-json",
            "VERIFY_SELF_REPORT.json",
            "--out-html",
            "VERIFY_SELF_REPORT.html",
        ]
    )
    if self_result.returncode != 0:
        print("Expected scanner product folder to pass strict self-scan.")
        print(self_result.stdout)
        print(self_result.stderr)
        return 1
    self_payload = json.loads((ROOT / "VERIFY_SELF_REPORT.json").read_text(encoding="utf-8"))
    if not require(self_payload.get("schema_version") == "1.0", "Expected schema_version in self-scan report."):
        return 1
    if not require_json_report_contract(self_payload):
        return 1
    if not require(self_payload["decision"] == "READY", "Expected READY self-scan decision."):
        return 1
    if not require(self_payload["counts"] == {"blocker": 0, "warning": 0, "info": 0}, "Expected empty self-scan counts."):
        return 1

    public_export_result = run(
        [
            sys.executable,
            "repo_preflight.py",
            "--repo",
            ".",
            "--profile",
            "public-export",
            "--paranoid",
            "--out-md",
            "VERIFY_PUBLIC_EXPORT_REPORT.md",
            "--out-json",
            "VERIFY_PUBLIC_EXPORT_REPORT.json",
        ]
    )
    if public_export_result.returncode != 0:
        print("Expected scanner product folder to pass public-export self-scan.")
        print(public_export_result.stdout)
        print(public_export_result.stderr)
        return 1
    public_export_payload = json.loads((ROOT / "VERIFY_PUBLIC_EXPORT_REPORT.json").read_text(encoding="utf-8"))
    if not require(public_export_payload["decision"] == "READY", "Expected READY public-export self-scan decision."):
        return 1

    docs_result = run(
        [
            sys.executable,
            "repo_preflight.py",
            "--repo",
            ".",
            "--profile",
            "docs",
            "--out-md",
            "VERIFY_OPPORTUNITY_BOARD_DOCS_REPORT.md",
            "--out-json",
            "VERIFY_OPPORTUNITY_BOARD_DOCS_REPORT.json",
            "--config",
            "configs/founder-strict.json",
        ]
    )
    if docs_result.returncode != 0:
        print("Expected opportunity-board docs profile scan to pass.")
        print(docs_result.stdout)
        print(docs_result.stderr)
        return 1
    docs_payload = json.loads((ROOT / "VERIFY_OPPORTUNITY_BOARD_DOCS_REPORT.json").read_text(encoding="utf-8"))
    if not require(docs_payload["profile"] == "docs", "Expected docs profile in docs report."):
        return 1

    if not verify_profile_and_output_coverage():
        return 1

    if not verify_dora_ai_readiness_profile():
        return 1

    if not verify_dora_ai_readiness_action():
        return 1

    if not verify_fieldheld_portfolio_profile():
        return 1

    if not verify_cli_error_handling():
        return 1

    if not verify_cli_profile_discovery():
        return 1

    if not verify_json_schema_artifact():
        return 1

    if not verify_release_package_boundary():
        return 1

    if not verify_source_boundary():
        return 1

    compile_result = run([sys.executable, "-m", "py_compile", "repo_preflight.py", "verify_scanner.py"])
    if compile_result.returncode != 0:
        print(compile_result.stderr)
        return 1

    print("Repo preflight scanner verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
