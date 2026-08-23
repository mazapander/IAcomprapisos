from datetime import date

from app.geographies import build_geography_catalog


def test_geography_catalog_has_named_hierarchy_and_coverage() -> None:
    items = build_geography_catalog(
        [
            ("ES", 4, date(2026, 6, 1)),
            ("PROV:24", 7, date(2025, 12, 1)),
        ]
    )
    by_code = {item["code"]: item for item in items}

    assert by_code["PROV:24"] == {
        "code": "PROV:24",
        "name": "León",
        "level": "province",
        "parent_code": "CCAA:07",
        "available": True,
        "indicator_count": 7,
        "latest_period": date(2025, 12, 1),
    }
    assert by_code["PROV:48"]["name"] == "Bizkaia"
    assert by_code["PROV:48"]["available"] is False
    assert len([item for item in items if item["level"] == "province"]) == 52
