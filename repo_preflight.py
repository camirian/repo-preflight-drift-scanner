#!/usr/bin/env python3
"""Local repo preflight/drift scanner.

This tool is intentionally deterministic, local, read-only, and dependency-free.
It is not a security or compliance scanner.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

TEXT_FILENAMES = {
    "AUTHORS",
    "LICENSE",
    "NOTICE",
}

PROFILES = {
    "strict": {
        "check_process_files": True,
        "check_checkboxes": True,
        "check_risky_claims": True,
        "check_drift_markers": True,
        "check_generated_artifacts": True,
        "check_public_export": False,
    },
    "docs": {
        "check_process_files": False,
        "check_checkboxes": False,
        "check_risky_claims": False,
        "check_drift_markers": False,
        "check_generated_artifacts": False,
        "check_public_export": False,
    },
    "public-export": {
        "check_process_files": True,
        "check_checkboxes": True,
        "check_risky_claims": True,
        "check_drift_markers": True,
        "check_generated_artifacts": True,
        "check_public_export": True,
    },
}

SECRET_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

GENERATED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
}

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}

DEFAULT_EXCLUDED_FILES = {
    "REPORT.md",
    "REPORT.json",
    "REPORT.html",
    "REPORT.sarif",
    "SELF_REPORT.md",
    "SELF_REPORT.json",
    "SELF_REPORT.html",
    "SELF_REPORT.sarif",
    "REPO_PREFLIGHT_REPORT.md",
    "REPO_PREFLIGHT_REPORT.json",
    "REPO_PREFLIGHT_REPORT.html",
    "REPO_PREFLIGHT_REPORT.sarif",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}

REQUIRED_PROCESS_FILES = {
    "README": ["README.md"],
    "SPEC": ["SPEC.md", "docs/SPEC.md"],
    "VERIFICATION_PLAN": ["VERIFICATION_PLAN.md", "docs/VERIFICATION_PLAN.md"],
    "PRE_RELEASE_CHECKLIST": [
        "PRE_RELEASE_CHECKLIST.md",
        "PRE_RELEASE_PREFLIGHT.md",
        "PUBLIC_RELEASE_SCRUB.md",
        "docs/PRE_RELEASE_CHECKLIST.md",
    ],
}

RISKY_CLAIMS = [
    "production ready",
    "production-ready",
    "guaranteed savings",
    "guarantees savings",
    "hipaa compliant",
    "hipaa-compliant",
    "security certified",
    "compliance guaranteed",
    "replaces human review",
]

DRIFT_MARKERS = [
    "todo",
    "fixme",
    "tbd",
    "placeholder",
    "replace this",
]

PUBLIC_EXPORT_PRIVATE_PATH_TERMS = [
    "career-vault",
    "launch-plan",
    "launch_notes",
    "launch_plan",
    "low_key_clearance",
    "monetization",
    "opportunity-board/outreach",
    "pricing",
    "private-notes",
    "side_business",
    "sister_",
    "strategy-vault",
    "terminal_handoff",
]

PUBLIC_EXPORT_PRIVATE_FILE_NAMES = {
    "HANDOFF.md",
    "LAUNCH.md",
    "MONETIZATION_NOTES.md",
    "PRODUCT_LISTING.md",
    "terminal_handoff.md",
}

PUBLIC_EXPORT_SENSITIVE_TERMS = [
    "642 uclan",
    "burbank ca",
    "caaren",
    "caaren amirian",
    "clearance",
    "cui",
    "export control",
    "itar",
    "northrop",
    "grumman",
]

SECRET_LITERAL_PATTERNS = {
    "private_key_literal": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "github_token_literal": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "openai_key_literal": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key_literal": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "personal_email_literal": re.compile(
        r"\b[A-Za-z0-9._%+-]+@(gmail|outlook|hotmail|yahoo|icloud|proton)\.com\b",
        re.IGNORECASE,
    ),
}

MAX_TEXT_BYTES = 300_000
CONFIG_LIST_KEYS = {
    "risky_claims",
    "drift_markers",
    "secret_filenames",
    "generated_dirs",
    "excluded_dirs",
    "excluded_files",
}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str
    line: int | None = None
    evidence: str | None = None


@dataclass(frozen=True)
class ScanConfig:
    required_process_files: dict[str, list[str]]
    risky_claims: set[str]
    drift_markers: set[str]
    secret_filenames: set[str]
    generated_dirs: set[str]
    excluded_dirs: set[str]
    excluded_files: set[str]


@dataclass(frozen=True)
class ReportOptions:
    no_evidence: bool = False
    max_evidence_chars: int = 180
    path_mode: str = "relative"
    redactors: tuple[re.Pattern[str], ...] = ()


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in TEXT_FILENAMES


def read_text(path: Path) -> str | None:
    if path.stat().st_size > MAX_TEXT_BYTES:
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def line_findings(
    root: Path,
    path: Path,
    text: str,
    terms: list[str],
    level: str,
    code: str,
    message_prefix: str,
) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for term in terms:
            if term in lowered:
                findings.append(
                    Finding(
                        level=level,
                        code=code,
                        path=relative(path, root),
                        line=number,
                        message=f"{message_prefix}: {term}",
                        evidence=line.strip()[:180],
                    )
                )
                break
    return findings


def secret_literal_findings(root: Path, path: Path, text: str) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for code, pattern in SECRET_LITERAL_PATTERNS.items():
            if pattern.search(line):
                findings.append(
                    Finding(
                        level="blocker",
                        code=code,
                        path=relative(path, root),
                        line=number,
                        message="High-confidence secret literal detected. Evidence suppressed.",
                    )
                )
                break
    return findings


def public_export_path_findings(rel: str, path: Path) -> list[Finding]:
    lowered = rel.lower()
    findings = []
    if path.name in PUBLIC_EXPORT_PRIVATE_FILE_NAMES or any(term in lowered for term in PUBLIC_EXPORT_PRIVATE_PATH_TERMS):
        findings.append(
            Finding(
                level="blocker",
                code="private_publication_surface",
                path=rel,
                message="Private strategy/planning path should not be in a public export.",
            )
        )
    if path.suffix.lower() in {".md", ".json", ".html", ".sarif"} and path.stem.lower().endswith("_report"):
        findings.append(
            Finding(
                level="blocker",
                code="generated_report_tracked",
                path=rel,
                message="Generated scanner report should not be in a public export.",
            )
        )
    return findings


def tracked_files(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def git_history_findings(root: Path) -> list[Finding]:
    if not (root / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    try:
        commit_count = int(result.stdout.strip())
    except ValueError:
        return []
    if commit_count <= 1:
        return []
    return [
        Finding(
            level="warning",
            code="public_history_requires_audit",
            path=".",
            message=f"Repository has {commit_count} commits; audit history before public release.",
        )
    ]


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[str] = set()
    unique = []
    for finding in findings:
        key = finding_key(finding)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


def default_config() -> ScanConfig:
    return ScanConfig(
        required_process_files={label: list(candidates) for label, candidates in REQUIRED_PROCESS_FILES.items()},
        risky_claims=set(RISKY_CLAIMS),
        drift_markers=set(DRIFT_MARKERS),
        secret_filenames=set(SECRET_FILENAMES),
        generated_dirs=set(GENERATED_DIRS),
        excluded_dirs=set(DEFAULT_EXCLUDED_DIRS),
        excluded_files=set(DEFAULT_EXCLUDED_FILES),
    )


def list_value(raw: object, key: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"Config key {key!r} must be a list of strings")
    return raw


def load_config(paths: list[Path]) -> ScanConfig:
    config = default_config()
    required = {label: list(candidates) for label, candidates in config.required_process_files.items()}
    risky_claims = set(config.risky_claims)
    drift_markers = set(config.drift_markers)
    secret_filenames = set(config.secret_filenames)
    generated_dirs = set(config.generated_dirs)
    excluded_dirs = set(config.excluded_dirs)
    excluded_files = set(config.excluded_files)

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Config file {path} must contain a JSON object")

        unknown = sorted(set(payload) - (CONFIG_LIST_KEYS | {"required_process_files"}))
        if unknown:
            raise ValueError(f"Unknown config key(s) in {path}: {', '.join(unknown)}")

        risky_claims.update(term.lower() for term in list_value(payload.get("risky_claims"), "risky_claims"))
        drift_markers.update(term.lower() for term in list_value(payload.get("drift_markers"), "drift_markers"))
        secret_filenames.update(term.lower() for term in list_value(payload.get("secret_filenames"), "secret_filenames"))
        generated_dirs.update(list_value(payload.get("generated_dirs"), "generated_dirs"))
        excluded_dirs.update(list_value(payload.get("excluded_dirs"), "excluded_dirs"))
        excluded_files.update(list_value(payload.get("excluded_files"), "excluded_files"))

        required_payload = payload.get("required_process_files", {})
        if not isinstance(required_payload, dict):
            raise ValueError(f"Config key 'required_process_files' in {path} must be an object")
        for label, candidates in required_payload.items():
            if not isinstance(label, str):
                raise ValueError(f"Required process file label in {path} must be a string")
            required[label] = list_value(candidates, f"required_process_files.{label}")

    return ScanConfig(
        required_process_files=required,
        risky_claims=risky_claims,
        drift_markers=drift_markers,
        secret_filenames=secret_filenames,
        generated_dirs=generated_dirs,
        excluded_dirs=excluded_dirs,
        excluded_files=excluded_files,
    )


def should_skip(path: Path, root: Path, include_fixtures: bool, config: ScanConfig) -> bool:
    rel_parts = path.relative_to(root).parts
    if not include_fixtures and any(
        rel_parts[index : index + 2] == ("examples", "sample-repo")
        for index in range(max(len(rel_parts) - 1, 0))
    ):
        return True
    if any(part in config.excluded_dirs for part in rel_parts):
        return True
    if path.name in config.excluded_files:
        return True
    if path.suffix.lower() in {".md", ".json", ".html", ".sarif"} and path.stem.lower().endswith("_report"):
        return True
    return False


def scan_repo(
    root: Path,
    include_fixtures: bool = False,
    profile: str = "strict",
    config: ScanConfig | None = None,
) -> list[Finding]:
    root = root.resolve()
    config = config or default_config()
    profile_settings = PROFILES[profile]
    findings: list[Finding] = []

    if profile_settings["check_public_export"]:
        findings.extend(git_history_findings(root))
        for rel in tracked_files(root):
            findings.extend(public_export_path_findings(rel, root / rel))
            name = Path(rel).name.lower()
            suffix = Path(rel).suffix.lower()
            if name in config.secret_filenames or suffix in {".pem", ".key", ".p12"}:
                findings.append(
                    Finding(
                        level="blocker",
                        code="tracked_secret_bearing_filename",
                        path=rel,
                        message="Secret-bearing filename is tracked by git. Contents were not read.",
                    )
                )

    if profile_settings["check_process_files"]:
        for label, candidates in config.required_process_files.items():
            if not any((root / candidate).exists() for candidate in candidates):
                findings.append(
                    Finding(
                        level="blocker",
                        code="missing_process_file",
                        path=".",
                        message=f"Missing process file: {label}",
                        evidence=", ".join(candidates),
                    )
                )

    for path in sorted(root.rglob("*")):
        if should_skip(path, root, include_fixtures, config):
            continue
        if path.is_symlink():
            continue
        rel = relative(path, root)
        name = path.name

        if profile_settings["check_public_export"]:
            findings.extend(public_export_path_findings(rel, path))

        if path.is_dir():
            if profile_settings["check_generated_artifacts"] and name in config.generated_dirs:
                findings.append(
                    Finding(
                        level="warning",
                        code="generated_artifact_dir",
                        path=rel,
                        message="Generated/cache directory present; keep out of release artifacts unless intentionally included.",
                    )
                )
            continue

        if name.lower() in config.secret_filenames or path.suffix.lower() in {".pem", ".key", ".p12"}:
            findings.append(
                Finding(
                    level="blocker",
                    code="secret_bearing_filename",
                    path=rel,
                    message="Secret-bearing filename detected. Contents were not read.",
                )
            )
            continue

        if not is_text_candidate(path):
            continue

        text = read_text(path)
        if text is None:
            findings.append(
                Finding(
                    level="info",
                    code="large_text_file_skipped",
                    path=rel,
                    message=f"Text file over {MAX_TEXT_BYTES} bytes skipped.",
                )
            )
            continue

        if profile_settings["check_public_export"] and path.name != "repo_preflight.py":
            findings.extend(secret_literal_findings(root, path, text))
            findings.extend(
                line_findings(
                    root,
                    path,
                    text,
                    PUBLIC_EXPORT_SENSITIVE_TERMS,
                    "blocker",
                    "public_sensitive_term",
                    "Sensitive public-export term",
                )
            )

        if path.name != "repo_preflight.py" and profile_settings["check_risky_claims"]:
            findings.extend(
                line_findings(
                    root,
                    path,
                    text,
                    sorted(config.risky_claims),
                    "blocker",
                    "risky_public_claim",
                    "Risky public claim",
                )
            )
        if path.name != "repo_preflight.py" and profile_settings["check_drift_markers"]:
            findings.extend(
                line_findings(
                    root,
                    path,
                    text,
                    sorted(config.drift_markers),
                    "warning",
                    "drift_marker",
                    "Possible AI/process drift marker",
                )
            )

        if profile_settings["check_checkboxes"]:
            for number, line in enumerate(text.splitlines(), start=1):
                if re.search(r"^\s*[-*]\s+\[\s\]\s+", line):
                    findings.append(
                        Finding(
                            level="blocker",
                            code="unchecked_release_gate",
                            path=rel,
                            line=number,
                            message="Unchecked checklist item remains.",
                            evidence=line.strip()[:180],
                        )
                    )

    return dedupe_findings(findings)


def decision(findings: list[Finding]) -> str:
    return "BLOCKED" if any(finding.level == "blocker" for finding in findings) else "READY"


def finding_counts(findings: list[Finding]) -> dict[str, int]:
    return {
        "blocker": sum(f.level == "blocker" for f in findings),
        "warning": sum(f.level == "warning" for f in findings),
        "info": sum(f.level == "info" for f in findings),
    }


def redact_text(text: str | None, options: ReportOptions) -> str | None:
    if text is None or options.no_evidence:
        return None
    value = text[: max(options.max_evidence_chars, 0)]
    for pattern in options.redactors:
        value = pattern.sub("[REDACTED]", value)
    return value


def report_path(path: str, options: ReportOptions) -> str:
    if options.path_mode == "basename":
        return Path(path).name if path != "." else "."
    if options.path_mode == "hash":
        digest = hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]
        suffix = Path(path).suffix
        return f"path-{digest}{suffix}"
    return path


def prepare_findings_for_report(findings: list[Finding], options: ReportOptions) -> list[Finding]:
    return [
        Finding(
            level=finding.level,
            code=finding.code,
            path=report_path(finding.path, options),
            message=finding.message,
            line=finding.line,
            evidence=redact_text(finding.evidence, options),
        )
        for finding in findings
    ]


def finding_key(finding: Finding) -> str:
    return "|".join(
        [
            finding.level,
            finding.code,
            finding.path,
            str(finding.line or ""),
            finding.message,
            finding.evidence or "",
        ]
    )


def diff_against_baseline(findings: list[Finding], baseline_path: Path | None) -> dict[str, int | list[dict[str, object]]]:
    if baseline_path is None:
        return {"new": 0, "resolved": 0, "new_findings": [], "resolved_findings": []}
    baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_findings = [Finding(**finding) for finding in baseline_payload.get("findings", [])]
    current_by_key = {finding_key(finding): finding for finding in findings}
    baseline_by_key = {finding_key(finding): finding for finding in baseline_findings}
    new = [current_by_key[key] for key in sorted(set(current_by_key) - set(baseline_by_key))]
    resolved = [baseline_by_key[key] for key in sorted(set(baseline_by_key) - set(current_by_key))]
    return {
        "new": len(new),
        "resolved": len(resolved),
        "new_findings": [asdict(finding) for finding in new],
        "resolved_findings": [asdict(finding) for finding in resolved],
    }


def render_markdown(
    repo: Path,
    findings: list[Finding],
    profile: str,
    baseline_diff: dict[str, int | list[dict[str, object]]] | None = None,
) -> str:
    counts = finding_counts(findings)
    lines = [
        "# Repo Preflight Report",
        "",
        f"Repo: `{repo}`",
        f"Profile: `{profile}`",
        f"Decision: {decision(findings)}",
        "",
        "## Summary",
        "",
        f"- Blockers: {counts['blocker']}",
        f"- Warnings: {counts['warning']}",
        f"- Info: {counts['info']}",
        "",
    ]
    if baseline_diff is not None:
        lines.extend(
            [
                "## Baseline Diff",
                "",
                f"- New findings: {baseline_diff['new']}",
                f"- Resolved findings: {baseline_diff['resolved']}",
                "",
            ]
        )
    lines.extend(["## Findings", ""])
    if not findings:
        lines.append("No findings.")
    for finding in findings:
        location = finding.path
        if finding.line is not None:
            location = f"{location}:{finding.line}"
        lines.append(f"- **{finding.level.upper()}** `{finding.code}` at `{location}`: {finding.message}")
        if finding.evidence:
            lines.append(f"  - Evidence: {finding.evidence}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is not a security scanner, compliance scanner, vulnerability scanner, or replacement for human review.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(repo: Path, findings: list[Finding], profile: str) -> str:
    counts = finding_counts(findings)
    rows = []
    for finding in findings:
        location = finding.path if finding.line is None else f"{finding.path}:{finding.line}"
        rows.append(
            "<tr>"
            f"<td>{html.escape(finding.level)}</td>"
            f"<td>{html.escape(finding.code)}</td>"
            f"<td>{html.escape(location)}</td>"
            f"<td>{html.escape(finding.message)}</td>"
            f"<td>{html.escape(finding.evidence or '')}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="5">No findings.</td></tr>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Repo Preflight Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d1d5db; padding: 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
  <h1>Repo Preflight Report</h1>
  <p><strong>Repo:</strong> <code>{html.escape(str(repo))}</code></p>
  <p><strong>Profile:</strong> <code>{html.escape(profile)}</code></p>
  <p><strong>Decision:</strong> {decision(findings)}</p>
  <ul>
    <li>Blockers: {counts['blocker']}</li>
    <li>Warnings: {counts['warning']}</li>
    <li>Info: {counts['info']}</li>
  </ul>
  <table>
    <thead><tr><th>Level</th><th>Code</th><th>Location</th><th>Message</th><th>Evidence</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p>This is not a security scanner, compliance scanner, vulnerability scanner, or replacement for human review.</p>
</body>
</html>
"""


