"""Útflutningur veðurstöðvanna í ``web/gogn/vedurstodvar.json`` (issue #15).

Les **eingöngu** úr grunninum (``weather_stations`` úr migration 004 og
``fetch_log``). Síurnar og stöðvavalið koma úr ``vinnsla.vedurstodvar_fyrirspurnir``
— sömu ``src/sql/queries/vedurstodvar-*.sql`` og #8/#11 prófuðu gegn gömlu
síðunni — og sóknin úr ``vedurstodvar-sokn.sql``. Skráin ber það sem
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

**Námundun í útflutningi.** Fyrirspurnirnar skila óafrúnnaðri fjarlægð;
metrar, fjarlægðarmunur og hlutfall virkra eru námunduð hér með Python
(``docs/adferdafraedi.md`` 4.1), munurinn á óafrúnnuðum fjarlægðum eins og
``vinnsla.vedurstodvar_mat`` gerir.

Forsendur æfingarinnar (hnit VR-II, 5 km, stöð 1469, 50 ár) eru inntak, ekki
gögn, og koma úr ``vinnsla.vedurstodvar_samanburdur`` þar sem #8 skráði þær.
"""

from __future__ import annotations

import json
from sqlite3 import Connection, Row
from typing import Any
from urllib.parse import urlsplit

from gagnagrunnur import fyrirspurnir
from vinnsla import vedurstodvar_fyrirspurnir as siur
from vinnsla.vedurstodvar_hledsla import THJONUSTA
from vinnsla.vedurstodvar_mat import hlutfall_prosent
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

from .json_skrif import UtflutningsVilla, byggja_umslag, ein_rod

SKRAARHEITI = "vedurstodvar.json"

UTGEFANDI = "Veðurstofa Íslands"
# Leyfið er skráð í data/raw/vedurstodvar/provenance.json og í haus migration
# 004; grunnurinn geymir það ekki og því stendur það hér.
LEYFI = "CC BY 4.0"
VIDMIDUNARSTADUR = "VR-II"
MORK = kassi(VR_II_BREIDD, VR_II_LENGD, RADIUS_KM)


def _heimild(endapunktur: str) -> str:
    slod = urlsplit(endapunktur)
    return f"{UTGEFANDI} — {slod.netloc}{slod.path} ({LEYFI})"


def _kassi() -> dict[str, float]:
    min_lengd, min_breidd, max_lengd, max_breidd = MORK
    return {"min_breidd": min_breidd, "max_breidd": max_breidd,
            "min_lengd": min_lengd, "max_lengd": max_lengd}


def _stod(stod: dict | None, spurning: str) -> dict[str, Any]:
    """Stöð úr svari við spurningu; ekkert svar er villa, ekki ``null`` á síðunni."""
    if stod is None:
        raise UtflutningsVilla(f"Engin stöð svarar spurningunni „{spurning}“.")
    return {"audkenni": stod["station_id"], "nafn": stod["name"], "metrar": stod["metrar"],
            "upphafsar": stod["start_year"], "lokaar": stod["end_year"]}


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
    """Beiðnirnar fimm úr töflu gömlu síðunnar: fjöldi stöðva í svari við hverri."""
    valin = siur.stod_eftir_audkenni(samband, VALIN_STOD)
    return [
        {"faeribreytur": "engin sía", "lysing": "allar stöðvar sem þjónustan þekkir",
         "fjoldi": siur.fjoldi_stodva(samband)},
        {"faeribreytur": "active=true", "lysing": "aðeins stöðvar sem mæla enn",
         "fjoldi": siur.fjoldi_virkra(samband)},
        {"faeribreytur": "polygon",
         "lysing": f"aðeins stöðvar innan {RADIUS_KM:g} km kassans um {VIDMIDUNARSTADUR}",
         "fjoldi": len(siur.stodvar_i_marghyrningi(samband, MORK))},
        {"faeribreytur": "polygon + active=true", "lysing": "hvort tveggja í sömu beiðni",
         "fjoldi": len(siur.virkar_stodvar_i_marghyrningi(samband, MORK))},
        {"faeribreytur": f"station_id={VALIN_STOD}",
         "lysing": "stöðin sem forritið les, sótt beint", "fjoldi": 0 if valin is None else 1},
    ]


