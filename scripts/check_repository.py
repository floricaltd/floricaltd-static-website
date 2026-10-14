#!/usr/bin/env python3
"""Fail closed on repository hygiene, secret, and workflow pin checks."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/pages.yml"
SECRET_PATTERNS = (
    re.compile("gh" + "p_[A-Za-z0-9]{20,}"),
    re.compile("github" + "_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"""(?i)(?:api[_-]?key|password|secret)\s*[:=]\s*["'][^"'\n]{8,}"""),
)
FORBIDDEN_PARTS = {"__pycache__", ".venv", "node_modules"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def assert_no_secrets(label: str, content: str) -> None:
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        raise SystemExit(f"{label}: potential credential pattern detected (content suppressed)")


def main() -> None:
    tracked = [Path(line) for line in git("ls-files").splitlines()]
    forbidden = [
        path.as_posix()
        for path in tracked
        if FORBIDDEN_PARTS.intersection(path.parts) or path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden:
        raise SystemExit(f"forbidden tracked artifacts: {', '.join(forbidden)}")

    for path in tracked:
        try:
            content = (ROOT / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert_no_secrets(f"tracked file {path}", content)
    assert_no_secrets("reachable Git history", git("log", "-p", "--all", "--no-ext-diff"))

    workflow = WORKFLOW.read_text(encoding="utf-8")
    pins = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, flags=re.MULTILINE)
    if not pins or any(not re.fullmatch(r"[^/@\s]+/[^@\s]+@[0-9a-f]{40}", pin) for pin in pins):
        raise SystemExit(f"all workflow actions must use full commit SHAs: {pins}")
    if "workflow_dispatch:" in workflow:
        raise SystemExit("arbitrary-ref workflow_dispatch is forbidden")
    if not re.search(r"^permissions:\s*\{\}\s*$", workflow, flags=re.MULTILINE):
        raise SystemExit("top-level workflow permissions must be empty")
    print(f"repository checks passed: {len(tracked)} tracked files, full reachable history, {len(pins)} action pins")


if __name__ == "__main__":
    main()
