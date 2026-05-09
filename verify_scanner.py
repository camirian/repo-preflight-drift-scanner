#!/usr/bin/env python3
"""Verify the repo preflight drift scanner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


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


def main() -> int:
    action_metadata = (ROOT / "action.yml").read_text(encoding="utf-8")
    if not require("using: composite" in action_metadata, "Expected composite action metadata."):
        return 1
    if not require("scripts/action_entrypoint.sh" in action_metadata, "Expected action to use tested shell entrypoint."):
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
            ["scripts/action_entrypoint.sh"],
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
        if not require(baseline_payload["baseline_diff"]["new"] == 0, "Expected no new findings against identical baseline."):
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

    compile_result = run([sys.executable, "-m", "py_compile", "repo_preflight.py", "verify_scanner.py"])
    if compile_result.returncode != 0:
        print(compile_result.stderr)
        return 1

    print("Repo preflight scanner verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
