from __future__ import annotations

from pathlib import Path

from .analyzer import RepositoryAnalyzer
from .graph import export_context_graph
from .wiki import write_wiki


def build_wiki(repository: str | Path, output_dir: str | Path = "wiki-output") -> dict[str, Path]:
    output = Path(output_dir)
    graph = RepositoryAnalyzer().analyze(repository)
    return {
        "wiki": write_wiki(graph, output / "README.md"),
        "graph": export_context_graph(graph, output / "graph.json"),
    }

