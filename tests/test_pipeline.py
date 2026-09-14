import json
from pathlib import Path

from semantica_wiki.pipeline import build_wiki


def test_build_wiki_creates_markdown_and_graph(tmp_path: Path) -> None:
    repository = tmp_path / "demo"
    repository.mkdir()
    (repository / "main.py").write_text(
        'def greet(name):\n    """Return a greeting."""\n    return f"Hello {name}"\n',
        encoding="utf-8",
    )

    artifacts = build_wiki(repository, tmp_path / "output")

    wiki = artifacts["wiki"].read_text(encoding="utf-8")
    graph = json.loads(artifacts["graph"].read_text(encoding="utf-8"))
    assert "demo — Code Wiki" in wiki
    assert "`greet`" in wiki
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2