def sarif_level(finding: Finding) -> str:
    if finding.level == "blocker":
        return "error"
    if finding.level == "warning":
        return "warning"
    return "note"


def write_sarif(repo: Path, findings: list[Finding], output_path: Path) -> None:
    rules = {}
    for finding in findings:
        rules.setdefault(
            finding.code,
            {
                "id": finding.code,
                "name": finding.code,
                "shortDescription": {"text": finding.message.split(":", 1)[0]},
            },
        )
    results = []
    for finding in findings:
        region = {}
        if finding.line is not None:
            region["startLine"] = finding.line
        results.append(
            {
                "ruleId": finding.code,
                "level": sarif_level(finding),
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.path},
                            **({"region": region} if region else {}),
                        }
                    }
                ],
            }
        )
    payload = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Repo Preflight Drift Scanner",
                        "informationUri": "https://github.com/camirian/repo-preflight-drift-scanner",
                        "rules": list(rules.values()),
                    }
                },
                "originalUriBaseIds": {"ROOTPATH": {"uri": repo.resolve().as_uri() + "/"}},
                "results": results,
            }
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def emit_github_annotations(findings: list[Finding]) -> None:
    for finding in findings:
        command = "error" if finding.level == "blocker" else "warning" if finding.level == "warning" else "notice"
        fields = [f"file={finding.path}"]
        if finding.line is not None:
            fields.append(f"line={finding.line}")
        fields.append(f"title={finding.code}")
        message = finding.message
        if finding.evidence:
            message = f"{message} | {finding.evidence}"
        safe_message = message.replace("\n", " ").replace("\r", " ")
        print(f"::{command} {','.join(fields)}::{safe_message}", file=sys.stderr)


