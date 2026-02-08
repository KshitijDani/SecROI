"""Shared LLM provider helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from openai import OpenAI


def _load_openai_api_key_from_env(project_root: Path) -> Optional[str]:
    env_path = project_root / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "OPENAI_API_KEY":
            return value.strip().strip("'").strip('"')
    return None


def call_gpt_5_1(prompt: str, api_key: Optional[str] = None) -> str:
    project_root = Path(__file__).resolve().parents[1]
    env_api_key = _load_openai_api_key_from_env(project_root)
    resolved_api_key = api_key or env_api_key
    client = OpenAI(api_key=resolved_api_key)
    response = client.responses.create(
        model="gpt-5.1",
        input=prompt,
    )
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    output_text_items = [
        item.text
        for item in getattr(response, "output", [])
        if getattr(item, "type", None) == "output_text"
    ]
    return "\n".join(output_text_items).strip()
