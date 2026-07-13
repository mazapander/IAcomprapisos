import hashlib
import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IndicatorObservation, IngestionRun, RawSourceRecord
from app.ingestion.registry import get_ingestion

logger = logging.getLogger(__name__)


def _raw_metadata(payload: dict) -> dict:
    return {
        "source_version": payload.get("source_version"),
        "dataset_version": payload.get("dataset_version"),
        "source_url": payload.get("api_url") or payload.get("download_url") or payload.get("source_page"),
        "content_type": payload.get("content_type"),
        "http_status": payload.get("http_status"),
        "published_at": payload.get("published_at"),
        "available_at": payload.get("available_at"),
    }


async def _mark_run_failed(
    session: AsyncSession,
    run_id: UUID,
    error: Exception,
    source: str,
    requested_by: str,
    parameters: dict,
) -> IngestionRun:
    """Persist an ingestion failure after the work transaction has been rolled back.

    The UUID is passed as a plain Python value because ORM instances are expired by
    rollback. Reading ``run.id`` after rollback can trigger an implicit async database
    load and raise ``MissingGreenlet``, hiding the original ingestion error.
    """
    # Always dump the full traceback to the container logs BEFORE attempting to
    # persist it, so operators can diagnose the failure even if the persistence
    # step below itself raises.
    logger.exception(
        "Ingestion failed source=%s requested_by=%s parameters=%r error=%s",
        source,
        requested_by,
        parameters,
        error,
    )

    persisted_run = await session.get(IngestionRun, run_id)
    if persisted_run is None:
        raise RuntimeError(f"Ingestion run {run_id} disappeared after rollback") from error

    persisted_run.status = "failed"
    persisted_run.error = f"{type(error).__name__}: {error}"
    persisted_run.finished_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(persisted_run)
    return persisted_run


async def execute_ingestion(
    session: AsyncSession,
    source: str,
    requested_by: str,
    parameters: dict,
) -> IngestionRun:
    logger.info(
        "Ingestion starting source=%s requested_by=%s parameters=%r",
        source,
        requested_by,
        parameters,
    )

    job = get_ingestion(source)
    run = IngestionRun(
        source=source,
        status="running",
        requested_by=requested_by,
        parameters=parameters,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    run_id = run.id
    logger.info("Ingestion run created source=%s run_id=%s", source, run_id)

    try:
        records = await job.extract(parameters)
        run.rows_received = len(records)
        logger.info(
            "Ingestion extract completed source=%s run_id=%s rows_received=%d",
            source,
            run_id,
            len(records),
        )

        for record in records:
            canonical = json.dumps(
                record.payload,
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
            stmt = (
                insert(RawSourceRecord)
                .values(
                    run_id=run_id,
                    source=source,
                    dataset=record.dataset,
                    external_id=record.external_id,
                    period=record.period,
                    geography_code=record.geography_code,
                    payload=record.payload,
                    payload_hash=hashlib.sha256(canonical.encode()).hexdigest(),
                    observed_at=record.observed_at,
                    ingested_at=datetime.now(UTC),
                    **_raw_metadata(record.payload),
                )
                .on_conflict_do_nothing(constraint="uq_raw_source_dataset_hash")
            )
            await session.execute(stmt)

        indicators = job.transform(records)
        logger.info(
            "Ingestion transform completed source=%s run_id=%s rows_to_write=%d",
            source,
            run_id,
            len(indicators),
        )

        for item in indicators:
            metadata = item.metadata or {}
            stmt = (
                insert(IndicatorObservation)
                .values(
                    indicator_code=item.indicator_code,
                    geography_code=item.geography_code,
                    period=item.period,
                    frequency=item.frequency,
                    value=item.value,
                    unit=item.unit,
                    source=source,
                    source_run_id=run_id,
                    published_at=item.published_at,
                    available_at=metadata.get("available_at"),
                    metadata=metadata,
                )
                .on_conflict_do_update(
                    constraint="uq_indicator_geo_period_source",
                    set_={
                        "value": item.value,
                        "frequency": item.frequency,
                        "unit": item.unit,
                        "source_run_id": run_id,
                        "published_at": item.published_at,
                        "available_at": metadata.get("available_at"),
                        "metadata": metadata,
                    },
                )
            )
            await session.execute(stmt)

        run.rows_written = len(indicators)
        run.status = "succeeded"
        run.finished_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(run)
        logger.info(
            "Ingestion succeeded source=%s run_id=%s rows_received=%d rows_written=%d duration_s=%.2f",
            source,
            run_id,
            run.rows_received,
            run.rows_written,
            (run.finished_at - run.started_at).total_seconds(),
        )
        return run
    except Exception as exc:
        await session.rollback()
        return await _mark_run_failed(session, run_id, exc, source, requested_by, parameters)


async def list_runs(session: AsyncSession, limit: int = 100) -> list[IngestionRun]:
    result = await session.scalars(
        select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit)
    )
    return list(result)
