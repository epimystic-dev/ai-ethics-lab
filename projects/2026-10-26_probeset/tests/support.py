"""Test helpers shared across the probeset suite."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Optional

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
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, "-m", "probeset"] + list(args)
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
    )
    return CliResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
