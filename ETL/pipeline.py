"""Reusable ETL pipeline runner for API usage."""
from __future__ import annotations

from pathlib import Path

from ETL.step_2_fetch_code_files import extract_code_files
from ETL.step_3_analyze_code_files import analyze_code_files
from ETL.step_5_cleanup_code_files import delete_extracted_code_files
from Remediation.remediation_summary import generate_remediation_summary
from Utils.common_utils import load_output_files_directory


def run_pipeline(repo_url: str) -> Path:
    """Run the ETL pipeline for a repository URL and return report path."""
    output_files_directory = load_output_files_directory()
    delete_extracted_code_files(output_files_directory)

    output_path = None
    try:
        output_path, _ = extract_code_files(repo_url, output_dir=output_files_directory)
        vulnerabilities_file = analyze_code_files(str(output_path))
        generate_remediation_summary(vulnerabilities_file)
    finally:
        # Ensure cleanup even if analysis fails.
        delete_extracted_code_files(output_files_directory)

    return vulnerabilities_file
