import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IndicatorObservation, IngestionRun, RawSourceRecord
from app.ingestion.registry import get_ingestion


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


async def execute_ingestion(
    session: AsyncSession,
    source: str,
    requested_by: str,
    parameters: dict,
) -> IngestionRun:
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

    try:
        records = await job.extract(parameters)
        run.rows_received = len(records)

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
                    run_id=run.id,
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
                    source_run_id=run.id,
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
                        "source_run_id": run.id,
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
    except Exception as exc:
        await session.rollback()
        persisted_run = await session.get(IngestionRun, run.id)
        if persisted_run is None:
            raise
        persisted_run.status = "failed"
        persisted_run.error = str(exc)
        persisted_run.finished_at = datetime.now(UTC)
        await session.commit()
        run = persisted_run

    await session.refresh(run)
    return run


async def list_runs(session: AsyncSession, limit: int = 100) -> list[IngestionRun]:
    result = await session.scalars(
        select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit)
    )
    return list(result)
