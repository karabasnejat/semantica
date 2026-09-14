from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from .models import CodeGraph


def render_wiki(graph: CodeGraph) -> str:
    counts = Counter(node.kind for node in graph.nodes)
    symbols_by_file: dict[str, list] = defaultdict(list)
    for node in graph.nodes:
        if node.kind in {"Class", "Function", "Method"}:
            symbols_by_file[node.path].append(node)

    dependencies = sorted(
        node.name for node in graph.nodes if node.kind == "Dependency"
    )
    lines = [
        f"# {graph.repository_name} — Code Wiki",
        "",
        "> Bu doküman kaynak koddan deterministik olarak üretilmiştir.",
        "",
        "## Genel Bakış",
        "",
        f"- Python dosyası: **{counts['File']}**",
        f"- Sınıf: **{counts['Class']}**",
        f"- Fonksiyon: **{counts['Function']}**",
        f"- Metot: **{counts['Method']}**",
        f"- İlişki: **{len(graph.relations)}**",
        "",
        "## Modüller",
        "",
    ]

    for path in sorted(node.name for node in graph.nodes if node.kind == "File"):
        lines.extend([f"### `{path}`", ""])
        symbols = sorted(symbols_by_file[path], key=lambda item: (item.line, item.name))
        if not symbols:
            lines.extend(["Tanımlı sınıf veya fonksiyon bulunmuyor.", ""])
            continue
        for symbol in symbols:
            doc = str(symbol.metadata.get("docstring", "")).splitlines()
            summary = doc[0] if doc else ""
            suffix = f" — {summary}" if summary else ""
            lines.append(
                f"- **{symbol.kind}** `{symbol.name}` ([kaynak]({path}#L{symbol.line})){suffix}"
            )
        lines.append("")

    lines.extend(["## Dış Bağımlılıklar", ""])
    lines.extend([f"- `{name}`" for name in dependencies] or ["- Bulunmuyor."])
    lines.extend(
        [
            "",
            "## Graph Explorer",
            "",
            "`graph.json` dosyasını Semantica Explorer ile açın:",
            "",
            "```bash",
            "SEMANTICA_ALLOW_ANONYMOUS=true semantica-explorer --graph wiki-output/graph.json",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_wiki(graph: CodeGraph, destination: str | Path) -> Path:
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_wiki(graph), encoding="utf-8")
    return output

