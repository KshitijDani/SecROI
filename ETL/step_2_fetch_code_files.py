"""Step 2: Validate GitHub repo and extract code files."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from Utils.common_utils import CODE_EXTENSIONS


def _normalize_github_url(repo_url: str) -> str:
    if repo_url.startswith("git@github.com:"):
        repo_path = repo_url.replace("git@github.com:", "https://github.com/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        return repo_path
    return repo_url.rstrip("/")


def _is_github_repo_url(repo_url: str) -> bool:
    parsed = urlparse(_normalize_github_url(repo_url))
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc.lower() != "github.com":
        return False
    path_parts = [part for part in parsed.path.split("/") if part]
    return len(path_parts) >= 2


def is_public_github_repo(repo_url: str) -> bool:
    """Return True if the repo URL is a public GitHub repo; otherwise False."""
    if not _is_github_repo_url(repo_url):
        return False

    normalized = _normalize_github_url(repo_url)
    try:
        result = subprocess.run(
            ["git", "ls-remote", normalized],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (subprocess.SubprocessError, OSError):
        return False

    return result.returncode == 0


def extract_code_files(repo_url: str, output_dir: str = "code_files") -> tuple[Path, int]:
    """Clone the repo and copy code files into output_dir."""
    if not is_public_github_repo(repo_url):
        raise ValueError("Repo URL is not a public GitHub repository.")

    normalized = _normalize_github_url(repo_url)
    repo_name = normalized.rstrip("/").split("/")[-1]
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        clone_path = Path(temp_dir) / "repo"
        clone_cmd = ["git", "clone", "--depth", "1", normalized, str(clone_path)]
        result = subprocess.run(
            clone_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {result.stderr.strip()}")

        extracted_count = 0
        manifest = []
        for root, dirs, files in os.walk(clone_path):
            if ".git" in dirs:
                dirs.remove(".git")
            root_path = Path(root)
            for filename in files:
                file_path = root_path / filename
                if file_path.suffix.lower() not in CODE_EXTENSIONS:
                    continue
                relative_path = file_path.relative_to(clone_path)
                target_path = destination / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, target_path)
                manifest.append(
                    {
                        "repo_url": normalized,
                        "repo_name": repo_name,
                        "repo_path": relative_path.as_posix(),
                        "extracted_path": target_path.as_posix(),
                    }
                )
                extracted_count += 1

        manifest_path = destination / "extracted_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return destination, extracted_count
