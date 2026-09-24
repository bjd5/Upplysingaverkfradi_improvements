"""Síurnar úr veðurstöðvaæfingunni, framkvæmdar sem SQL á ``weather_stations``.

Gamla verkefnið sendi hverja síu sem sérstaka beiðni til þjónustunnar —
``station_id=``, ``active=true`` og ``polygon=`` — og treysti henni fyrir
svarinu. Hér er sama síun gerð á frosna eintakinu í grunninum. Það er tilgangur
æfingarinnar: sama spurning, sama svar, en netlaust og endurtekjanlegt.

SQL-ið sjálft er í ``src/sql/queries/vedurstodvar-siur.sql`` og er lesið þaðan.
Fyrirspurn sem er afrituð inn í Python fer fyrr eða síðar á skjön við skrána
sem á að vera heimildin.

**Öll gildi fara inn sem breytur** (``cur.execute(sql, (gildi,))``) — engin
fyrirspurn hér er sett saman úr strengjum (regla 5).

Fjarlægðarreikningurinn kemur úr ``vedurstodvar_samanburdur`` og er skráður á
tenginguna sem SQL-fallið ``fjarlaegd_metrar``, svo röðun eftir fjarlægð gerist
í fyrirspurninni og noti sömu formúlu og samanburðurinn við gömlu síðuna.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import re
from pathlib import Path
from sqlite3 import Connection, Row

from gagnagrunnur.tenging import ROT

from .vedurstodvar_samanburdur import haversine_km

FYRIRSPURNASKRA = ROT / "src" / "sql" / "queries" / "vedurstodvar-siur.sql"

# Hver fyrirspurn hefst á "-- @fyrirspurn: <heiti>" í SQL-skránni.
MERKI = re.compile(r"^--\s*@fyrirspurn:\s*([a-z0-9_]+)\s*$")

FJARLAEGDARFALL = "fjarlaegd_metrar"
METRAR_I_KM = 1000.0

_SAFN: dict[str, str] | None = None


class FyrirspurnaVilla(RuntimeError):
    """Fyrirspurnasafnið er ekki læsilegt eða fyrirspurnin finnst ekki."""


def lesa_fyrirspurnir(slod: Path = FYRIRSPURNASKRA) -> dict[str, str]:
    """Þáttar SQL-skrána í nefndar fyrirspurnir.

    Tvær fyrirspurnir með sama heiti stöðva lesturinn: önnur myndi annars
    hverfa þegjandi og kallandinn fengi ranga fyrirspurn (regla 6).
    """
    if not slod.is_file():
        raise FyrirspurnaVilla(f"Fyrirspurnaskráin finnst ekki: {slod}")

    safn: dict[str, list[str]] = {}
    heiti: str | None = None
    for lina in slod.read_text(encoding="utf-8").splitlines():
        samsvorun = MERKI.match(lina.strip())
        if samsvorun is not None:
            heiti = samsvorun.group(1)
            if heiti in safn:
                raise FyrirspurnaVilla(
                    f"Fyrirspurnin {heiti!r} er skilgreind oftar en einu sinni í "
                    f"{slod.name}. Heitin verða að vera einkvæm."
                )
            safn[heiti] = []
        elif heiti is not None:
            safn[heiti].append(lina)

    if not safn:
        raise FyrirspurnaVilla(
            f"Engin fyrirspurn fannst í {slod.name} — vantar línuna "
            "'-- @fyrirspurn: <heiti>'?"
        )
    return {heiti: "\n".join(linur).strip() for heiti, linur in safn.items()}


def fyrirspurn(heiti: str) -> str:
    """Skilar nefndri fyrirspurn úr safninu og les skrána í fyrsta sinn."""
    global _SAFN
    if _SAFN is None:
        _SAFN = lesa_fyrirspurnir()
    if heiti not in _SAFN:
        raise FyrirspurnaVilla(
            f"Fyrirspurnin {heiti!r} er ekki til. Þessar eru til: "
            + ", ".join(sorted(_SAFN))
        )
    return _SAFN[heiti]


def skra_fjarlaegdarfall(samband: Connection) -> None:
    """Skráir ``fjarlaegd_metrar(lat, lon, lat0, lon0)`` á tenginguna.

    Án þess er ekki hægt að raða eftir fjarlægð í SQL og spurningin „hver er
    næsta stöð?" yrði að færast upp í Python. ``deterministic=True`` er óhætt:
    fallið les engin ytri gögn og skilar sama svari fyrir sömu hnit.
    """
    samband.create_function(
        FJARLAEGDARFALL,
        4,
        lambda lat, lon, lat0, lon0: haversine_km(lat0, lon0, lat, lon) * METRAR_I_KM,
        deterministic=True,
    )


def _saekja(samband: Connection, heiti: str, breytur: tuple = ()) -> list[Row]:
    """Keyrir nefnda fyrirspurn með breytum og skilar öllum röðum."""
    return samband.execute(fyrirspurn(heiti), breytur).fetchall()


def allar_stodvar(samband: Connection) -> list[Row]:
    """Ósíað: allar stöðvar sem eintakið þekkir."""
    return _saekja(samband, "allar_stodvar")


def fjoldi_stodva(samband: Connection) -> int:
    """Fjöldi stöðva í töflunni."""
    return int(_saekja(samband, "fjoldi_stodva")[0]["fjoldi"])


def stod_eftir_audkenni(samband: Connection, audkenni: int) -> Row | None:
    """Sama og ``station_id=<n>``: ein stöð sótt beint, eða ``None`` finnist hún ekki."""
    radir = _saekja(samband, "stod_eftir_audkenni", (audkenni,))
    return radir[0] if radir else None


def virkar_stodvar(samband: Connection) -> list[Row]:
    """Sama og ``active=true``: stöðvar sem mæla enn (``end_year IS NULL``)."""
    return _saekja(samband, "virkar_stodvar")


def fjoldi_virkra(samband: Connection) -> int:
    """Fjöldi stöðva sem mæla enn."""
    return int(_saekja(samband, "fjoldi_virkra")[0]["fjoldi"])


def _marghyrningsbreytur(mork: tuple[float, float, float, float]) -> tuple[float, ...]:
    """Raðar mörkum kassans í þá röð sem fyrirspurnin væntir.

    ``mork`` er á sama sniði og ``vedurstodvar_samanburdur.kassi`` skilar,
    þ.e. (lengd-lágmark, breidd-lágmark, lengd-hámark, breidd-hámark) eins og í
    WKT. Fyrirspurnin síar breidd á undan lengd, svo röðinni er snúið hér á
    einum stað í stað þess að kallendur muni hana.
    """
    min_lengd, min_breidd, max_lengd, max_breidd = mork
    return (min_breidd, max_breidd, min_lengd, max_lengd)


def stodvar_i_marghyrningi(
    samband: Connection, mork: tuple[float, float, float, float]
) -> list[Row]:
    """Sama og ``polygon=<WKT>``: stöðvar innan kassans um viðmiðunarpunktinn."""
    return _saekja(samband, "stodvar_i_marghyrningi", _marghyrningsbreytur(mork))


def virkar_stodvar_i_marghyrningi(
    samband: Connection, mork: tuple[float, float, float, float]
) -> list[Row]:
    """Sama og ``polygon=<WKT>&active=true``: báðar síur í sömu fyrirspurn."""
    return _saekja(samband, "virkar_stodvar_i_marghyrningi", _marghyrningsbreytur(mork))


def naesta_virka_stod(samband: Connection, breidd: float, lengd: float) -> Row | None:
    """Næsta stöð við hnitin sem mælir enn, með fjarlægð í metrum."""
    radir = _saekja(samband, "naesta_virka_stod", (breidd, lengd))
    return radir[0] if radir else None


def naesta_aflagda_stod(samband: Connection, breidd: float, lengd: float) -> Row | None:
    """Næsta stöð sem er hætt mælingum — til samanburðar við þá virku."""
    radir = _saekja(samband, "naesta_aflagda_stod", (breidd, lengd))
    return radir[0] if radir else None


def naesta_virka_langtimastod(
    samband: Connection, breidd: float, lengd: float, fra_ari: int
) -> Row | None:
    """Næsta virka stöð sem mælir aftur til ``fra_ari``.

    Nálægð og samfelld tímaröð eru tvö ólík skilyrði og sama stöðin uppfyllir
    sjaldnast bæði — þess vegna er þetta sérstök fyrirspurn en ekki sía ofan á
    þá næstu.
    """
    radir = _saekja(samband, "naesta_virka_langtimastod", (breidd, lengd, fra_ari))
    return radir[0] if radir else None
