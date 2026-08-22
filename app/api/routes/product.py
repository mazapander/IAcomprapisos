import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response
from sqlalchemy import delete, distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import verify_api_key
from app.core.config import settings
from app.db.models import ProductEvent, ProductVisitor, UserQuestion
from app.db.session import get_session
from app.schemas.product import ConsentRequest, ProductEventRequest, QuestionRequest

router = APIRouter()
CONSENT_COOKIE = "iacp_consent"
VISITOR_COOKIE = "iacp_visitor"


def _cookie_options() -> dict:
    return {
        "max_age": settings.analytics_cookie_max_age_days * 86400,
        "secure": settings.analytics_cookie_secure,
        "samesite": "lax",
        "path": "/",
    }


def _visitor_id(raw: str | None) -> uuid.UUID | None:
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


@router.post("/consent")
async def set_consent(
    payload: ConsentRequest,
    response: Response,
    iacp_visitor: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(UTC)
    visitor_id = _visitor_id(iacp_visitor)
    options = _cookie_options()
    if payload.choice == "rejected":
        if visitor_id:
            await session.execute(
                update(UserQuestion).where(UserQuestion.visitor_id == visitor_id).values(visitor_id=None)
            )
            await session.execute(delete(ProductEvent).where(ProductEvent.visitor_id == visitor_id))
            await session.execute(delete(ProductVisitor).where(ProductVisitor.id == visitor_id))
            await session.commit()
        response.set_cookie(CONSENT_COOKIE, "rejected", httponly=False, **options)
        response.delete_cookie(VISITOR_COOKIE, path="/", secure=settings.analytics_cookie_secure, samesite="lax")
        return {"consent": "rejected", "analytics_enabled": False}

    visitor = await session.get(ProductVisitor, visitor_id) if visitor_id else None
    if visitor is None:
        visitor_id = uuid.uuid4()
        visitor = ProductVisitor(
            id=visitor_id,
            consent_version=payload.consent_version,
            consented_at=now,
            created_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(days=settings.product_data_retention_days),
        )
        session.add(visitor)
    else:
        visitor.consent_version = payload.consent_version
        visitor.consented_at = now
        visitor.last_seen_at = now
        visitor.expires_at = now + timedelta(days=settings.product_data_retention_days)
    await session.commit()
    response.set_cookie(CONSENT_COOKIE, "accepted", httponly=False, **options)
    response.set_cookie(VISITOR_COOKIE, str(visitor_id), httponly=True, **options)
    return {"consent": "accepted", "analytics_enabled": True}


@router.post("/events", status_code=202)
async def record_event(
    payload: ProductEventRequest,
    iacp_consent: str | None = Cookie(default=None),
    iacp_visitor: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    visitor_id = _visitor_id(iacp_visitor)
    if iacp_consent != "accepted" or not visitor_id:
        raise HTTPException(status_code=403, detail="Analytics consent is required")
    visitor = await session.get(ProductVisitor, visitor_id)
    if visitor is None:
        raise HTTPException(status_code=403, detail="Unknown analytics visitor")
    now = datetime.now(UTC)
    visitor.last_seen_at = now
    visitor.expires_at = now + timedelta(days=settings.product_data_retention_days)
    session.add(
        ProductEvent(
            visitor_id=visitor_id,
            session_id=payload.session_id,
            event_name=payload.event_name,
            page_path=payload.page_path,
            properties=payload.properties,
            occurred_at=now,
            expires_at=now + timedelta(days=settings.product_data_retention_days),
        )
    )
    await session.commit()
    return {"accepted": True}


@router.post("/questions", status_code=201)
async def submit_question(
    payload: QuestionRequest,
    iacp_consent: str | None = Cookie(default=None),
    iacp_visitor: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(UTC)
    visitor_id = _visitor_id(iacp_visitor) if iacp_consent == "accepted" else None
    question = UserQuestion(
        visitor_id=visitor_id,
        question=payload.question.strip(),
        category=payload.category,
        journey_stage=payload.journey_stage,
        geography_code=payload.geography_code,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        contact_consent=payload.contact_consent,
        privacy_notice_version=payload.privacy_notice_version,
        status="new",
        created_at=now,
        expires_at=now + timedelta(days=settings.product_data_retention_days),
    )
    session.add(question)
    await session.commit()
    return {"id": str(question.id), "status": "received"}


@router.get("/admin/metrics", dependencies=[Depends(verify_api_key)])
async def product_metrics(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> dict:
    since = datetime.now(UTC) - timedelta(days=days)
    event_rows = (
        await session.execute(
            select(ProductEvent.event_name, func.count(ProductEvent.id))
            .where(ProductEvent.occurred_at >= since)
            .group_by(ProductEvent.event_name)
        )
    ).all()
    events = {name: count for name, count in event_rows}
    visitors = await session.scalar(
        select(func.count(distinct(ProductEvent.visitor_id))).where(ProductEvent.occurred_at >= since)
    )
    questions = await session.scalar(
        select(func.count(UserQuestion.id)).where(UserQuestion.created_at >= since)
    )
    starts = events.get("review_started", 0)
    completions = events.get("review_completed", 0)
    return {
        "period_days": days,
        "unique_visitors": visitors or 0,
        "events": events,
        "questions": questions or 0,
        "review_completion_pct": round(completions / starts * 100, 1) if starts else None,
    }


@router.get("/admin/questions", dependencies=[Depends(verify_api_key)])
async def list_questions(
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    rows = (
        await session.scalars(
            select(UserQuestion).order_by(UserQuestion.created_at.desc()).limit(limit)
        )
    ).all()
    return [
        {
            "id": str(row.id),
            "question": row.question,
            "category": row.category,
            "journey_stage": row.journey_stage,
            "geography_code": row.geography_code,
            "contact_email": row.contact_email,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/admin/purge-expired", dependencies=[Depends(verify_api_key)])
async def purge_expired(session: AsyncSession = Depends(get_session)) -> dict:
    now = datetime.now(UTC)
    questions = await session.execute(delete(UserQuestion).where(UserQuestion.expires_at < now))
    events = await session.execute(delete(ProductEvent).where(ProductEvent.expires_at < now))
    visitors = await session.execute(delete(ProductVisitor).where(ProductVisitor.expires_at < now))
    await session.commit()
    return {
        "deleted_questions": questions.rowcount,
        "deleted_events": events.rowcount,
        "deleted_visitors": visitors.rowcount,
    }
