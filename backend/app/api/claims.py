import uuid
from datetime import timedelta
from typing import Annotated
from azure.core.exceptions import AzureError
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request,Response, UploadFile, status
from sqlalchemy import select 
from app.api.deps import CurrentUser, DbSession
from app.audio import detect_audio
from app.models import Claim, User, Match
from app.schemas import ClaimDetail, ClaimOut, MatchOut, EstimateIn
from app.jobs import match_claim
from app.royalties import PAYOUT_SOURCE, estimate_value

router = APIRouter(prefix='/api/claims', tags=['claims'])

AUDIO_LINK_LIFETIME= timedelta(minutes=10)

async def get_own_claim(db: DbSession, user: User, claim_id: uuid.UUID) -> Claim:
    claim = await db.scalar(select(Claim).where(
        Claim.id == claim_id,
        Claim.user_id == user.id
    ))
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    return claim

# helper - builds api of a match with its estimate calculated from stored inputs
def to_match_out(match: Match, payout_per_stream: float) -> MatchOut:
    out = MatchOut.model_validate(match, from_attributes=True)
    return out.model_copy(
        update={"estimated_value": estimate_value(match.streams, match.share_percent, payout_per_stream)}
    )

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClaimOut)
async def create_claim(
        user: CurrentUser,
        db: DbSession,
        request: Request,
        background_tasks: BackgroundTasks,
        title: Annotated[str, Form(min_length=1, max_length=200)],
        file: UploadFile
) -> Claim:
    limit = request.app.state.settings.max_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code = status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File is too large, over {request.app.state.settings.max_upload_mb} MB."
        )
    audio = detect_audio(data)
    if audio is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload an audio file: WAV, MP3, FLAC, OGG, AIFF or M4A"
        )

    claim_id=uuid.uuid4()
    key = f"{user.id}/{claim_id}.{audio.extension}"
    store = request.app.state.audio_store
    try:
        await store.save(key, data, audio.content_type)
    except AzureError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not store the file, please try again shortly"
        ) from error

    claim = Claim(
        id=claim_id,
        user_id=user.id,
        title=title.strip(),
        original_filename=(file.filename or f"sample.{audio.extension}")[:255],
        audio_key=key,
        content_type=audio.content_type,
        size_bytes=len(data),
    )
    db.add(claim)
    try:
        await db.commit()
    except Exception:
        await store.delete(key)
        raise
    await db.refresh(claim)

    background_tasks.add_task(
        match_claim,
        request.app.state.sessionmaker,
        request.app.state.matcher,
        claim.id, 
        data,
    )
    return claim

@router.get("", response_model=list[ClaimOut])
async def list_claims(user: CurrentUser, db: DbSession) -> list[Claim]:
    result = await db.scalars(
        select(Claim).where(Claim.user_id == user.id).order_by(Claim.created_at.desc())
    )
    return list(result)

@router.get("/{claim_id}", response_model=ClaimDetail)
async def get_claim(
    claim_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    request: Request
) -> ClaimDetail:
    claim = await get_own_claim(db, user, claim_id)
    matches = await db.scalars(
        select(Match).where(Match.claim_id == claim.id).order_by(Match.score.desc(), Match.title)
    )
    audio_url = request.app.state.audio_store.signed_url(claim.audio_key, AUDIO_LINK_LIFETIME)
    payout = request.app.state.settings.payout_per_stream
    return ClaimDetail(
        **ClaimOut.model_validate(claim, from_attributes=True).model_dump(),
        audio_url=audio_url,
        matches=[to_match_out(match, payout) for match in matches], 
        payout_per_stream=payout,
        payout_source=PAYOUT_SOURCE,   
    )

@router.patch("/{claim_id}/matches/{match_id}", response_model=MatchOut)
async def update_match_estimate(
    claim_id: uuid.UUID,
    match_id: uuid.UUID,
    body: EstimateIn,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> MatchOut:
    claim = await get_own_claim(db, user, claim_id)
    match = await db.scalar(select(Match).where(Match.id == match_id, Match.claim_id == claim.id))
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    match.streams = body.streams
    match.share_percent = body.share_percent
    await db.commit()
    return to_match_out(match, request.app.state.settings.payout_per_stream)

@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    request: Request
) -> Response:
    claim = await get_own_claim(db, user, claim_id)
    key = claim.audio_key
    await db.delete(claim)
    await db.commit()
    await request.app.state.audio_store.delete(key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

