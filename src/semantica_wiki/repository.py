from __future__ import annotations

import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from git import Repo


GITHUB_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def normalize_github_url(url: str) -> str:
    """Return a canonical public GitHub HTTPS URL or reject the input."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("Only https://github.com/owner/repository URLs are accepted.")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("Credentials and custom ports are not accepted in repository URLs.")
    repository = parsed.path.strip("/").removesuffix(".git")
    if not GITHUB_REPOSITORY.fullmatch(repository):
        raise ValueError("GitHub URL must contain exactly an owner and repository name.")
    return f"https://github.com/{repository}.git"


@contextmanager
def cloned_repository(url: str) -> Iterator[Path]:
    canonical_url = normalize_github_url(url)
    with tempfile.TemporaryDirectory(prefix="semantica-wiki-") as directory:
        target = Path(directory) / "repository"
        Repo.clone_from(
            canonical_url,
            target,
            depth=1,
            single_branch=True,
            no_tags=True,
            env={"GIT_TERMINAL_PROMPT": "0"},
        )
        yield target

