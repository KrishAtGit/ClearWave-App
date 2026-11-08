import httpx, pytest
from app.acrcloud import ACRCloudMatcher
from app.matching import MatcherError

SUCCESS = {
    "status" : {
        "code" : 0, 
        "msg": "Success"
        },
    "metadata" : {
        "music" : [
            {
                "title": "Real Song",
                "artists": [
                    {"name": "X-artist"},
                    {"name" : "Y-artist"}
                    ],
                "album": {"name" : "album-XY"},
                "label" : "XY-label",
                "release_date" : "2019-06-12",
                "external_ids" : {"isrc": "USABC15000001"},
                "external_metadata": {
                    "spotify" : {"track" : {"id" : "spotify123"}},
                    "youtube": {"vid": "yt123"},
                },
                "score" : 99,
                "play_offset_ms" : 42500,
            }
        ]
    },
}

def matcher_replying(body: dict, seen: list[httpx.Request] | None = None) -> ACRCloudMatcher:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ACRCloudMatcher(
        "identify.test",
        "test-key",
        "test-secret",
        client=client
    )

async def test_parses_a_successful_match() -> None:
    seen: list[httpx.Request] = []
    [song] = await matcher_replying(SUCCESS, seen).find_matches(b"audio bytes")

    assert song.title == "Real Song"
    assert song.artists == ["X-artist", "Y-artist"]
    assert song.album == "album-XY"
    assert song.label == "XY-label"
    assert song.release_date == "2019-06-12"
    assert song.isrc == "USABC15000001"
    assert song.score == 99
    assert song.offset_seconds == 42.5
    assert song.spotify_track_id == "spotify123"
    assert song.youtube_video_id == "yt123"
    assert song.composers == []

    [request] = seen
    assert request.url == "https://identify.test/v1/identify"
    assert b"test-key" in request.content
    assert b"test-secret" not in request.content  # the secret itself is never sent


async def test_no_result_is_an_empty_list() -> None:
    no_result = {"status": {"code": 1001, "msg": "No result"}}
    assert await matcher_replying(no_result).find_matches(b"x") == []


async def test_api_errors_raise_matcher_error() -> None:
    bad_key = {"status": {"code": 3001, "msg": "Missing/Invalid Access Key"}}
    with pytest.raises(MatcherError, match="3001"):
        await matcher_replying(bad_key).find_matches(b"x")