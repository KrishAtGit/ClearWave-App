from app.matching import FakeMatcher

async def test_fake_matcher() -> None:
    matches = await FakeMatcher().find_matches(b"any audio bytes")

    assert len(matches) == 2
    for match in matches:
        assert match.title
        assert match.artists
        assert 0 <= match.score <= 100

async def test_composers_default() -> None:
    matches = await FakeMatcher().find_matches(b"")
    assert matches[1].composers == []
    assert matches[0].composers is not matches[1].composers
    