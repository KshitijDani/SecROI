"""FastAPI app to run ETL pipeline and serve latest report."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ETL.pipeline import run_pipeline
from ETL.step_4_render_vulnerabilities import get_latest_vulnerabilities_path
from Remediation.remediation_summary import get_remediation_summary_path

app = FastAPI(title="Security ETL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run(repo_url: str) -> Dict[str, Any]:
    if not repo_url or not repo_url.strip():
        raise HTTPException(status_code=400, detail="repo_url is required")
    report_path = run_pipeline(repo_url.strip())
    return {
        "report_path": str(report_path),
        "report_name": report_path.name,
    }


@app.get("/report")
def report(name: Optional[str] = None) -> Dict[str, Any]:
    root = Path("code_file_vulnerabilities").resolve()
    if name:
        candidate = root / name
        if not candidate.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        latest = candidate
    else:
        latest = get_latest_vulnerabilities_path(root)
        if latest is None:
            raise HTTPException(status_code=404, detail="No report files found")
    return {
        "report_path": str(latest),
        "data": __import__("json").loads(latest.read_text(encoding="utf-8")),
    }


@app.get("/remediation")
def remediation(name: str) -> Dict[str, str]:
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    summary_path = get_remediation_summary_path(name)
    if summary_path is None:
        raise HTTPException(status_code=404, detail="Remediation summary not found")
    return {"summary": summary_path.read_text(encoding="utf-8")}


@app.get("/reports")
def reports() -> Dict[str, List[Dict[str, Any]]]:
    root = Path("code_file_vulnerabilities").resolve()
    if not root.exists():
        return {"reports": []}
    candidates = sorted(root.glob("vulnerabilities_*.json"))
    reports_list = [
        {
            "name": path.name,
            "path": str(path),
            "modified": path.stat().st_mtime,
        }
        for path in candidates
    ]
    reports_list.sort(key=lambda item: item["name"], reverse=True)
    return {"reports": reports_list}
