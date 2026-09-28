"""``web/gogn/vedurstodvar.json`` — stöðvaskrá Veðurstofunnar (issue #22).

Svörin við spurningum æfingarinnar koma úr SQL gegnum
``vinnsla.vedurstodvar_fyrirspurnir``, sem keyrir ``src/sql/queries/vedurstodvar-*.sql``
með sameiginlega lesaranum. Sóknartíminn og slóðin koma úr ``fetch_log``
(``gagnasofnun-skraning``); þjónustuheitið og leyfið eru ekki í grunninum og
eru lesin úr ``data/raw/vedurstodvar/provenance.json`` — sömu skrá og hleðslan
sannreyndi eintakið gegn.

**Frosið eintak, ekki lifandi staða** (#22): ``gogn["uppruni"]["sott"]`` er
sóknartíminn og ``frosid_eintak`` er alltaf ``true``, svo síðan geti sagt það
áberandi.

Aðeins stöðvarnar innan kassans um VR-II fara út (súluritið og taflan), ekki
allar 778 — samantektir, ekki heilar töflur (#15).

Námundun: fjarlægðir í heilum metrum og hlutfall í heilum prósentum, eins og
gamla síðan birti. Röðun og mismunur eru reiknuð á óafrúnnaðri fjarlægð.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur import fyrirspurnir
from vinnsla import vedurstodvar_fyrirspurnir as spurn
from vinnsla import vedurstodvar_samanburdur as sam
from vinnsla.vedurstodvar_hledsla import FROSID, PROVENANCE, THJONUSTA

from .skjal import Uppruni, UtflutningsVilla, ein_rod, lesa_provenance, skjal

SKRA = "vedurstodvar.json"
SIDA = "web/sidur/vedurstodvar.html"
PROVENANCE_REITIR = ("provider", "license")
PROSENT = 100

FYRIRSPURNIR = (
    "gagnasofnun-skraning",
    "vedurstodvar-fjoldi-stodva",
    "vedurstodvar-fjoldi-virkra",
    "vedurstodvar-stodvar-i-marghyrningi",
    "vedurstodvar-virkar-stodvar-i-marghyrningi",
    "vedurstodvar-stod-eftir-audkenni",
    "vedurstodvar-kassi-eftir-fjarlaegd",
    "vedurstodvar-naesta-virka-stod",
    "vedurstodvar-naesta-aflagda-stod",
    "vedurstodvar-naesta-virka-langtimastod",
)


def _stod(rad: dict | None) -> dict | None:
    if rad is None:
        return None
    return {
        "station_id": rad["station_id"],
        "nafn": rad["name"],
        "metrar": rad["metrar"],
        "fyrsta_ar": rad["start_year"],
        "lokaar": rad["end_year"],
        "virk": rad["end_year"] is None,
    }


def _beidnir(samband: Connection, mork: tuple[float, float, float, float]) -> list[dict]:
    """Beiðnirnar fimm sem gamla síðan sendi, framkvæmdar sem SQL á eintakinu."""
    audkenni = spurn.stod_eftir_audkenni(samband, sam.VALIN_STOD)
    return [
        {"sia": "engin sía", "fjoldi": spurn.fjoldi_stodva(samband)},
        {"sia": "active=true", "fjoldi": spurn.fjoldi_virkra(samband)},
        {"sia": "polygon", "fjoldi": len(spurn.stodvar_i_marghyrningi(samband, mork))},
        {"sia": "polygon + active=true",
         "fjoldi": len(spurn.virkar_stodvar_i_marghyrningi(samband, mork))},
        {"sia": f"station_id={sam.VALIN_STOD}", "fjoldi": 0 if audkenni is None else 1},
    ]


def _svor(samband: Connection, kassi: list[dict], fjoldi: int, virkar: int) -> dict:
    """Svör æfingarinnar: næsta stöð, næsta virka og aflagða, hlutfall, langtímastöð."""
    breidd, lengd = sam.VR_II_BREIDD, sam.VR_II_LENGD
    vidmidunarar = sam.VIDMIDSAR - sam.AR_AFTUR_I_TIMANN
    virk = spurn.naesta_virka_stod(samband, breidd, lengd)
    aflogd = spurn.naesta_aflagda_stod(samband, breidd, lengd)
    langtima = spurn.naesta_virka_langtimastod(samband, breidd, lengd, vidmidunarar)
    if virk is None or not kassi:
        raise UtflutningsVilla("Engin stöð eða engin virk stöð fannst við VR-II.")
    munur = None if aflogd is None else round(abs(aflogd["distance_m"] - virk["distance_m"]))
    return {
        "naesta": _stod(kassi[0]),
        "naesta_virka": _stod(virk),
        "naesta_aflogd": _stod(aflogd),
        "munur_metrar": munur,
        "fjoldi_virkra": virkar,
        "fjoldi_allra": fjoldi,
        "hlutfall_virkra_prosent": round(PROSENT * virkar / fjoldi),
        "ar_aftur_i_timann": sam.AR_AFTUR_I_TIMANN,
        "vidmidunarar": vidmidunarar,
        "naesta_virka_naer_aftur": virk["start_year"] <= vidmidunarar,
        "langtimastod": _stod(langtima),
    }


def byggja(samband: Connection, mappa: Path = FROSID) -> dict:
    """Skráin sem veðurstöðvasíðan les. Kallandinn skráir ``fjarlaegd_metrar`` á tenginguna."""
    provenance = lesa_provenance(mappa / PROVENANCE, PROVENANCE_REITIR)
    skraning = ein_rod(fyrirspurnir.keyra(samband, "gagnasofnun-skraning", (THJONUSTA,)),
                       THJONUSTA)
    uppruni = Uppruni(
        thjonusta=str(provenance["provider"]),
        slod=str(skraning["endpoint"]),
        leyfi=str(provenance["license"]),
        sott=str(skraning["fetched_at"]),
        hragogn=str(skraning["raw_file"]),
    )
    mork = sam.kassi(sam.VR_II_BREIDD, sam.VR_II_LENGD, sam.RADIUS_KM)
    kassi = spurn.kassi_eftir_fjarlaegd(samband, sam.VR_II_BREIDD, sam.VR_II_LENGD, mork)
    fjoldi, virkar = spurn.fjoldi_stodva(samband), spurn.fjoldi_virkra(samband)
    if fjoldi != skraning["record_count"]:
        raise UtflutningsVilla(
            f"fetch_log segir {skraning['record_count']} stöðvar en taflan hefur {fjoldi}."
        )
    gogn = {
        "uppruni": {**uppruni.sem_gogn(), "frosid_eintak": True},
        "vidmidunarpunktur": {
            "heiti": "VR-II",
            "breidd": sam.VR_II_BREIDD,
            "lengd": sam.VR_II_LENGD,
            "heimild": sam.VR_II_HEIMILD,
            "radius_km": sam.RADIUS_KM,
            "kassi": {"lengd_min": mork[0], "breidd_min": mork[1],
                      "lengd_max": mork[2], "breidd_max": mork[3]},
        },
        "beidnir": _beidnir(samband, mork),
        "svor": _svor(samband, kassi, fjoldi, virkar),
        "stodvar_i_kassa": [{**_stod(rad), "rod": rad["distance_rank"]} for rad in kassi],
    }
    return skjal(uppruni, gogn)
