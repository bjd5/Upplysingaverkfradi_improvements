"""Útflutningur regex-æfingarinnar í ``web/gogn/mbl.json`` (issue #15, #23).

Les **eingöngu** úr grunninum (migration 005) gegnum ``mbl-eintok`` og
``mbl-svor``. Skráin ber það sem ``web/sidur/mbl-regex.html`` þarf:

* ``gogn`` — spurningarnar fimm, hver með svarinu, **mynstrinu sjálfu**
  orðréttu (svo JS-ið harðkóði aldrei regex-streng), flöggunum, afmörkun
  leitarsvæðisins, fjölda tilvika, sýnishorni og þekktum takmörkunum.
* ``lysigogn`` — eintakið sem var lesið (slóð, sóknartími, skrá, MD5, stærð)
  og öll eintök í grunninum, svo síðan geti sagt að tölurnar eigi aðeins við
  þetta eina eintak af síbreytilegri forsíðu.

Liggi fleiri en eitt eintak í grunninum er **nýjasta** eintakið flutt út.

``uppfaert`` er sóknartími eintaksins (``mbl_snapshots.fetched_at``), styttur
í heilar sekúndur. **Leyfið er ekki til sem gögn:** fréttaefni mbl.is er
höfundarréttarvarið (``docs/heimildir.md``, haus migration 005); aðeins
niðurstöður og stutt sýnishorn fara út, aldrei HTML-ið.

Gildin eru óbreytt úr grunninum; heiltölur fara út sem heiltölur og gengið
með tveimur aukastöfum eins og gamla síðan birti það.
"""

from __future__ import annotations

from sqlite3 import Connection, Row
from typing import Any
from urllib.parse import urlsplit

from gagnagrunnur import fyrirspurnir

from .json_skrif import UtflutningsVilla, byggja_umslag, utc_timastimpill

SKRAARHEITI = "mbl.json"
LEYFI = "höfundarréttarvarið fréttaefni; aðeins niðurstöður birtar"
HRAGAGNAMAPPA = "data/raw/mbl/"
AUKASTAFIR = 2
FJOLDI_SPURNINGA = 5


def _gildi(tala: float) -> float | int:
    return int(tala) if float(tala).is_integer() else round(tala, AUKASTAFIR)


def _eintak(rad: Row) -> dict[str, Any]:
    return {"sott": utc_timastimpill(rad["fetched_at"]), "slod": rad["source_url"],
            "hraskra": HRAGAGNAMAPPA + rad["raw_file"], "md5": rad["md5"],
            "baeti": rad["content_length_bytes"], "http_stada": rad["status_code"]}


def _svar(rad: Row) -> dict[str, Any]:
    return {
        "nr": rad["nr"], "lykill": rad["lykill"], "spurning": rad["spurning"],
        "gildi": _gildi(rad["gildi"]), "svar": rad["svar"], "eining": rad["eining"],
        "mynstur_heiti": rad["mynsturheiti"], "mynstur": rad["mynstur"],
        "mynstur_flogg": rad["mynsturflogg"], "afmorkun_heiti": rad["afmorkun"],
        "afmorkun_mynstur": rad["afmorkunarmynstur"], "tilvik": rad["tilvik"],
        "einstok": rad["einstok"], "synishorn": rad["synishorn"],
        "takmarkanir": rad["takmarkanir"],
    }


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``mbl.json``."""
    eintok = fyrirspurnir.keyra(samband, "mbl-eintok")
    if not eintok:
        raise UtflutningsVilla("Ekkert mbl-eintak í grunninum — er það hlaðið (--skref hlada)?")
    nyjast = eintok[-1]
    svor = fyrirspurnir.keyra(samband, "mbl-svor", (nyjast["fetched_at"], None, None))
    if len(svor) != FJOLDI_SPURNINGA:
        raise UtflutningsVilla(
            f"Eintakið {nyjast['raw_file']} á {len(svor)} svör í grunninum, ekki {FJOLDI_SPURNINGA}."
        )
    slod = urlsplit(nyjast["source_url"])
    return byggja_umslag(
        uppfaert=nyjast["fetched_at"],
        heimild=f"{slod.netloc.removeprefix('www.')} — {slod.netloc}{slod.path} ({LEYFI})",
        gogn=[_svar(rad) for rad in svor],
        lysigogn={"eintak": _eintak(nyjast), "eintok": [_eintak(rad) for rad in eintok],
                  "aukastafir": AUKASTAFIR},
    )
