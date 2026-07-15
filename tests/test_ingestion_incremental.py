from app.ingestion.service import _payload_hash, _stable_payload


def test_raw_hash_ignores_retrieval_timestamps() -> None:
    first = {
        "series_code": "ETDP1826",
        "observation": {"Anyo": 2026, "T3_Periodo": "M04", "Valor": 53241.0},
        "retrieved_at": "2026-07-13T23:28:43+00:00",
    }
    second = {
        "series_code": "ETDP1826",
        "observation": {"Anyo": 2026, "T3_Periodo": "M04", "Valor": 53241.0},
        "retrieved_at": "2026-08-13T23:28:43+00:00",
    }

    assert _payload_hash(first) == _payload_hash(second)
    assert "retrieved_at" not in _stable_payload(first)


def test_raw_hash_changes_when_official_value_is_revised() -> None:
    provisional = {
        "series_code": "ETDP1826",
        "observation": {"Anyo": 2026, "T3_Periodo": "M04", "Valor": 53241.0},
        "retrieved_at": "2026-07-13T23:28:43+00:00",
    }
    revised = {
        "series_code": "ETDP1826",
        "observation": {"Anyo": 2026, "T3_Periodo": "M04", "Valor": 53310.0},
        "retrieved_at": "2026-08-13T23:28:43+00:00",
    }

    assert _payload_hash(provisional) != _payload_hash(revised)