def write_json(
    repo: Path,
    findings: list[Finding],
    output_path: Path,
    profile: str,
    baseline_diff: dict[str, int | list[dict[str, object]]] | None = None,
) -> None:
    counts = finding_counts(findings)
    payload = {
        "repo": str(repo),
        "profile": profile,
        "decision": decision(findings),
        "counts": counts,
        "findings": [asdict(finding) for finding in findings],
    }
    if baseline_diff is not None:
        payload["baseline_diff"] = baseline_diff
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repo for release preflight/drift findings")
    parser.add_argument("--repo", default=Path("."), type=Path)
    parser.add_argument("--out-md", default=Path("REPO_PREFLIGHT_REPORT.md"), type=Path)
    parser.add_argument("--out-json", default=Path("REPO_PREFLIGHT_REPORT.json"), type=Path)
    parser.add_argument("--out-html", type=Path)
    parser.add_argument("--out-sarif", type=Path)
    parser.add_argument("--baseline-json", type=Path)
    parser.add_argument("--config", action="append", default=[], type=Path, help="JSON rule-pack config; may be repeated")
    parser.add_argument("--include-fixtures", action="store_true", help="include examples/sample-repo fixture findings")
    parser.add_argument("--github-annotations", action="store_true", help="emit GitHub workflow annotations")
    parser.add_argument("--paranoid", action="store_true", help="privacy-first reports: basename paths and no evidence snippets")
    parser.add_argument("--no-evidence", action="store_true", help="omit evidence snippets from reports and annotations")
    parser.add_argument("--max-evidence-chars", default=180, type=int)
    parser.add_argument("--redact-pattern", action="append", default=[], help="regex pattern to redact from evidence snippets; may be repeated")
    parser.add_argument("--path-mode", choices=["relative", "basename", "hash"], default="relative")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="strict")
    args = parser.parse_args()

    config = load_config(args.config)
    findings = scan_repo(args.repo, include_fixtures=args.include_fixtures, profile=args.profile, config=config)
    path_mode = "basename" if args.paranoid and args.path_mode == "relative" else args.path_mode
    report_options = ReportOptions(
        no_evidence=args.no_evidence or args.paranoid,
        max_evidence_chars=args.max_evidence_chars,
        path_mode=path_mode,
        redactors=tuple(re.compile(pattern) for pattern in args.redact_pattern),
    )
    report_findings = prepare_findings_for_report(findings, report_options)
    baseline_diff = diff_against_baseline(report_findings, args.baseline_json) if args.baseline_json else None
    args.out_md.write_text(render_markdown(args.repo, report_findings, args.profile, baseline_diff), encoding="utf-8")
    write_json(args.repo, report_findings, args.out_json, args.profile, baseline_diff)
    if args.out_html:
        args.out_html.write_text(render_html(args.repo, report_findings, args.profile), encoding="utf-8")
    if args.out_sarif:
        write_sarif(args.repo, report_findings, args.out_sarif)
    if args.github_annotations:
        emit_github_annotations(report_findings)

    if decision(findings) == "BLOCKED":
        print("Repo preflight found blockers.")
        return 1
    print("Repo preflight ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
