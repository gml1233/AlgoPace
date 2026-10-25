"""Wrapper for `manim-lint` CLI: static checks on generated Manim code without rendering."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass
class LintDiagnostic:
    """Single diagnostic from manim-lint."""

    code: str
    message: str
    severity: str
    file_path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class LintReport:
    """Result of running manim-lint on a snippet written to a temp file."""

    success: bool
    diagnostics: List[LintDiagnostic]
    raw_stdout: str = ""
    raw_stderr: str = ""
    exit_code: int = 0
    manim_version: Optional[str] = None
    cli_error: Optional[str] = None

    def has_errors(self) -> bool:
        return any(d.severity.lower() == "error" for d in self.diagnostics)


def _build_lint_command(py_path: str, geometry: str) -> tuple[list[str], Optional[dict[str, str]]]:
    """
    Return argv and optional extra env for subprocess.
    Prefer `manim-lint` on PATH; else `python -m manim_linter.cli` with PYTHONPATH.
    """
    root = _project_root()
    src = root / "third_party" / "manim-linter" / "src"
    # CLI: manim-lint <path> [--json] [--occlusion-geometry ...]
    tail = [py_path, "--json", "--occlusion-geometry", geometry]

    exe = shutil.which("manim-lint")
    if exe:
        return [exe, *tail], None

    if src.is_dir():
        env_extra = {"PYTHONPATH": os.pathsep.join(filter(None, [str(src), os.environ.get("PYTHONPATH", "")]))}
        return [sys.executable, "-m", "manim_linter.cli", *tail], env_extra

    return [], None


def _parse_diagnostic(raw: dict[str, Any]) -> LintDiagnostic:
    sev = raw.get("severity", "info")
    if not isinstance(sev, str):
        sev = str(sev)
    return LintDiagnostic(
        code=str(raw.get("code", "")),
        message=str(raw.get("message", "")),
        severity=sev,
        file_path=raw.get("file_path"),
        line=raw.get("line"),
        column=raw.get("column"),
    )


def lint_manim_code(
    code: str,
    *,
    save_to: Optional[Path] = None,
    geometry: str = "manim_points",
    timeout: int = 60,
    project_root: Optional[Path] = None,
) -> LintReport:
    """
    Run `manim-lint` on a Python string (written to a temp file).

    If the CLI is unavailable and the submodule src/ is missing, returns success=True
    with empty diagnostics so the pipeline can still render.
    """
    logger = logging.getLogger(__name__)
    root = project_root or _project_root()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        cmd, env_extra = _build_lint_command(temp_path, geometry)
        if not cmd:
            msg = "manim-lint not found and third_party/manim-linter/src missing; skipping lint"
            logger.warning(msg)
            return LintReport(success=True, diagnostics=[], cli_error=msg)

        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(root),
            env=env,
        )

        out = proc.stdout or ""
        err = proc.stderr or ""

        if save_to is not None:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            combined = {
                "exit_code": proc.returncode,
                "stdout": out,
                "stderr": err,
            }
            if out.strip():
                try:
                    combined["payload"] = json.loads(out)
                except json.JSONDecodeError:
                    combined["payload_parse_error"] = True
            save_to.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")

        diagnostics: List[LintDiagnostic] = []
        manim_ver: Optional[str] = None
        if out.strip():
            try:
                payload = json.loads(out)
                manim_ver = payload.get("manim_version")
                for d in payload.get("diagnostics", []) or []:
                    if isinstance(d, dict):
                        diagnostics.append(_parse_diagnostic(d))
            except json.JSONDecodeError:
                logger.warning("manim-lint stdout is not valid JSON: %s", out[:200])

        # CLI contract: exit 0 iff no error-level diagnostics
        success = proc.returncode == 0 and not any(d.severity.lower() == "error" for d in diagnostics)

        return LintReport(
            success=success,
            diagnostics=diagnostics,
            raw_stdout=out,
            raw_stderr=err,
            exit_code=proc.returncode,
            manim_version=manim_ver,
        )

    except subprocess.TimeoutExpired:
        logger.warning("manim-lint timed out after %s seconds", timeout)
        return LintReport(
            success=True,
            diagnostics=[],
            raw_stderr=f"timeout after {timeout}s",
            exit_code=-1,
            cli_error="timeout",
        )
    except FileNotFoundError as e:
        logger.warning("manim-lint executable not runnable: %s", e)
        return LintReport(success=True, diagnostics=[], cli_error=str(e))
    except OSError as e:
        logger.warning("manim-lint failed: %s", e)
        return LintReport(success=True, diagnostics=[], cli_error=str(e))
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
