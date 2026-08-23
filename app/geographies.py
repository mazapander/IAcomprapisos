from __future__ import annotations

from collections.abc import Iterable
from datetime import date


CCAA: tuple[tuple[str, str], ...] = (
    ("CCAA:01", "Andalucía"),
    ("CCAA:02", "Aragón"),
    ("CCAA:03", "Principado de Asturias"),
    ("CCAA:04", "Illes Balears"),
    ("CCAA:05", "Canarias"),
    ("CCAA:06", "Cantabria"),
    ("CCAA:07", "Castilla y León"),
    ("CCAA:08", "Castilla-La Mancha"),
    ("CCAA:09", "Cataluña"),
    ("CCAA:10", "Comunitat Valenciana"),
    ("CCAA:11", "Extremadura"),
    ("CCAA:12", "Galicia"),
    ("CCAA:13", "Comunidad de Madrid"),
    ("CCAA:14", "Región de Murcia"),
    ("CCAA:15", "Comunidad Foral de Navarra"),
    ("CCAA:16", "País Vasco"),
    ("CCAA:17", "La Rioja"),
    ("CCAA:18", "Ceuta"),
    ("CCAA:19", "Melilla"),
)


PROVINCES: tuple[tuple[str, str, str], ...] = (
    ("PROV:01", "Araba/Álava", "CCAA:16"),
    ("PROV:02", "Albacete", "CCAA:08"),
    ("PROV:03", "Alicante/Alacant", "CCAA:10"),
    ("PROV:04", "Almería", "CCAA:01"),
    ("PROV:05", "Ávila", "CCAA:07"),
    ("PROV:06", "Badajoz", "CCAA:11"),
    ("PROV:07", "Illes Balears", "CCAA:04"),
    ("PROV:08", "Barcelona", "CCAA:09"),
    ("PROV:09", "Burgos", "CCAA:07"),
    ("PROV:10", "Cáceres", "CCAA:11"),
    ("PROV:11", "Cádiz", "CCAA:01"),
    ("PROV:12", "Castellón/Castelló", "CCAA:10"),
    ("PROV:13", "Ciudad Real", "CCAA:08"),
    ("PROV:14", "Córdoba", "CCAA:01"),
    ("PROV:15", "A Coruña", "CCAA:12"),
    ("PROV:16", "Cuenca", "CCAA:08"),
    ("PROV:17", "Girona", "CCAA:09"),
    ("PROV:18", "Granada", "CCAA:01"),
    ("PROV:19", "Guadalajara", "CCAA:08"),
    ("PROV:20", "Gipuzkoa", "CCAA:16"),
    ("PROV:21", "Huelva", "CCAA:01"),
    ("PROV:22", "Huesca", "CCAA:02"),
    ("PROV:23", "Jaén", "CCAA:01"),
    ("PROV:24", "León", "CCAA:07"),
    ("PROV:25", "Lleida", "CCAA:09"),
    ("PROV:26", "La Rioja", "CCAA:17"),
    ("PROV:27", "Lugo", "CCAA:12"),
    ("PROV:28", "Madrid", "CCAA:13"),
    ("PROV:29", "Málaga", "CCAA:01"),
    ("PROV:30", "Murcia", "CCAA:14"),
    ("PROV:31", "Navarra", "CCAA:15"),
    ("PROV:32", "Ourense", "CCAA:12"),
    ("PROV:33", "Asturias", "CCAA:03"),
    ("PROV:34", "Palencia", "CCAA:07"),
    ("PROV:35", "Las Palmas", "CCAA:05"),
    ("PROV:36", "Pontevedra", "CCAA:12"),
    ("PROV:37", "Salamanca", "CCAA:07"),
    ("PROV:38", "Santa Cruz de Tenerife", "CCAA:05"),
    ("PROV:39", "Cantabria", "CCAA:06"),
    ("PROV:40", "Segovia", "CCAA:07"),
    ("PROV:41", "Sevilla", "CCAA:01"),
    ("PROV:42", "Soria", "CCAA:07"),
    ("PROV:43", "Tarragona", "CCAA:09"),
    ("PROV:44", "Teruel", "CCAA:02"),
    ("PROV:45", "Toledo", "CCAA:08"),
    ("PROV:46", "Valencia/València", "CCAA:10"),
    ("PROV:47", "Valladolid", "CCAA:07"),
    ("PROV:48", "Bizkaia", "CCAA:16"),
    ("PROV:49", "Zamora", "CCAA:07"),
    ("PROV:50", "Zaragoza", "CCAA:02"),
    ("PROV:51", "Ceuta", "CCAA:18"),
    ("PROV:52", "Melilla", "CCAA:19"),
)


def build_geography_catalog(
    coverage_rows: Iterable[tuple[str, int, date | None]],
) -> list[dict]:
    coverage = {
        code: {"indicator_count": indicator_count, "latest_period": latest_period}
        for code, indicator_count, latest_period in coverage_rows
    }
    items = [
        {
            "code": "ES",
            "name": "España",
            "level": "country",
            "parent_code": None,
        },
        *(
            {
                "code": code,
                "name": name,
                "level": "ccaa",
                "parent_code": "ES",
            }
            for code, name in CCAA
        ),
        *(
            {
                "code": code,
                "name": name,
                "level": "province",
                "parent_code": parent_code,
            }
            for code, name, parent_code in PROVINCES
        ),
    ]
    for item in items:
        stats = coverage.get(item["code"], {})
        item["available"] = bool(stats)
        item["indicator_count"] = stats.get("indicator_count", 0)
        item["latest_period"] = stats.get("latest_period")
    return items
