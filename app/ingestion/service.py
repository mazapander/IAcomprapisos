import hashlib
import json
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import IndicatorObservation, IngestionRun, RawSourceRecord
from app.ingestion.registry import get_ingestion

async def execute_ingestion(session: AsyncSession, source: str, requested_by: str, parameters: dict) -> IngestionRun:
    job = get_ingestion(source)
    run = IngestionRun(source=source, status="running", requested_by=requested_by, parameters=parameters, started_at=datetime.now(UTC))
    session.add(run)
    await session.commit()
    await session.refresh(run)
    try:
        records = await job.extract(parameters)
        run.rows_received = len(records)
        for record in records:
            canonical = json.dumps(record.payload, sort_keys=True, ensure_ascii=False, default=str)
            stmt = insert(RawSourceRecord).values(run_id=run.id, source=source, dataset=record.dataset, external_id=record.external_id, period=record.period, geography_code=record.geography_code, payload=record.payload, payload_hash=hashlib.sha256(canonical.encode()).hexdigest(), observed_at=record.observed_at, ingested_at=datetime.now(UTC)).on_conflict_do_nothing(constraint="uq_raw_source_dataset_hash")
            await session.execute(stmt)
        indicators = job.transform(records)
        for item in indicators:
            stmt = insert(IndicatorObservation).values(indicator_code=item.indicator_code, geography_code=item.geography_code, period=item.period, frequency=item.frequency, value=item.value, unit=item.unit, source=source, source_run_id=run.id, published_at=item.published_at, metadata=item.metadata or {}).on_conflict_do_update(constraint="uq_indicator_geo_period_source", set_={"value": item.value, "source_run_id": run.id, "published_at": item.published_at, "metadata": item.metadata or {}})
            await session.execute(stmt)
        run.rows_written = len(indicators)
        run.status = "succeeded"
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
    finally:
        run.finished_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(run)
    return run

async def list_runs(session: AsyncSession, limit: int = 100) -> list[IngestionRun]:
    result = await session.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit))
    return list(result)
