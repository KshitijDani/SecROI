"""Entry point for the security scanning package."""
from __future__ import annotations

import logging

from Utils.common_utils import load_output_files_directory
from Remediation.remediation_summary import generate_remediation_summary
from ETL.step_1_fetch_url import get_repo_url_from_user
from ETL.step_2_fetch_code_files import extract_code_files
from ETL.step_3_analyze_code_files import analyze_code_files
from ETL.step_4_render_vulnerabilities import load_and_render_table
from ETL.step_5_cleanup_code_files import delete_extracted_code_files

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Run the pipeline steps in order."""
    logger.info("Step 1: Fetching repository URL.")
    repo_url = get_repo_url_from_user()
    if not repo_url:
        print("No repository URL provided.")
        return

    try:
        output_files_directory = load_output_files_directory()
        logger.info("Step 2: Fetching code files from repository.")
        logger.info("Pre-step: Clearing extracted code files directory.")
        try:
            delete_extracted_code_files(output_files_directory)
        except (NotADirectoryError, OSError) as exc:
            raise SystemExit(str(exc)) from exc
        output_path, extracted_count = extract_code_files(
            repo_url,
            output_dir=output_files_directory,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Code files extracted to: {output_path}")
    logger.info("Extracted %d code files.", extracted_count)

    try:
        logger.info("Step 3: Analyzing code files with LLM.")
        vulnerabilities_file = analyze_code_files(str(output_path))
    except (FileNotFoundError, NotImplementedError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Vulnerability report saved to: {vulnerabilities_file}")

    try:
        logger.info("Step 3.5: Generating remediation summary.")
        remediation_file = generate_remediation_summary(vulnerabilities_file)
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Remediation summary saved to: {remediation_file}")

    try:
        logger.info("Step 4: Rendering vulnerabilities table.")
        table = load_and_render_table()
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    print("\nVulnerabilities Table:\n")
    print(table)

    logger.info("Step 5: Cleaning up extracted code files.")
    try:
        delete_extracted_code_files(output_files_directory)
    except (NotADirectoryError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
