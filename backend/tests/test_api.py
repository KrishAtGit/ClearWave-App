from httpx import AsyncClient

async def test_health_reports_database(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == { 
        "status" : "ok",
        "database" : True
        }

async def test_root_redirects_to_docs(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"

async def test_cors_allow_only_the_frontend(client: AsyncClient) -> None:
    allowed = await client.get("/api/health", headers={
        "Origin" : "http://localhost:5173"
        })
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    other = await client.get("/api/health", headers={
        "Origin" : "http://evil.example"
    })
    assert "access-control-allow-origin" not in other.headers
    