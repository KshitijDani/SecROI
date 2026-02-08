"""Generate remediation summaries using the configured LLM provider."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from llm_providers.utils import call_gpt_5_1

SUMMARY_DIR = "code_file_remediation_summary"


def _extract_timestamp_from_report(report_path: Path) -> str:
    name = report_path.name
    if name.startswith("vulnerabilities_") and name.endswith(".json"):
        return name.replace("vulnerabilities_", "").replace(".json", "")
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_remediation_summary(report_path: Path, llm_call=call_gpt_5_1) -> Path:
    """Create a remediation summary for a vulnerabilities report."""
    if not report_path.exists():
        raise FileNotFoundError(f"Vulnerabilities report not found: {report_path}")

    vulnerabilities_text = report_path.read_text(encoding="utf-8")
    prompt = (
        "Here are the list of bugs detected in the files: \n"
        f"{vulnerabilities_text}\n\n"
        "Create a remediation summary of 250-300 words. "
        "Make sure you highlight the total number of bugs and list the top 5 files "
        "that need to be remediated. "
        "This text will be displayed in a ReactJS frontend, so return plain text only "
        "(no markdown, no bullets, no headings)."
    )

    summary_text = llm_call(prompt)

    summary_dir = Path(SUMMARY_DIR).resolve()
    summary_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _extract_timestamp_from_report(report_path)
    summary_path = summary_dir / f"remediation_summary_{timestamp}.txt"
    summary_path.write_text(summary_text.strip(), encoding="utf-8")
    return summary_path


def get_remediation_summary_path(report_name: str) -> Optional[Path]:
    """Resolve the remediation summary file for a given vulnerabilities report name."""
    if not report_name.startswith("vulnerabilities_") or not report_name.endswith(".json"):
        return None
    timestamp = report_name.replace("vulnerabilities_", "").replace(".json", "")
    summary_path = Path(SUMMARY_DIR).resolve() / f"remediation_summary_{timestamp}.txt"
    return summary_path if summary_path.exists() else None
