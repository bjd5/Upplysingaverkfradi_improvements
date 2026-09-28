"""Útflutningur veðurstöðvanna í ``web/gogn/vedurstodvar.json`` (issue #15).

Les **eingöngu** úr grunninum (``weather_stations`` úr migration 004 og
``fetch_log``). Síurnar koma úr ``src/sql/queries/vedurstodvar-siur.sql`` (þær
sömu og #8 prófaði gegn gömlu síðunni) og samantektirnar úr
``vedurstodvar-utflutningur.sql``. Skráin ber það sem
``web/sidur/vedurstodvar.html`` þarf (issue #22):

* ``gogn`` — stöðvarnar innan 5 km kassans um VR-II, raðaðar eftir fjarlægð,
  hver merkt virk eða aflögð. Þetta eru stöðvarnar sem síurnar skila
  (``polygon``; ``virk`` segir hverjar standast ``active=true`` líka).
* ``lysigogn.sokn`` — hvaða eintak, af hvaða slóð, hvenær sótt. Síðan á að
  sýna sóknardagsetninguna áberandi: þetta er frosið eintak, ekki lifandi staða.
* ``lysigogn.beidnir`` — beiðnirnar fimm og fjöldi stöðva í svari við hverri.
  Heiti færibreytanna eru rituð eins og í töflu gömlu síðunnar.
* ``lysigogn.svor`` — svörin við spurningum æfingarinnar.

**Af hverju ``uppfaert`` er sóknartíminn.** ``uppfaert`` er
``fetch_log.fetched_at`` þessa safns, 2026-09-24T11:22:18Z úr provenance.json —
ekki klukkan við útflutning. Stöðvaskráin er frosið eintak; lesandinn þarf að
vita hvenær það var tekið, og tvær útflutningskeyrslur á sama grunni eiga að
gefa sömu bæti.

Forsendur æfingarinnar (hnit VR-II, 5 km, stöð 1469, 50 ár) eru inntak, ekki
gögn, og koma úr ``vinnsla.vedurstodvar_samanburdur`` þar sem #8 skráði þær.
"""

from __future__ import annotations

import json
from sqlite3 import Connection, Row
from typing import Any
from urllib.parse import urlsplit

from vinnsla import vedurstodvar_fyrirspurnir as siur
from vinnsla.vedurstodvar_hledsla import THJONUSTA
from vinnsla.vedurstodvar_samanburdur import (
    AR_AFTUR_I_TIMANN,
    RADIUS_KM,
    VALIN_STOD,
    VIDMIDSAR,
    VR_II_BREIDD,
    VR_II_HEIMILD,
    VR_II_LENGD,
    kassi,
)

from .json_skrif import UtflutningsVilla, byggja_umslag
from .sql_safn import FYRIRSPURNAMAPPA, Fyrirspurnasafn

SKRAARHEITI = "vedurstodvar.json"
SAFN = Fyrirspurnasafn(FYRIRSPURNAMAPPA / "vedurstodvar-utflutningur.sql")

UTGEFANDI = "Veðurstofa Íslands"
# Leyfið er skráð í data/raw/vedurstodvar/provenance.json og í haus migration
# 004; grunnurinn geymir það ekki og því stendur það hér.
LEYFI = "CC BY 4.0"
VIDMIDUNARSTADUR = "VR-II"
# Fjórir aukastafir (~10 m) — sama nákvæmni og WKT-kassinn sem var sendur.
HNITAAUKASTAFIR = 4


def _heimild(endapunktur: str) -> str:
    slod = urlsplit(endapunktur)
    return f"{UTGEFANDI} — {slod.netloc}{slod.path} ({LEYFI})"


def _kassabreytur() -> dict[str, float]:
    min_lengd, min_breidd, max_lengd, max_breidd = kassi(VR_II_BREIDD, VR_II_LENGD, RADIUS_KM)
    return {"min_breidd": min_breidd, "max_breidd": max_breidd,
            "min_lengd": min_lengd, "max_lengd": max_lengd}


def _stadsetning() -> dict[str, float]:
    return {"breidd": VR_II_BREIDD, "lengd": VR_II_LENGD}


def _stod(rod: Row | None, spurning: str) -> dict[str, Any]:
    """Stöð úr svari við spurningu; ekkert svar er villa, ekki ``null`` á síðunni."""
    if rod is None:
        raise UtflutningsVilla(f"Engin stöð svarar spurningunni „{spurning}“.")
    return {"audkenni": rod["station_id"], "nafn": rod["name"], "metrar": rod["metrar"],
            "upphafsar": rod["start_year"], "lokaar": rod["end_year"]}


def _sokn(samband: Connection) -> Row:
    return SAFN.ein_rod(samband, "sokn", {"thjonusta": THJONUSTA})


def _faeribreytur(sokn: Row) -> dict[str, Any]:
    """Færibreyturnar sem sóknin sendi, geymdar sem JSON í ``fetch_log.params``."""
    try:
        faeribreytur = json.loads(sokn["params"])
    except (TypeError, json.JSONDecodeError) as villa:
        raise UtflutningsVilla("fetch_log.params veðurstöðvanna er ekki gilt JSON.") from villa
    if not isinstance(faeribreytur, dict):
        raise UtflutningsVilla("fetch_log.params veðurstöðvanna á að vera JSON-hlutur.")
    return faeribreytur


