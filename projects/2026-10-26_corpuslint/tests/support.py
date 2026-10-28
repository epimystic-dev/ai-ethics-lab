"""Test helpers shared across the suite.

Importable as `from tests.support import ...`. Keep no non-ASCII in this file."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")


def example(name: str) -> str:
    return os.path.join(EXAMPLES_DIR, name)


@dataclass
class CliResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def run_cli(*args: str, env_extra: Optional[Dict[str, str]] = None) -> CliResult:
    """Invoke `python -m corpuslint ...` as a real subprocess so the shared
    contract tests exercise the actual entry point."""
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, "-m", "corpuslint"] + list(args)
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
    )
    return CliResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def load_example(name: str) -> dict:
    with open(example(name), "r", encoding="utf-8") as fh:
        return json.load(fh)
