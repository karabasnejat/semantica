from pathlib import Path

from semantica_wiki.analyzer import RepositoryAnalyzer


def test_analyzer_extracts_python_symbols(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text(
        'import json\n\nclass Service:\n    """Business service."""\n\n    def run(self):\n        return json.dumps({"ok": True})\n\ndef health():\n    return "ok"\n',
        encoding="utf-8",
    )

    graph = RepositoryAnalyzer().analyze(tmp_path)

    assert any(node.kind == "Class" and node.name == "Service" for node in graph.nodes)
    assert any(node.kind == "Method" and node.name == "Service.run" for node in graph.nodes)
    assert any(node.kind == "Function" and node.name == "health" for node in graph.nodes)
    assert any(node.kind == "Dependency" and node.name == "json" for node in graph.nodes)
    assert any(relation.kind == "DECLARES" for relation in graph.relations)

