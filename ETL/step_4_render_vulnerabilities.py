"""Step 4: Load vulnerabilities and render a terminal table."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_latest_vulnerabilities_path(root: Path) -> Optional[Path]:
    candidates = sorted(root.glob("vulnerabilities_*.json"))
    if candidates:
        return candidates[-1]
    fallback = root / "vulnerabilities.json"
    return fallback if fallback.exists() else None


def load_vulnerabilities(vulnerabilities_dir: str = "code_file_vulnerabilities") -> List[Dict[str, Any]]:
    """Load vulnerabilities from the JSON file produced in step 3."""
    root = Path(vulnerabilities_dir).resolve()
    json_path = get_latest_vulnerabilities_path(root)
    if json_path is None:
        raise FileNotFoundError(f"No vulnerability files found in: {root}")
    return json.loads(json_path.read_text(encoding="utf-8"))


def _flatten_findings(records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for record in records:
        file_name = str(record.get("file", ""))
        findings = record.get("findings", []) or []
        for finding in findings:
            rows.append(
                {
                    "file_name": str(finding.get("file_name", file_name)),
                    "bug_type": str(finding.get("bug_type", "")),
                    "bug_name": str(finding.get("bug_name", "")),
                    "bug_priority": str(finding.get("bug_priority", "")),
                    "file_lines": str(finding.get("file_lines", "")),
                }
            )
    return rows


def render_vulnerabilities_table(records: List[Dict[str, Any]]) -> str:
    """Return a simple table string for terminal output."""
    rows = _flatten_findings(records)
    if not rows:
        return "No vulnerabilities found."

    headers = ["file_name", "bug_type", "bug_name", "bug_priority", "file_lines"]
    widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            widths[h] = max(widths[h], len(row.get(h, "")))

    def format_row(row: Dict[str, str]) -> str:
        return " | ".join(row.get(h, "").ljust(widths[h]) for h in headers)

    header_line = format_row({h: h for h in headers})
    sep_line = "-+-".join("-" * widths[h] for h in headers)
    body_lines = [format_row(row) for row in rows]

    return "\n".join([header_line, sep_line, *body_lines])


def load_and_render_table(vulnerabilities_dir: str = "code_file_vulnerabilities") -> str:
    records = load_vulnerabilities(vulnerabilities_dir)
    return render_vulnerabilities_table(records)
