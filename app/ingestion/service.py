import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IndicatorObservation, IngestionRun, RawSourceRecord
from app.ingestion.registry import get_ingestion

logger = logging.getLogger(__name__)

_VOLATILE_RAW_KEYS = {"retrieved_at", "ingested_at", "observed_at"}


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


def _stable_payload(value: Any) -> Any:
    """Remove retrieval-only fields before calculating raw idempotency hashes.

    The source payload remains stored untouched. Only the hash input is normalized so
    rerunning the same official observation does not create another raw row merely
    because it was downloaded at a different time. A revised official value still
    produces a new hash and is therefore retained as a new raw version.
    """
    if isinstance(value, dict):
        return {
            key: _stable_payload(item)
            for key, item in value.items()
            if key not in _VOLATILE_RAW_KEYS
        }
    if isinstance(value, list):
        return [_stable_payload(item) for item in value]
    return value


def _payload_hash(payload: dict) -> str:
    canonical = json.dumps(
        _stable_payload(payload),
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


async def _resolve_ingestion_parameters(
    session: AsyncSession,
    source: str,
    parameters: dict,
) -> dict:
    """Resolve incremental mode against the latest analytical period in PostgreSQL."""
    resolved = dict(parameters)
    mode = str(resolved.pop("mode", "full")).lower()
    if mode not in {"full", "incremental", "latest"}:
        raise ValueError("parameters.mode must be full, incremental or latest")

    if mode in {"incremental", "latest"} and not resolved.get("date_from"):
        latest_period = await session.scalar(
            select(func.max(IndicatorObservation.period)).where(
                IndicatorObservation.source == source
            )
        )
        if latest_period is not None:
            # Re-read the latest stored period as an overlap. The analytics upsert
            # updates provisional revisions and inserts a newly published period.
            resolved["date_from"] = latest_period.isoformat()
            logger.info(
                "Incremental ingestion resolved source=%s latest_period=%s",
                source,
                latest_period,
            )
        else:
            logger.info(
                "Incremental ingestion has no previous data; falling back to full source=%s",
                source,
            )
    resolved["mode"] = mode
    return resolved


async def _mark_run_failed(
    session: AsyncSession,
    run_id: UUID,
    error: Exception,
    source: str,
    requested_by: str,
    parameters: dict,
) -> IngestionRun:
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
    resolved_parameters = await _resolve_ingestion_parameters(session, source, parameters)
    logger.info(
        "Ingestion starting source=%s requested_by=%s parameters=%r",
        source,
        requested_by,
        resolved_parameters,
    )

    job = get_ingestion(source)
    run = IngestionRun(
        source=source,
        status="running",
        requested_by=requested_by,
        parameters=resolved_parameters,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    run_id = run.id
    logger.info("Ingestion run created source=%s run_id=%s", source, run_id)

    try:
        extract_parameters = {
            key: value for key, value in resolved_parameters.items() if key != "mode"
        }
        records = await job.extract(extract_parameters)
        run.rows_received = len(records)
        logger.info(
            "Ingestion extract completed source=%s run_id=%s rows_received=%d",
            source,
            run_id,
            len(records),
        )

        for record in records:
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
                    payload_hash=_payload_hash(record.payload),
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

        indicator_table = IndicatorObservation.__table__
        for item in indicators:
            item_metadata = item.metadata or {}
            stmt = (
                insert(indicator_table)
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
                    available_at=item_metadata.get("available_at"),
                    metadata=item_metadata,
                )
                .on_conflict_do_update(
                    constraint="uq_indicator_geo_period_source",
                    set_={
                        indicator_table.c.value: item.value,
                        indicator_table.c.frequency: item.frequency,
                        indicator_table.c.unit: item.unit,
                        indicator_table.c.source_run_id: run_id,
                        indicator_table.c.published_at: item.published_at,
                        indicator_table.c.available_at: item_metadata.get("available_at"),
                        indicator_table.c.metadata: item_metadata,
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
        return await _mark_run_failed(
            session,
            run_id,
            exc,
            source,
            requested_by,
            resolved_parameters,
        )


async def list_runs(session: AsyncSession, limit: int = 100) -> list[IngestionRun]:
    result = await session.scalars(
        select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit)
    )
    return list(result)
