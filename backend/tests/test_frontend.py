from pathlib import Path
from httpx import ASGITransport, AsyncClient
from app.config import Settings
from app.main import create_app

async def test_serves_the_built_frontend(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>ClearWave app</h1>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('hi')")
    (tmp_path / "logo.svg").write_text("<svg></svg>")

    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:", static_dir=tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        assert "ClearWave app" in (await http.get("/")).text
        # a page react handles: the server returns index.html
        assert "ClearWave app" in (await http.get("/claims/42")).text
        assert (await http.get("/assets/app.js")).text == "console.log('hi')"
        assert (await http.get("/logo.svg")).text == "<svg></svg>"
        # real API routes still work, and unknown ones are a 404
        assert (await http.get("/api/nope")).status_code == 404