def _beidnir(samband: Connection) -> list[dict[str, Any]]:
    """Beiðnirnar fimm úr töflu gömlu síðunnar, taldar í SQL."""
    allt = SAFN.ein_rod(samband, "fjoldatolur")
    i_kassa = SAFN.ein_rod(samband, "fjoldi_i_kassa", _kassabreytur())
    med_audkenni = SAFN.ein_rod(samband, "fjoldi_med_audkenni", {"stod": VALIN_STOD})
    return [
        {"faeribreytur": "engin sía", "lysing": "allar stöðvar sem þjónustan þekkir",
         "fjoldi": allt["allar"]},
        {"faeribreytur": "active=true", "lysing": "aðeins stöðvar sem mæla enn",
         "fjoldi": allt["virkar"]},
        {"faeribreytur": "polygon",
         "lysing": f"aðeins stöðvar innan {RADIUS_KM:g} km kassans um {VIDMIDUNARSTADUR}",
         "fjoldi": i_kassa["allar"]},
        {"faeribreytur": "polygon + active=true", "lysing": "hvort tveggja í sömu beiðni",
         "fjoldi": i_kassa["virkar"]},
        {"faeribreytur": f"station_id={VALIN_STOD}",
         "lysing": "stöðin sem forritið les, sótt beint", "fjoldi": med_audkenni["fjoldi"]},
    ]


def _svor(samband: Connection) -> dict[str, Any]:
    """Svörin við spurningum æfingarinnar — hver tala úr SQL."""
    fjoldi = SAFN.ein_rod(samband, "fjoldatolur")
    vidmidunarar = VIDMIDSAR - AR_AFTUR_I_TIMANN
    naesta = _stod(siur.naesta_virka_stod(samband, VR_II_BREIDD, VR_II_LENGD),
                   "næsta virka stöð")
    aflogd = _stod(siur.naesta_aflagda_stod(samband, VR_II_BREIDD, VR_II_LENGD),
                   "næsta aflagða stöð")
    langtima = _stod(
        siur.naesta_virka_langtimastod(samband, VR_II_BREIDD, VR_II_LENGD, vidmidunarar),
        f"næsta virka stöð sem mælir frá {vidmidunarar}",
    )
    munur = SAFN.ein_rod(samband, "munur_aflagdrar_og_virkrar", _stadsetning())
    return {
        "fjoldi_allra": fjoldi["allar"],
        "fjoldi_virkra": fjoldi["virkar"],
        "fjoldi_aflagdra": fjoldi["aflagdar"],
        "hlutfall_virkra_prosent": fjoldi["hlutfall_virkra_prosent"],
        "naesta_virka": naesta,
        "naesta_aflagda": aflogd,
        "munur_metrar": munur["munur_metrar"],
        "ar_aftur_i_timann": AR_AFTUR_I_TIMANN,
        "vidmidunarar": vidmidunarar,
        "valin_naer_aftur": naesta["upphafsar"] <= vidmidunarar,
        "langtimastod": langtima,
    }


def _stodvar_i_kassa(samband: Connection) -> list[dict[str, Any]]:
    breytur = {**_kassabreytur(), **_stadsetning(), "hnitaaukastafir": HNITAAUKASTAFIR}
    return [
        {"audkenni": rod["station_id"], "nafn": rod["name"], "tegund": rod["station_type"],
         "breidd": rod["lat"], "lengd": rod["lon"], "haed_m": rod["elevation_m"],
         "upphafsar": rod["start_year"], "lokaar": rod["end_year"],
         "virk": bool(rod["virk"]), "metrar": rod["metrar"]}
        for rod in SAFN.radir(samband, "stodvar_i_kassa", breytur)
    ]


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``vedurstodvar.json``."""
    siur.skra_fjarlaegdarfall(samband)
    sokn = _sokn(samband)
    gogn = _stodvar_i_kassa(samband)
    beidnir = _beidnir(samband)
    if beidnir[0]["fjoldi"] != sokn["record_count"]:
        raise UtflutningsVilla(
            f"fetch_log skráir {sokn['record_count']} stöðvar en taflan geymir "
            f"{beidnir[0]['fjoldi']}. Grunnurinn er ekki heil hleðsla eintaksins."
        )
    lysigogn = {
        "sokn": {"endapunktur": sokn["endpoint"], "faeribreytur": _faeribreytur(sokn),
                 "hraskra": sokn["raw_file"],
                 "fjoldi_stodva": sokn["record_count"]},
        "vidmidunarpunktur": {"heiti": VIDMIDUNARSTADUR, **_stadsetning(),
                              "heimild": VR_II_HEIMILD, "radius_km": RADIUS_KM,
                              "kassi": _kassabreytur()},
        "beidnir": beidnir,
        "svor": _svor(samband),
    }
    return byggja_umslag(
        uppfaert=sokn["fetched_at"], heimild=_heimild(sokn["endpoint"]),
        gogn=gogn, lysigogn=lysigogn,
    )
