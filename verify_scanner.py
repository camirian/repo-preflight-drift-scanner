#!/usr/bin/env python3
"""Verify the repo preflight drift scanner."""

from __future__ import annotations

import json
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
        "README-for-buyers.md",
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
        "buyer-license.txt",
        "docs/report-schema.md",
        "docs/rule-packs.md",
        "docs/buyer/quickstart.md",
        "docs/buyer/local-cli-setup.md",
        "docs/buyer/github-action-setup.md",
        "docs/buyer/how-to-use-the-kit.md",
        "docs/buyer/sample-report-walkthrough.md",
        "docs/buyer/what-this-is-not.md",
        "examples/github-action.yml",
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
            print("Expected package script to build buyer ZIP.")
            print(package_result.stdout)
            print(package_result.stderr)
            return False

        zip_path = package_root / "release" / f"{package_name}.zip"
        if not require(zip_path.is_file(), "Expected buyer ZIP to be created."):
            return False

        with ZipFile(zip_path) as zf:
            manifest = sorted(name for name in zf.namelist() if not name.endswith("/"))

            for name in manifest:
                parts = PurePosixPath(name).parts
                if name.startswith("/") or ".." in parts:
                    print(f"Unsafe ZIP member path: {name}")
                    return False
                if ".git" in parts:
                    print(f"Unexpected .git content in buyer ZIP: {name}")
                    return False

            prefix = f"{package_name}/"
            if not require(
                all(name.startswith(prefix) for name in manifest),
                "Expected all ZIP members under package directory.",
            ):
                return False

            packaged_files = {name.removeprefix(prefix) for name in manifest}
            missing_files = sorted(required_files - packaged_files)
            if missing_files:
                print("Missing required buyer package files:")
                for path in missing_files:
                    print(f"- {path}")
                return False

            forbidden_files = sorted(
                path
                for path in packaged_files
                if path in forbidden_exact or path.startswith("docs/marketing/")
            )
            if forbidden_files:
                print("Seller/admin files leaked into buyer package:")
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
                print("Generated report files leaked into buyer package:")
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
        if not require(demo_payload["decision"] == "BLOCKED", "Expected extracted CLI demo report to be BLOCKED."):
            return False

    return True


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

        if payload.get("schema_version") != "1.0":
            print("Expected JSON schema_version 1.0.")
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

    if not verify_cli_error_handling():
        return 1

    if not verify_release_package_boundary():
        return 1

    compile_result = run([sys.executable, "-m", "py_compile", "repo_preflight.py", "verify_scanner.py"])
    if compile_result.returncode != 0:
        print(compile_result.stderr)
        return 1

    print("Repo preflight scanner verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
