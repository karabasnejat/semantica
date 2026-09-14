from __future__ import annotations

import ast
from pathlib import Path

from .models import CodeGraph, CodeNode, CodeRelation


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}


class RepositoryAnalyzer:
    """Deterministically extracts a navigable code graph from a Python repo."""

    def analyze(self, root: str | Path) -> CodeGraph:
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {root_path}")

        graph = CodeGraph(repository_name=root_path.name, root=root_path)
        repo_id = f"repo:{root_path.name}"
        graph.nodes.append(CodeNode(repo_id, "Repository", root_path.name, "."))

        python_files = sorted(
            path
            for path in root_path.rglob("*.py")
            if not any(part in IGNORED_DIRECTORIES for part in path.parts)
        )
        modules: dict[str, str] = {}

        for file_path in python_files:
            relative = file_path.relative_to(root_path).as_posix()
            module_name = self._module_name(relative)
            file_id = f"file:{relative}"
            modules[module_name] = file_id
            graph.nodes.append(CodeNode(file_id, "File", relative, relative))
            graph.relations.append(CodeRelation(repo_id, file_id, "CONTAINS"))

            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=relative)
            except (SyntaxError, UnicodeDecodeError):
                continue
            self._extract_symbols(tree, relative, file_id, graph)

        self._link_imports(graph, modules)
        return graph

    @staticmethod
    def _module_name(relative_path: str) -> str:
        path = relative_path.removesuffix(".py").replace("/", ".")
        return path.removesuffix(".__init__")

    def _extract_symbols(
        self, tree: ast.Module, path: str, file_id: str, graph: CodeGraph
    ) -> None:
        for item in tree.body:
            if isinstance(item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "Class" if isinstance(item, ast.ClassDef) else "Function"
                symbol_id = f"{kind.lower()}:{path}:{item.name}"
                graph.nodes.append(
                    CodeNode(
                        symbol_id,
                        kind,
                        item.name,
                        path,
                        item.lineno,
                        {"docstring": ast.get_docstring(item) or ""},
                    )
                )
                graph.relations.append(CodeRelation(file_id, symbol_id, "DECLARES"))

                if isinstance(item, ast.ClassDef):
                    for child in item.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_id = f"method:{path}:{item.name}.{child.name}"
                            graph.nodes.append(
                                CodeNode(
                                    method_id,
                                    "Method",
                                    f"{item.name}.{child.name}",
                                    path,
                                    child.lineno,
                                    {"docstring": ast.get_docstring(child) or ""},
                                )
                            )
                            graph.relations.append(
                                CodeRelation(symbol_id, method_id, "DECLARES")
                            )

        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    self._add_external_import(file_id, alias.name, path, item.lineno, graph)
            elif isinstance(item, ast.ImportFrom) and item.module:
                self._add_external_import(file_id, item.module, path, item.lineno, graph)

    @staticmethod
    def _add_external_import(
        file_id: str, module: str, path: str, line: int, graph: CodeGraph
    ) -> None:
        dependency = module.split(".")[0]
        dep_id = f"dependency:{dependency}"
        if not any(node.id == dep_id for node in graph.nodes):
            graph.nodes.append(CodeNode(dep_id, "Dependency", dependency, path, line))
        graph.relations.append(CodeRelation(file_id, dep_id, "IMPORTS"))

    @staticmethod
    def _link_imports(graph: CodeGraph, modules: dict[str, str]) -> None:
        node_map = graph.node_map()
        rewritten: list[CodeRelation] = []
        for relation in graph.relations:
            if relation.kind != "IMPORTS":
                rewritten.append(relation)
                continue
            dependency = node_map[relation.target].name
            local_target = next(
                (file_id for name, file_id in modules.items() if name == dependency or name.startswith(f"{dependency}.")),
                None,
            )
            rewritten.append(
                CodeRelation(relation.source, local_target or relation.target, relation.kind)
            )
        graph.relations = list(dict.fromkeys(rewritten))

