import pytest

from semantica_wiki.repository import normalize_github_url


def test_normalize_github_url() -> None:
    assert normalize_github_url("https://github.com/openai/openai-python") == "https://github.com/openai/openai-python.git"


@pytest.mark.parametrize("url", ["http://github.com/openai/openai-python", "https://example.com/openai/openai-python", "https://github.com/openai/openai-python/issues/1", "https://user:secret@github.com/openai/openai-python"])
def test_rejects_unsafe_or_non_repository_urls(url: str) -> None:
    with pytest.raises(ValueError):
        normalize_github_url(url)

