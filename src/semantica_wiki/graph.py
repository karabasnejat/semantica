from __future__ import annotations

from pathlib import Path

from semantica.context import ContextGraph

from .models import CodeGraph


NODE_COLORS = {
    "Repository": "#A78BFA",
    "File": "#63E6FF",
    "Class": "#34D399",
    "Function": "#FFD166",
    "Method": "#FF8FAB",
    "Dependency": "#94A3B8",
}


def export_context_graph(code_graph: CodeGraph, destination: str | Path) -> Path:
    graph = ContextGraph(advanced_analytics=False)
    for node in code_graph.nodes:
        graph.add_node(
            node.id,
            node_type=node.kind,
            content=node.name,
            color=NODE_COLORS.get(node.kind, "#CBD5E1"),
            path=node.path,
            line=node.line,
            **node.metadata,
        )
    for relation in code_graph.relations:
        graph.add_edge(relation.source, relation.target, edge_type=relation.kind)

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    graph.save_to_file(str(output))
    return output

