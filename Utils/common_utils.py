"""Shared utilities for pipeline steps."""
from __future__ import annotations

from pathlib import Path

CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".m",
    ".mm",
    ".php",
    ".pl",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}

DEFAULT_OUTPUT_FILES_DIRECTORY = "code_files"


def load_output_files_directory(config_path: Path | None = None) -> str:
    """Load output files directory from config.yaml, falling back to default."""
    resolved_config_path = (
        Path(config_path)
        if config_path is not None
        else Path(__file__).resolve().parents[1] / "config.yaml"
    )
    if not resolved_config_path.exists():
        return DEFAULT_OUTPUT_FILES_DIRECTORY
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required to read config.yaml. Install with `pip install pyyaml`."
        ) from exc
    data = yaml.safe_load(resolved_config_path.read_text(encoding="utf-8")) or {}
    value = data.get("output_files_directory", DEFAULT_OUTPUT_FILES_DIRECTORY)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit("output_files_directory must be a non-empty string in config.yaml.")
    return value.strip()
