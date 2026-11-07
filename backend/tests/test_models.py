from sqlalchemy import func, select
from app.db import Base, make_sessionmaker
from app.models import Claim, Match, User

# test: checking if deleting a claim deletes its matches
async def test_deleting_claim() -> None:
    engine, sessionmaker = make_sessionmaker("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with sessionmaker() as db:
        user = User(email="wow@example.com")
        db.add(user)
        await db.flush()

        claim = Claim(
            user_id=user.id,
            title="a simple loop",
            original_filename="loop.wav",
            audio_key=f"{user.id}/loop.wav",
            content_type="audio/wav",
            size_bytes=100,
        )

        db.add(claim)
        await db.flush()

        db.add(Match(
            claim_id=claim.id,
            title="mysong",
            artists=["X", "Y"],
            score=90
        ))
        await db.commit()

        saved = await db.scalar(select(Match))
        assert saved is not None
        assert saved.artists == ["X", "Y"]
        assert saved.composers == []

        await db.delete(claim)
        await db.commit()

        remaining = await db.scalar(
            select(func.count()).select_from(Match)
        )
        assert remaining == 0

    await engine.dispose()
