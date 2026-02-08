"""Step 3: Analyze extracted code files for security vulnerabilities."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional

from llm_providers.utils import call_gpt_5_1
from Utils.common_utils import CODE_EXTENSIONS

JSON_SCHEMA_EXAMPLE = [
    {
        "file_name": "path/to/file.py",
        "bug_type": "Injection",
        "bug_name": "SQL Injection",
        "bug_priority": "High",
        "file_lines": "42-58",
    }
]


def _load_max_num_files_from_config(config_path: Path) -> Optional[int]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if config_path.suffix.lower() == ".json":
        data = json.loads(config_path.read_text(encoding="utf-8"))
    elif config_path.suffix.lower() in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "PyYAML is required to read YAML configs. Install with `pip install pyyaml`."
            ) from exc
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        raise ValueError("Config must be a .json, .yml, or .yaml file.")

    value = data.get("max_num_files")
    if value is None:
        return None
    if not isinstance(value, int) or value < 1:
        raise ValueError("max_num_files must be a positive integer.")
    return value


def iter_code_files(root_dir: Path) -> Iterable[Path]:
    for path in root_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in CODE_EXTENSIONS:
            yield path


def build_security_prompt(file_path: Path, code_text: str) -> str:
    return (
        "You are a security code reviewer. Analyze the file for vulnerabilities such as SQL "
        "injection, XSS, SSRF, path traversal, command injection, insecure deserialization, "
        "unsafe cryptography, secrets exposure, auth bypass, and vulnerable dependencies. "
        "Return ONLY valid JSON matching this schema (no markdown, no commentary). "
        f"Schema example: {json.dumps(JSON_SCHEMA_EXAMPLE)}. "
        "If no issues are found, return an empty JSON array []. "
        f"File name: {file_path.as_posix()}\n\nCode:\n{code_text}"
    )


def analyze_code_files(
    output_dir: str,
    vulnerabilities_dir: str = "code_file_vulnerabilities",
    max_num_files: Optional[int] = None,
    config_path: Optional[str] = None,
    llm_provider: str = "openai",
    llm_call: Optional[Callable[[str], str]] = None,
) -> Path:
    root_dir = Path(output_dir).resolve()
    if not root_dir.exists():
        raise FileNotFoundError(f"Output directory not found: {root_dir}")

    manifest_path = root_dir / "extracted_manifest.json"
    manifest_map = {}
    repo_name = None
    repo_url = None
    if manifest_path.exists():
        try:
            manifest_entries = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in manifest_entries:
                if not isinstance(entry, dict):
                    continue
                extracted_path = entry.get("extracted_path")
                repo_path = entry.get("repo_path")
                if extracted_path and repo_path:
                    manifest_map[extracted_path] = repo_path
                if repo_name is None:
                    repo_name = entry.get("repo_name")
                if repo_url is None:
                    repo_url = entry.get("repo_url")
        except json.JSONDecodeError:
            manifest_map = {}

    vulnerabilities_path = Path(vulnerabilities_dir).resolve()
    vulnerabilities_path.mkdir(parents=True, exist_ok=True)

    if max_num_files is None:
        if config_path is None:
            project_root = Path(__file__).resolve().parents[1]
            config_path = str(project_root / "config.yaml")
        config_file = Path(config_path)
        if config_file.exists():
            max_num_files = _load_max_num_files_from_config(config_file)

    if llm_call is None:
        if llm_provider == "openai":
            llm_call = call_gpt_5_1
        else:
            raise NotImplementedError(
                f"LLM provider '{llm_provider}' is not configured. "
                "Provide llm_call or set llm_provider to 'openai'."
            )

    results = []
    processed = 0
    for file_path in iter_code_files(root_dir):
        if max_num_files is not None and processed >= max_num_files:
            break
        print(f"Analyzing file: {file_path.as_posix()}")
        code_text = file_path.read_text(encoding="utf-8", errors="ignore")
        prompt = build_security_prompt(file_path, code_text)
        response_text = llm_call(prompt)
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            parsed = [
                {
                    "file_name": file_path.as_posix(),
                    "bug_type": "LLM_OUTPUT_ERROR",
                    "bug_name": "Invalid JSON",
                    "bug_priority": "High",
                    "file_lines": "",
                }
            ]
        repo_path = manifest_map.get(file_path.as_posix()) or file_path.relative_to(root_dir).as_posix()
        if isinstance(parsed, list):
            for finding in parsed:
                if isinstance(finding, dict):
                    finding["file_name"] = repo_path
        results.append(
            {
                "file": repo_path,
                "repo_name": repo_name,
                "repo_url": repo_url,
                "findings": parsed,
            }
        )
        processed += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = vulnerabilities_path / f"vulnerabilities_{timestamp}.json"
    output_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return output_file
