"""Step 1: Fetch repository URL from the user."""
from __future__ import annotations


def get_repo_url_from_user(prompt: str = "Enter a public code repository URL: ") -> str:
    """Prompt the user for a repository URL and return the cleaned value."""
    url = input(prompt).strip()
    return url
