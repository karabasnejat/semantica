from pathlib import Path

from fastapi.testclient import TestClient

from semantica_wiki.web import create_app


def test_health_and_home(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/health").json() == {"status": "ok"}
    assert "Code Wiki" in client.get("/").text


def test_rejects_non_github_url(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    response = client.post("/api/build", json={"repository_url": "https://example.com/acme/repo"})
    assert response.status_code == 400

