"""``web/gogn/mbl.json`` — regex-æfingin á fréttasíðu mbl.is (issue #23).

Svörin fimm, mynstrin sem framkölluðu þau og sýnishorn af því sem mynstrið hitti
á koma úr ``mbl-svor``; eintakið (slóð, sóknartími, skrá, MD5) úr ``mbl-eintok``.
Regex-strengirnir fara út orðréttir svo JS-ið þurfi aldrei að harðkóða þá (#23).

Liggi fleiri en eitt eintak í grunninum er **nýjasta** eintakið flutt út og öll
eintökin talin upp í ``gogn["eintok"]``, svo síðan geti sagt að tölurnar eigi
aðeins við þetta eina eintak.

**Leyfið er ekki til sem gögn.** Fréttaefni mbl.is er höfundarréttarvarið
(``docs/heimildir.md``, migration 005); aðeins niðurstöður útdráttarins og stutt
sýnishorn fara á síðuna, aldrei HTML-ið sjálft.

Gildin eru óbreytt úr grunninum (``value_number``); ``svar`` er textinn eins
og útdrátturinn sneið hann á íslensku. Tveir aukastafir duga genginu.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from sqlite3 import Connection
from urllib.parse import urlsplit

from gagnagrunnur import fyrirspurnir

from .skjal import Uppruni, UtflutningsVilla, namunda, skjal, utc_stimpill

SKRA = "mbl.json"
SIDA = "web/sidur/mbl-regex.html"
LEYFI = "höfundarréttarvarið fréttaefni — aðeins niðurstöður birtar"
AUKASTAFIR = 2
HRAGAGNAMAPPA = "data/raw/mbl/"

FYRIRSPURNIR = ("mbl-eintok", "mbl-svor")


def _eintak(rad) -> dict:
    return {
        "sott": utc_stimpill(rad["fetched_at"]),
        "slod": rad["source_url"],
        "skra": rad["raw_file"],
        "md5": rad["md5"],
        "baeti": rad["content_length_bytes"],
        "http_stada": rad["status_code"],
    }


def _svar(rad) -> dict:
    gildi = rad["gildi"]
    if float(gildi).is_integer():
        gildi = int(gildi)
    return {
        "nr": rad["nr"],
        "lykill": rad["lykill"],
        "spurning": rad["spurning"],
        "gildi": namunda(gildi, AUKASTAFIR),
        "svar": rad["svar"],
        "eining": rad["eining"],
        "mynstur_heiti": rad["mynsturheiti"],
        "mynstur": rad["mynstur"],
        "mynstur_flogg": rad["mynsturflogg"],
        "afmorkun_heiti": rad["afmorkun"],
        "afmorkun_mynstur": rad["afmorkunarmynstur"],
        "tilvik": rad["tilvik"],
        "einstok": rad["einstok"],
        "synishorn": rad["synishorn"],
        "takmarkanir": rad["takmarkanir"],
    }


def byggja(samband: Connection) -> dict:
    """Skráin sem mbl-síðan les: eintakið og svörin fimm með mynstrum sínum."""
    eintok = fyrirspurnir.keyra(samband, "mbl-eintok")
    if not eintok:
        raise UtflutningsVilla("Ekkert mbl-eintak í grunninum.")
    nyjast = eintok[-1]
    svor = fyrirspurnir.keyra(samband, "mbl-svor", (nyjast["fetched_at"], None, None))
    if not svor:
        raise UtflutningsVilla(f"Engin svör í grunninum fyrir eintakið {nyjast['raw_file']}.")
    slod = str(nyjast["source_url"])
    uppruni = Uppruni(
        thjonusta=urlsplit(slod).hostname.removeprefix("www."),
        slod=slod,
        leyfi=LEYFI,
        sott=str(nyjast["fetched_at"]),
        hragogn=HRAGAGNAMAPPA + str(nyjast["raw_file"]),
    )
    gogn = {
        "uppruni": {**uppruni.sem_gogn(), "md5": nyjast["md5"],
                    "baeti": nyjast["content_length_bytes"],
                    "http_stada": nyjast["status_code"]},
        "eintok": [_eintak(rad) for rad in eintok],
        "svor": [_svar(rad) for rad in svor],
    }
    return skjal(uppruni, gogn)