def _svor(samband: Connection) -> dict[str, Any]:
    """Svörin við spurningum æfingarinnar."""
    allar, virkar = siur.fjoldi_stodva(samband), siur.fjoldi_virkra(samband)
    vidmidunarar = VIDMIDSAR - AR_AFTUR_I_TIMANN
    naesta = siur.naesta_virka_stod(samband, VR_II_BREIDD, VR_II_LENGD)
    aflogd = siur.naesta_aflagda_stod(samband, VR_II_BREIDD, VR_II_LENGD)
    langtima = siur.naesta_virka_langtimastod(samband, VR_II_BREIDD, VR_II_LENGD, vidmidunarar)
    naesta_stod = _stod(naesta, "næsta virka stöð")
    aflogd_stod = _stod(aflogd, "næsta aflagða stöð")
    return {
        "fjoldi_allra": allar,
        "fjoldi_virkra": virkar,
        "fjoldi_aflagdra": allar - virkar,
        "hlutfall_virkra_prosent": hlutfall_prosent(virkar, allar),
        "naesta_virka": naesta_stod,
        "naesta_aflagda": aflogd_stod,
        # Á óafrúnnuðum fjarlægðum, rúnnað í lokin — eins og gamla skriftan.
        "munur_metrar": round(abs(aflogd["distance_m"] - naesta["distance_m"])),
        "ar_aftur_i_timann": AR_AFTUR_I_TIMANN,
        "vidmidunarar": vidmidunarar,
        "valin_naer_aftur": naesta_stod["upphafsar"] <= vidmidunarar,
        "langtimastod": _stod(langtima, f"næsta virka stöð sem mælir frá {vidmidunarar}"),
    }


def _stodvar_i_kassa(samband: Connection) -> list[dict[str, Any]]:
    """Stöðvarnar í kassanum, næsta fyrst (röðin kemur úr SQL)."""
    return [
        {"audkenni": stod["station_id"], "nafn": stod["name"],
         "upphafsar": stod["start_year"], "lokaar": stod["end_year"],
         "virk": bool(stod["is_active"]), "metrar": stod["metrar"]}
        for stod in siur.kassi_eftir_fjarlaegd(samband, VR_II_BREIDD, VR_II_LENGD, MORK)
    ]


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``vedurstodvar.json``."""
    siur.skra_fjarlaegdarfall(samband)
    sokn = ein_rod(fyrirspurnir.keyra(samband, "vedurstodvar-sokn", (THJONUSTA,)),
                   "vedurstodvar-sokn")
    beidnir = _beidnir(samband)
    if beidnir[0]["fjoldi"] != sokn["record_count"]:
        raise UtflutningsVilla(
            f"fetch_log skráir {sokn['record_count']} stöðvar en taflan geymir "
            f"{beidnir[0]['fjoldi']}. Grunnurinn er ekki heil hleðsla eintaksins."
        )
    lysigogn = {
        "sokn": {"endapunktur": sokn["endpoint"], "faeribreytur": _faeribreytur(sokn),
                 "hraskra": sokn["raw_file"], "fjoldi_stodva": sokn["record_count"]},
        "vidmidunarpunktur": {"heiti": VIDMIDUNARSTADUR, "breidd": VR_II_BREIDD,
                              "lengd": VR_II_LENGD, "heimild": VR_II_HEIMILD,
                              "radius_km": RADIUS_KM, "kassi": _kassi()},
        "beidnir": beidnir,
        "svor": _svor(samband),
    }
    return byggja_umslag(
        uppfaert=sokn["fetched_at"], heimild=_heimild(sokn["endpoint"]),
        gogn=_stodvar_i_kassa(samband), lysigogn=lysigogn,
    )
