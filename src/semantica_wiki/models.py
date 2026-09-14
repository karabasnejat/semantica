from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CodeNode:
    id: str
    kind: str
    name: str
    path: str
    line: int = 1
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CodeRelation:
    source: str
    target: str
    kind: str


@dataclass
class CodeGraph:
    repository_name: str
    root: Path
    nodes: list[CodeNode] = field(default_factory=list)
    relations: list[CodeRelation] = field(default_factory=list)

    def node_map(self) -> dict[str, CodeNode]:
        return {node.id: node for node in self.nodes}

