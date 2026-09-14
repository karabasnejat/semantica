from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import bleach
import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .pipeline import build_wiki
from .repository import cloned_repository


class BuildRequest(BaseModel):
    repository_url: str = Field(min_length=20, max_length=300)


def create_app(data_dir: str | Path = ".semantica-wiki/runs") -> FastAPI:
    app = FastAPI(title="Semantica Wiki", version="0.2.0")
    run_root = Path(data_dir).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return INDEX_HTML

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


INDEX_HTML = r'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Semantica Wiki</title>
<style>:root{color-scheme:dark;--bg:#070a12;--panel:#101522;--line:#263047;--text:#eef2ff;--muted:#94a3b8;--cyan:#63e6ff;--violet:#a78bfa}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#17213a 0,var(--bg) 42%);color:var(--text);font:15px/1.6 Inter,system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:56px 24px}.eyebrow{color:var(--cyan);letter-spacing:.16em;text-transform:uppercase;font-size:12px}h1{font-size:clamp(38px,7vw,72px);line-height:1;margin:12px 0 18px;max-width:850px}h1 span{color:var(--violet)}.lead{color:var(--muted);font-size:18px;max-width:700px}form{display:flex;gap:10px;margin:34px 0}input{flex:1;background:#0b1020;border:1px solid var(--line);border-radius:12px;color:var(--text);padding:15px 17px;font-size:15px;outline:none}input:focus{border-color:var(--cyan)}button,.button{border:0;border-radius:12px;padding:15px 20px;background:linear-gradient(135deg,var(--cyan),var(--violet));color:#070a12;font-weight:800;cursor:pointer;text-decoration:none}button:disabled{opacity:.5;cursor:wait}#status{color:var(--muted);min-height:28px}.stats{display:none;grid-template-columns:repeat(2,1fr);gap:14px;margin:24px 0}.card,.wiki{background:rgba(16,21,34,.88);border:1px solid var(--line);border-radius:16px;padding:22px}.number{font-size:34px;font-weight:800}.label{color:var(--muted)}.actions{margin:18px 0 26px}.wiki{display:none;overflow:auto}.wiki h1{font-size:30px}.wiki h2{margin-top:32px;border-bottom:1px solid var(--line)}.wiki a{color:var(--cyan)}.wiki code{color:#c4b5fd}.error{color:#fda4af}@media(max-width:650px){form{flex-direction:column}}</style></head>
<body><main><div class="eyebrow">Graph-native code intelligence</div><h1>Repository’den yaşayan bir <span>Code Wiki</span> üret.</h1><p class="lead">Public GitHub reposunu gir. Semantica Wiki kod sembollerini, bağımlılıkları ve ilişkileri çıkarıp kaynak bağlantılı bir wiki ve keşfedilebilir graph üretir.</p>
<form id="form"><input id="url" type="url" required value="https://github.com/karabasnejat/semantica" aria-label="GitHub repository URL"><button id="submit">Wiki oluştur</button></form><div id="status"></div><section class="stats" id="stats"><div class="card"><div class="number" id="nodes">0</div><div class="label">Graph node</div></div><div class="card"><div class="number" id="edges">0</div><div class="label">İlişki</div></div></section><div class="actions" id="actions"></div><article class="wiki" id="wiki"></article></main>
<script>const form=document.querySelector('#form'),status=document.querySelector('#status'),button=document.querySelector('#submit');form.addEventListener('submit',async(e)=>{e.preventDefault();button.disabled=true;status.className='';status.textContent='Repository klonlanıyor ve bilgi grafiği oluşturuluyor…';document.querySelector('#wiki').style.display='none';document.querySelector('#stats').style.display='none';try{const response=await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({repository_url:document.querySelector('#url').value})});const data=await response.json();if(!response.ok)throw new Error(data.detail||'İşlem başarısız');document.querySelector('#nodes').textContent=data.node_count.toLocaleString('tr-TR');document.querySelector('#edges').textContent=data.edge_count.toLocaleString('tr-TR');document.querySelector('#stats').style.display='grid';document.querySelector('#actions').innerHTML=`<a class="button" href="${data.graph_url}">graph.json indir</a>`;document.querySelector('#wiki').innerHTML=data.wiki_html;document.querySelector('#wiki').style.display='block';status.textContent='Wiki hazır.';}catch(error){status.className='error';status.textContent=error.message}finally{button.disabled=false}});</script></body></html>'''
