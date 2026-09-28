"""Síurnar úr veðurstöðvaæfingunni, framkvæmdar sem SQL á ``weather_stations``.

Gamla verkefnið sendi hverja síu sem sérstaka beiðni til þjónustunnar —
``station_id=``, ``active=true`` og ``polygon=`` — og treysti henni fyrir
svarinu. Hér er sama síun gerð á frosna eintakinu í grunninum. Það er tilgangur
æfingarinnar: sama spurning, sama svar, en netlaust og endurtekjanlegt.

SQL-ið sjálft er í ``src/sql/queries/vedurstodvar-*.sql`` — ein skrá á hverja
fyrirspurn — og er lesið með sameiginlega lesaranum ``gagnagrunnur.fyrirspurnir``
(#11). Fyrirspurn sem er afrituð inn í Python fer fyrr eða síðar á skjön við
skrána sem á að vera heimildin.

**Öll gildi fara inn sem breytur** (``cur.execute(sql, (gildi,))``) — engin
fyrirspurn hér er sett saman úr strengjum (regla 5).

Fjarlægðarreikningurinn kemur úr ``vedurstodvar_samanburdur`` og er skráður á
tenginguna sem SQL-fallið ``fjarlaegd_metrar``, svo röðun eftir fjarlægð gerist
í fyrirspurninni og noti sömu formúlu og samanburðurinn við gömlu síðuna.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from sqlite3 import Connection, Row

from gagnagrunnur import fyrirspurnir

from .vedurstodvar_samanburdur import haversine_km

# Forskeyti skránna í src/sql/queries/. Heiti fallanna hér eru með undirstriki
# (``naesta_virka_stod``), skrárnar með bandstriki (regla 1.2).
FORSKEYTI = "vedurstodvar-"

FJARLAEGDARFALL = "fjarlaegd_metrar"
METRAR_I_KM = 1000.0

FyrirspurnaVilla = fyrirspurnir.FyrirspurnaVilla


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
    """Keyrir ``vedurstodvar-<heiti>.sql`` með breytum og skilar öllum röðum."""
    return fyrirspurnir.keyra(samband, FORSKEYTI + heiti.replace("_", "-"), breytur)


def _i_metrum(rad: Row | None) -> dict | None:
    """Röðin með fjarlægð í heilum metrum, eins og síðan birtir hana.

    SQL skilar óafrúnnaðri fjarlægð (``distance_m``) og raðar á henni; hér er
    námundað í birtingarnákvæmni með ``round`` — sama venja og
    ``vedurstodvar_mat`` og öll birting (``docs/adferdafraedi.md`` 4.1).
    """
    if rad is None:
        return None
    gildi = dict(rad)
    gildi["metrar"] = round(gildi["distance_m"])
    return gildi


def allar_stodvar(samband: Connection) -> list[Row]:
    """Ósíað: allar stöðvar sem eintakið þekkir."""
    return _saekja(samband, "allar_stodvar")


def fjoldi_stodva(samband: Connection) -> int:
    """Fjöldi stöðva í töflunni."""
    return int(_saekja(samband, "fjoldi_stodva")[0]["station_count"])


def stod_eftir_audkenni(samband: Connection, audkenni: int) -> Row | None:
    """Sama og ``station_id=<n>``: ein stöð sótt beint, eða ``None`` finnist hún ekki."""
    radir = _saekja(samband, "stod_eftir_audkenni", (audkenni,))
    return radir[0] if radir else None


def virkar_stodvar(samband: Connection) -> list[Row]:
    """Sama og ``active=true``: stöðvar sem mæla enn (``end_year IS NULL``)."""
    return _saekja(samband, "virkar_stodvar")


def fjoldi_virkra(samband: Connection) -> int:
    """Fjöldi stöðva sem mæla enn."""
    return int(_saekja(samband, "fjoldi_virkra")[0]["station_count"])


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


def naesta_virka_stod(samband: Connection, breidd: float, lengd: float) -> dict | None:
    """Næsta stöð við hnitin sem mælir enn, með fjarlægð í heilum metrum (``metrar``)."""
    radir = _saekja(samband, "naesta_virka_stod", (breidd, lengd))
    return _i_metrum(radir[0] if radir else None)


def naesta_aflagda_stod(samband: Connection, breidd: float, lengd: float) -> dict | None:
    """Næsta stöð sem er hætt mælingum — til samanburðar við þá virku."""
    radir = _saekja(samband, "naesta_aflagda_stod", (breidd, lengd))
    return _i_metrum(radir[0] if radir else None)


def naesta_virka_langtimastod(
    samband: Connection, breidd: float, lengd: float, fra_ari: int
) -> dict | None:
    """Næsta virka stöð sem mælir aftur til ``fra_ari``.

    Nálægð og samfelld tímaröð eru tvö ólík skilyrði og sama stöðin uppfyllir
    sjaldnast bæði — þess vegna er þetta sérstök fyrirspurn en ekki sía ofan á
    þá næstu.
    """
    radir = _saekja(samband, "naesta_virka_langtimastod", (breidd, lengd, fra_ari))
    return _i_metrum(radir[0] if radir else None)


def kassi_eftir_fjarlaegd(
    samband: Connection,
    breidd: float,
    lengd: float,
    mork: tuple[float, float, float, float],
) -> list[dict]:
    """Stöðvarnar í kassanum, næsta fyrst — súluritið á síðunni.

    Sama röð og ``vedurstodvar_mat.rada_eftir_fjarlaegd``, en úr SQL. Hver röð
    ber ``metrar`` (heilir metrar, birting) við hlið óafrúnnuðu ``distance_m``.
    """
    radir = _saekja(
        samband, "kassi_eftir_fjarlaegd", (breidd, lengd, *_marghyrningsbreytur(mork))
    )
    return [_i_metrum(rad) for rad in radir]
