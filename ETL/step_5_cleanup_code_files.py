"""Step 5: Delete extracted code files to reduce disk usage."""
from __future__ import annotations

import shutil
from pathlib import Path


def delete_extracted_code_files(output_dir: str | Path) -> None:
    """Remove the extracted code files directory if it exists."""
    root = Path(output_dir).resolve()
    if not root.exists():
        return
    if not root.is_dir():
        raise NotADirectoryError(f"Expected a directory to delete: {root}")
    shutil.rmtree(root)
