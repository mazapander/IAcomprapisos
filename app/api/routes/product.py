import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response
from sqlalchemy import delete, distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import verify_api_key
from app.core.config import settings
from app.db.models import MarketObservation, ProductEvent, ProductVisitor, UserQuestion
from app.db.session import get_session
from app.schemas.product import (
    ConsentRequest,
    MarketObservationRequest,
    ProductEventRequest,
    QuestionNotificationResult,
    QuestionRequest,
)

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


def _market_observation_metrics(observation: MarketObservation) -> dict[str, float | None]:
    surface = float(observation.surface_area_m2)

    def per_m2(value) -> float | None:
        return round(float(value) / surface, 2) if value is not None else None

    def percentage(numerator, denominator) -> float | None:
        if numerator is None or denominator is None:
            return None
        return round((float(numerator) - float(denominator)) / float(denominator) * 100, 2)

    asking = observation.asking_price_eur
    appraisal = observation.appraisal_value_eur
    negotiated = observation.negotiated_price_eur
    deed = observation.deed_price_eur
    negotiated_discount = None
    if asking is not None and negotiated is not None:
        negotiated_discount = round(
            (float(asking) - float(negotiated)) / float(asking) * 100,
            2,
        )
    return {
        "asking_price_eur_m2": per_m2(asking),
        "appraisal_value_eur_m2": per_m2(appraisal),
        "negotiated_price_eur_m2": per_m2(negotiated),
        "deed_price_eur_m2": per_m2(deed),
        "asking_vs_appraisal_pct": percentage(asking, appraisal),
        "negotiated_discount_pct": negotiated_discount,
        "deed_vs_appraisal_pct": percentage(deed, appraisal),
    }
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
        notification_attempts=0,
        created_at=now,
        expires_at=now + timedelta(days=settings.product_data_retention_days),
    )
    session.add(question)
    await session.commit()
    return {"id": str(question.id), "status": "received"}


@router.post("/market-observations", status_code=201)
async def submit_market_observation(
    payload: MarketObservationRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    now = datetime.now(UTC)
    observation = MarketObservation(
        id=uuid.uuid4(),
        geography_code=payload.geography_code,
        property_type=payload.property_type,
        property_age=payload.property_age,
        contributor_role=payload.contributor_role,
        surface_area_m2=payload.surface_area_m2,
        asking_price_eur=payload.asking_price_eur,
        appraisal_value_eur=payload.appraisal_value_eur,
        negotiated_price_eur=payload.negotiated_price_eur,
        deed_price_eur=payload.deed_price_eur,
        observed_period=payload.observed_period,
        market_data_consent=True,
        privacy_notice_version=payload.privacy_notice_version,
        status="submitted",
        created_at=now,
        expires_at=now + timedelta(days=settings.product_data_retention_days),
    )
    session.add(observation)
    await session.commit()
    return {
        "id": str(observation.id),
        "status": observation.status,
        "metrics": _market_observation_metrics(observation),
    }


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
    market_observations = await session.scalar(
        select(func.count(MarketObservation.id)).where(MarketObservation.created_at >= since)
    )
    category_rows = (
        await session.execute(
            select(UserQuestion.category, func.count(UserQuestion.id))
            .where(UserQuestion.created_at >= since)
            .group_by(UserQuestion.category)
        )
    ).all()
    stage_rows = (
        await session.execute(
            select(UserQuestion.journey_stage, func.count(UserQuestion.id))
            .where(UserQuestion.created_at >= since)
            .group_by(UserQuestion.journey_stage)
        )
    ).all()
    starts = events.get("review_started", 0)
    completions = events.get("review_completed", 0)
    return {
        "period_days": days,
        "unique_visitors": visitors or 0,
        "events": events,
        "questions": questions or 0,
        "market_observations": market_observations or 0,
        "question_categories": {category: count for category, count in category_rows},
        "question_journey_stages": {stage: count for stage, count in stage_rows},
        "review_completion_pct": round(completions / starts * 100, 1) if starts else None,
    }


@router.get("/admin/questions", dependencies=[Depends(verify_api_key)])
async def list_questions(
    limit: int = Query(100, ge=1, le=500),
    status: str | None = Query(default=None, pattern=r"^(new|notified|resolved|dismissed)$"),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    statement = select(UserQuestion)
    if status:
        statement = statement.where(UserQuestion.status == status)
    rows = (await session.scalars(statement.order_by(UserQuestion.created_at.desc()).limit(limit))).all()
    return [
        {
            "id": str(row.id),
            "question": row.question,
            "category": row.category,
            "journey_stage": row.journey_stage,
            "geography_code": row.geography_code,
            "contact_email": row.contact_email,
            "contact_consent": row.contact_consent,
            "status": row.status,
            "notification_attempts": row.notification_attempts,
            "notified_at": row.notified_at,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/admin/questions/notifications/pending", dependencies=[Depends(verify_api_key)])
async def pending_question_notifications(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    rows = (
        await session.scalars(
            select(UserQuestion)
            .where(UserQuestion.status == "new")
            .order_by(UserQuestion.created_at.asc())
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": str(row.id),
            "question": row.question,
            "category": row.category,
            "journey_stage": row.journey_stage,
            "geography_code": row.geography_code,
            "contact_email": row.contact_email if row.contact_consent else None,
            "notification_attempts": row.notification_attempts,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post(
    "/admin/questions/{question_id}/notification-result",
    dependencies=[Depends(verify_api_key)],
)
async def record_question_notification_result(
    question_id: uuid.UUID,
    payload: QuestionNotificationResult,
    session: AsyncSession = Depends(get_session),
) -> dict:
    question = await session.get(UserQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    question.notification_attempts += 1
    if payload.delivered:
        question.status = "notified"
        question.notified_at = datetime.now(UTC)
        question.last_notification_error = None
    else:
        question.status = "new"
        question.last_notification_error = payload.error
    await session.commit()
    return {
        "id": str(question.id),
        "status": question.status,
        "notification_attempts": question.notification_attempts,
    }


@router.get("/admin/market-observations", dependencies=[Depends(verify_api_key)])
async def list_market_observations(
    limit: int = Query(100, ge=1, le=500),
    geography_code: str | None = Query(default=None, max_length=20),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    statement = select(MarketObservation)
    if geography_code:
        statement = statement.where(MarketObservation.geography_code == geography_code)
    rows = (
        await session.scalars(statement.order_by(MarketObservation.created_at.desc()).limit(limit))
    ).all()
    return [
        {
            "id": str(row.id),
            "geography_code": row.geography_code,
            "property_type": row.property_type,
            "property_age": row.property_age,
            "contributor_role": row.contributor_role,
            "surface_area_m2": float(row.surface_area_m2),
            "observed_period": row.observed_period,
            "status": row.status,
            "metrics": _market_observation_metrics(row),
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/admin/purge-expired", dependencies=[Depends(verify_api_key)])
async def purge_expired(session: AsyncSession = Depends(get_session)) -> dict:
    now = datetime.now(UTC)
    questions = await session.execute(delete(UserQuestion).where(UserQuestion.expires_at < now))
    market_observations = await session.execute(
        delete(MarketObservation).where(MarketObservation.expires_at < now)
    )
    events = await session.execute(delete(ProductEvent).where(ProductEvent.expires_at < now))
    visitors = await session.execute(delete(ProductVisitor).where(ProductVisitor.expires_at < now))
    await session.commit()
    return {
        "deleted_questions": questions.rowcount,
        "deleted_market_observations": market_observations.rowcount,
        "deleted_events": events.rowcount,
        "deleted_visitors": visitors.rowcount,
    }
