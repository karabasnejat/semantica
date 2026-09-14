from pathlib import Path

from fastapi.testclient import TestClient

from semantica_wiki.web import create_app


def test_health_and_root(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, cors_origins=["https://karabasnejat.github.io"]))
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/").json() == {
        "name": "Semantica Wiki API",
        "health_url": "/api/health",
        "build_url": "/api/build",
    }


def test_build_endpoint_allows_configured_cors_origin(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, cors_origins=["https://karabasnejat.github.io"]))
    response = client.options(
        "/api/build",
        headers={
            "Origin": "https://karabasnejat.github.io",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://karabasnejat.github.io"


def test_rejects_non_github_url(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    response = client.post("/api/build", json={"repository_url": "https://example.com/acme/repo"})
    assert response.status_code == 400
