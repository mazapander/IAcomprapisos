from decimal import InvalidOperation

from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.sources.ine_common import extract_ine_table, fold, parse_decimal

INCOME_TABLE_ID = "53689"
INCOME_SOURCE_TABLE_ID = "53687"

ABSOLUTE_INDICATORS = (
    ("renta neta media por persona", "income_net_mean_person_eur"),
    ("renta neta media por hogar", "income_net_mean_household_eur"),
    ("media de la renta por unidad de consumo", "income_mean_equivalised_eur"),
    ("mediana de la renta por unidad de consumo", "income_median_equivalised_eur"),
    ("renta bruta media por persona", "income_gross_mean_person_eur"),
    ("renta bruta media por hogar", "income_gross_mean_household_eur"),
)

SOURCE_SHARE_INDICATORS = (
    ("prestaciones por desempleo", "income_share_unemployment_benefits_pct"),
    ("otras prestaciones", "income_share_other_benefits_pct"),
    ("pensiones", "income_share_pensions_pct"),
    ("salario", "income_share_salary_pct"),
    ("otros ingresos", "income_share_other_income_pct"),
)


class INEHouseholdIncomeIngestion(BaseIngestion):
    source = "ine_household_income"

    async def extract(self, parameters: dict) -> list[SourceRecord]:
        income = await extract_ine_table(
            INCOME_TABLE_ID,
            self.source,
            parameters,
            "annual",
        )
        source_mix = await extract_ine_table(
            INCOME_SOURCE_TABLE_ID,
            self.source,
            parameters,
            "annual",
        )
        return [*income, *source_mix]

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        result: list[IndicatorValue] = []
        for record in records:
            if not record.geography_code or not record.period:
                continue

            name = fold(str(record.payload.get("series_name", "")))
            table_id = str(record.payload.get("table_id", ""))
            indicator_code: str | None = None
            unit: str | None = None

            if table_id == INCOME_TABLE_ID:
                rules = ABSOLUTE_INDICATORS
                unit = "eur_year"
            elif table_id == INCOME_SOURCE_TABLE_ID:
                rules = SOURCE_SHARE_INDICATORS
                unit = "percent"
            else:
                continue

            for phrase, code in rules:
                if phrase in name:
                    indicator_code = code
                    break

            if not indicator_code or not unit:
                continue

            observation = record.payload.get("observation") or {}
            try:
                value = parse_decimal(observation.get("Valor"))
            except (ValueError, InvalidOperation):
                continue

            result.append(
                IndicatorValue(
                    indicator_code=indicator_code,
                    geography_code=record.geography_code,
                    period=record.period,
                    frequency="annual",
                    value=value,
                    unit=unit,
                    metadata={
                        "table_id": table_id,
                        "series_code": record.payload.get("series_code"),
                        "series_name": record.payload.get("series_name"),
                        "methodology": "ADRH",
                    },
                )
            )
        return result
