# SecROI

SecROI is a security scanning workflow that pulls a public GitHub repo, extracts code files, and analyzes them for common vulnerabilities. It generates a timestamped vulnerabilities report, a remediation summary, and renders an interactive UX with severity charts, occurrence counts, and remediation priorities. The report highlights risks by file, summarizes remediation needs, and provides a consolidated bugs list. Use it to quickly assess security posture, triage high‑risk findings, and guide remediation planning with a clean dashboard and actionable insights.

## Backend Setup
1. Create a venv and install deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r /Users/kshitijdani/Desktop/Ksh_Personal_Projects/secroi/requirements.txt
```
2. Add your API key:
Create `/Users/kshitijdani/Desktop/Ksh_Personal_Projects/secroi/.env` with:
```
OPENAI_API_KEY=your_key_here
```
3. Run the Backend Server:
```bash
cd /Users/kshitijdani/Desktop/Ksh_Personal_Projects/secroi
uvicorn api:app --reload --port 8001
```

## Frontend UX Setup
```bash
cd /Users/kshitijdani/Desktop/Ksh_Personal_Projects/secroi/UX
npm install
npm run dev
```
Open the URL Vite prints (usually `http://localhost:5173`).
