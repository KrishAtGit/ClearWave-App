import logging
import uuid
from sqlalchemy import delete 
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.matching import Matcher
from app.models import Claim, Match

log = logging.getLogger(__name__)

async def match_claim(
        sessionmaker: async_sessionmaker[AsyncSession],
        matcher: Matcher,
        claim_id: uuid.UUID,
        audio: bytes
) -> None:
    async with sessionmaker() as db:
        claim = await db.get(Claim, claim_id)
        if claim is None:
            return 

        claim.status="matching"
        await db.commit()

        try: 
            songs = await matcher.find_matches(audio)
        except Exception:
            log.exception("Matching failed for claim %s", claim_id)
            claim.status = "failed"
            await db.commit()
            return

        claim = await db.get(Claim, claim_id, populate_existing=True)
        if claim is None:
            return

        await db.execute(delete(Match).where(Match.claim_id == claim_id))
        db.add_all([Match(
            claim_id=claim_id,
            title= song.title,
            artists=song.artists,
            album=song.album,
            label=song.label,
            release_date=song.release_date,
            isrc=song.isrc,
            score=song.score,
            offset_seconds=song.offset_seconds,
            spotify_track_id=song.spotify_track_id,
            youtube_video_id=song.youtube_video_id,
            composers=song.composers

            )
            for song in songs
        
        ])
        claim.status = "matched"
        await db.commit()
