from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

import bleach
import markdown
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .pipeline import build_wiki
from .repository import cloned_repository


DEFAULT_CORS_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


class BuildRequest(BaseModel):
    repository_url: str = Field(min_length=20, max_length=300)


def parse_cors_origins(value: str | None) -> list[str]:
    if value is None:
        return list(DEFAULT_CORS_ORIGINS)
    origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)


def create_app(
    data_dir: str | Path = ".semantica-wiki/runs",
    cors_origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Semantica Wiki", version="0.2.0")
    run_root = Path(data_dir).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    allowed_origins = (
        cors_origins
        if cors_origins is not None
        else parse_cors_origins(os.getenv("SEMANTICA_CORS_ALLOW_ORIGINS"))
    )
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/")
    def home() -> dict[str, str]:
        return {
            "name": "Semantica Wiki API",
            "health_url": "/api/health",
            "build_url": "/api/build",
        }

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/build")
    def build(request: BuildRequest) -> dict[str, object]:
        run_id = uuid.uuid4().hex
        output = run_root / run_id
        try:
            with cloned_repository(request.repository_url) as repository:
                artifacts = build_wiki(repository, output)
                wiki_text = artifacts["wiki"].read_text(encoding="utf-8")
                graph = json.loads(artifacts["graph"].read_text(encoding="utf-8"))
        except ValueError as exc:
            shutil.rmtree(output, ignore_errors=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            shutil.rmtree(output, ignore_errors=True)
            raise HTTPException(status_code=422, detail=f"Repository could not be indexed: {exc}") from exc

        rendered_wiki = markdown.markdown(
            wiki_text, extensions=["fenced_code", "tables"]
        )
        safe_wiki = bleach.clean(
            rendered_wiki,
            tags={
                "a", "blockquote", "code", "em", "h1", "h2", "h3", "h4",
                "li", "ol", "p", "pre", "strong", "table", "tbody", "td",
                "th", "thead", "tr", "ul",
            },
            attributes={"a": ["href", "title"]},
        )
        return {
            "run_id": run_id,
            "node_count": len(graph.get("nodes", [])),
            "edge_count": len(graph.get("edges", [])),
            "wiki_html": safe_wiki,
            "graph_url": f"/api/runs/{run_id}/graph",
        }

    @app.get("/api/runs/{run_id}/graph")
    def graph_file(run_id: str) -> FileResponse:
        if not run_id.isalnum():
            raise HTTPException(status_code=404)
        graph_path = run_root / run_id / "graph.json"
        if not graph_path.is_file():
            raise HTTPException(status_code=404, detail="Graph not found")
        return FileResponse(graph_path, filename=f"semantica-wiki-{run_id}.json")

    return app


app = create_app()
