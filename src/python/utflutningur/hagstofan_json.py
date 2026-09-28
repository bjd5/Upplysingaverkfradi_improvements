"""Útflutningur Hagstofugagnanna í ``web/gogn/hagstofan.json`` (issue #15).

Les **eingöngu** úr grunninum (migration 003 + ``fetch_log``) með sameiginlega
lesaranum ``gagnagrunnur.fyrirspurnir`` (#11). Tölurnar koma úr sömu
fyrirspurnum og viðmiðsprófin nota (``hagstofan-hlutfoll``, ``-summur``,
``-munur``); lýsigögnin úr ``hagstofan-gagnasafn``, ``-fyrirspurn``, ``-viddir``
og ``-kodabok``. Skráin ber
það sem ``web/sidur/hagstofan.html`` þarf (issue #21):

* ``gogn`` — niðurstöðutölurnar: ein lína á hverja samsetningu námssviðs og
  kyns, með stöðuflokkunum þremur og samtölu þeirra, rúnnað á einn aukastaf
  eins og gamla síðan birti.
* ``lysigogn`` — afmörkunin (innritunarár 2017, ``n+3``, hlutfall %), POST-
  beiðnin sjálf (``query.json`` úr ``fetch_log.params``), víddirnar sex með
  kóðabókinni svo síðan geti sýnt hvernig flati json-stat2-listinn er lesinn,
  og mismunirnir þrír í prósentustigum sem gamla síðan fullyrti.

**Af hverju ``uppfaert`` er sóknartíminn.** ``uppfaert`` er
``hagstofan_datasets.fetched_at`` — okkar eigin sóknartími úr provenance.json,
2026-09-10T09:02:26+00:00. Klukkan við útflutning myndi gera hverja keyrslu að
nýrri skrá án þess að nokkur tala hefði breyst, og ``updated`` úr svarinu
(9999-12-31T23:59:59Z) er ekki dagsetning. Sóknartíminn er það sem lesandinn
þarf að vita: *hversu gömul eru gögnin?* Og hann er ákvarðaður: sami grunnur
gefur sömu bæti.

**Námundun í útflutningi, ekki í vafranum og ekki í SQL.** Fyrirspurnirnar
skila óafrúnnuðu; hér er námundað með Python ``round`` — sama venja og öll
birting (``docs/adferdafraedi.md`` 4.1).

Allt eða ekkert: stemmi afmörkunin eða fjöldi mælinga ekki við það sem
skráin gerir ráð fyrir stöðvast útflutningurinn áður en nokkuð er skrifað.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from sqlite3 import Connection, Row
from typing import Any
from urllib.parse import urlsplit

from gagnagrunnur import fyrirspurnir

from .json_skrif import UtflutningsVilla, byggja_umslag, ein_rod

SKRAARHEITI = "hagstofan.json"

# Töfluauðkennið sem hleðslan (vinnsla.hagstofan) leiðir af endapunktinum.
GAGNASAFN = "SKO04208b"
UTGEFANDI = "Hagstofa Íslands"

# Gamla síðan birti einn aukastaf; námundað hér, ekki í vafranum.
AUKASTAFIR = 1

# Stöðuflokkarnir þrír sem fyrirspurnin valdi: kóði Hagstofunnar -> reitur.
STODUR: tuple[tuple[str, str], ...] = (
    ("5", "brautskradir"),
    ("6", "brottfallnir"),
    ("7", "enn_i_nami"),
)
VIDD_STODU = "Nemendur"
VIDD_SVIDS = "Námssvið"
VIDD_KYNS = "Kyn"
# Víddir með einu völdu gildi: þær eru afmörkunin, ekki sundurliðun. Hefði
# einhver þeirra fleiri en eitt gildi myndu ósambærilegar tölur lenda í sömu
# línu — þess vegna er það stöðvað.
FASTAR_VIDDIR = ("Innritunarár", "Tími", "Fjöldi/Hlutfall")

# Mismunirnir sem gamla síðan fullyrti: (lýsing, svið a, kyn a, svið b, kyn b).
SAMANBURDIR: tuple[tuple[str, str, str, str, str], ...] = (
    ("Verkfræði miðað við öll svið, bæði kyn", "07", "Alls", "Alls", "Alls"),
    ("Konur miðað við karla í verkfræði", "07", "2", "07", "1"),
    ("Konur miðað við karla á öllum sviðum", "Alls", "2", "Alls", "1"),
)


def _keyra(samband: Connection, heiti: str, *breytur: object) -> list[Row]:
    return fyrirspurnir.keyra(samband, heiti, (GAGNASAFN, *breytur))


def _runna(gildi: float) -> float:
    return round(gildi, AUKASTAFIR)


def _heimild(gagnasafn: Row) -> str:
    """„Hagstofa Íslands — <slóð án https://> (<uppruni taflunnar>)"."""
    slod = urlsplit(gagnasafn["endpoint"])
    uppruni = str(gagnasafn["source"]).strip().rstrip(".")
    return f"{UTGEFANDI} — {slod.netloc}{slod.path} ({uppruni})"


def _fyrirspurnin(samband: Connection) -> dict[str, Any]:
    """POST-beiðnin (query.json) eins og hún var geymd í ``fetch_log``."""
    rod = ein_rod(_keyra(samband, "hagstofan-fyrirspurn"), "hagstofan-fyrirspurn")
    try:
        return json.loads(rod["params"])
    except (TypeError, json.JSONDecodeError) as villa:
        raise UtflutningsVilla(
            "fetch_log.params geymir ekki gilda JSON-fyrirspurn fyrir Hagstofuna."
        ) from villa


def _viddir(samband: Connection) -> list[dict[str, Any]]:
    """Víddirnar í röð ``id`` með allri kóðabókinni undir hverri."""
    gildi: dict[str, list[dict[str, Any]]] = {}
    for rod in _keyra(samband, "hagstofan-kodabok"):
        gildi.setdefault(rod["dimension_code"], []).append(
            {"kodi": rod["code"], "heiti": rod["label"],
             "valid": bool(rod["selected"]), "stada": rod["value_index"]}
        )
    viddir = [
        {"kodi": rod["code"], "heiti": rod["label"], "stada": rod["position"],
         "staerd": rod["size"], "timavidd": bool(rod["is_time"]),
         "gildi": gildi.get(rod["code"], [])}
        for rod in _keyra(samband, "hagstofan-viddir")
    ]
    if not viddir:
        raise UtflutningsVilla(f"Engar víddir fyrir {GAGNASAFN} í grunninum — er hann hlaðinn?")
    return viddir


def _valin(vidd: dict[str, Any]) -> list[dict[str, Any]]:
    return [gildi for gildi in vidd["gildi"] if gildi["valid"]]


def _afmorkun(viddir: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Föstu víddirnar með eina valda gildinu sínu; annað er villa."""
    afmorkun = []
    for kodi in FASTAR_VIDDIR:
        valin = _valin(viddir[kodi])
        if len(valin) != 1:
            raise UtflutningsVilla(
                f"Víddin {kodi!r} á að hafa eitt valið gildi en hefur {len(valin)}. "
                "Afmörkun fyrirspurnarinnar hefur breyst og samantektin á ekki lengur við."
            )
        afmorkun.append({"vidd": kodi, "heiti": viddir[kodi]["heiti"],
                         "kodi": valin[0]["kodi"], "gildi": valin[0]["heiti"]})
    return afmorkun


def _stodur(viddir: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Stöðuflokkarnir sem dálkar, með heiti úr kóðabókinni."""
    valin = {gildi["kodi"]: gildi["heiti"] for gildi in _valin(viddir[VIDD_STODU])}
    vaent = {kodi for kodi, _ in STODUR}
    if set(valin) != vaent:
        raise UtflutningsVilla(
            f"Valdir stöðuflokkar eru {sorted(valin)} en útflutningurinn þekkir "
            f"{sorted(vaent)}. Dálkur myndi týnast eða bætast við óséður."
        )
    return [{"reitur": reitur, "kodi": kodi, "heiti": valin[kodi]} for kodi, reitur in STODUR]


def _rodun(vidd: dict[str, Any]) -> list[str]:
    """Völdu kóðarnir í röð svarsins (``category.index``) — Alls fyrst."""
    return [gildi["kodi"] for gildi in _valin(vidd)]


def _nidurstodur(samband: Connection, viddir: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Ein lína á hverja samsetningu námssviðs og kyns; hver reitur ein mæling."""
    hopar: dict[tuple[str, str], dict[str, Any]] = {}
    reitir = dict(STODUR)
    for rod in _keyra(samband, "hagstofan-hlutfoll"):
        lina = hopar.setdefault(
            (rod["field_code"], rod["sex_code"]),
            {"namssvid_kodi": rod["field_code"], "namssvid": rod["field_label"],
             "kyn_kodi": rod["sex_code"], "kyn": rod["sex_label"]},
        )
        reitur = reitir.get(rod["student_status_code"])
        if reitur is None or reitur in lina:
            raise UtflutningsVilla(
                f"Óvænt eða tvítekin mæling: {rod['field_code']}/{rod['sex_code']}/"
                f"{rod['student_status_code']}."
            )
        lina[reitur] = _runna(rod["percentage"])

    summur = {(rod["field_code"], rod["sex_code"]): rod["percentage_sum"]
              for rod in _keyra(samband, "hagstofan-summur")}
    rod_svida, rod_kynja = _rodun(viddir[VIDD_SVIDS]), _rodun(viddir[VIDD_KYNS])
    lyklar = [(svid, kyn) for svid in rod_svida for kyn in rod_kynja]
    if sorted(hopar) != sorted(lyklar) or sorted(summur) != sorted(lyklar):
        raise UtflutningsVilla(
            f"Niðurstöðulínurnar ({len(hopar)}) stemma ekki við víddirnar "
            f"({len(rod_svida)} svið × {len(rod_kynja)} kyn)."
        )
    gogn = []
    for lykill in lyklar:
        lina = hopar[lykill]
        vantar = [reitur for _, reitur in STODUR if reitur not in lina]
        if vantar:
            raise UtflutningsVilla(f"Línuna {lykill} vantar stöðuflokkana {vantar}.")
        gogn.append({**lina, "samtals": _runna(summur[lykill])})
    return gogn


def _heiti(vidd: dict[str, Any]) -> dict[str, str]:
    return {gildi["kodi"]: gildi["heiti"] for gildi in vidd["gildi"]}


def _munir(samband: Connection, viddir: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Mismunirnir þrír í prósentustigum: dregnir saman í SQL, námundaðir hér."""
    svid, kyn = _heiti(viddir[VIDD_SVIDS]), _heiti(viddir[VIDD_KYNS])
    brautskradir = STODUR[0][0]
    munir = []
    for lysing, svid_a, kyn_a, svid_b, kyn_b in SAMANBURDIR:
        radir: Sequence[Row] = _keyra(
            samband, "hagstofan-munur", brautskradir, svid_a, kyn_a, svid_b, kyn_b
        )
        rod = ein_rod(radir, f"Mismunurinn „{lysing}“")
        munir.append({"lysing": lysing,
                      "a": {"namssvid": svid[svid_a], "kyn": kyn[kyn_a]},
                      "b": {"namssvid": svid[svid_b], "kyn": kyn[kyn_b]},
                      "prosentustig": _runna(rod["difference_pp"])})
    return munir


def byggja(samband: Connection) -> dict[str, Any]:
    """Les grunninn og skilar sannreyndu umslagi fyrir ``hagstofan.json``."""
    gagnasafn = ein_rod(_keyra(samband, "hagstofan-gagnasafn"), "hagstofan-gagnasafn")
    viddalisti = _viddir(samband)
    viddir = {vidd["kodi"]: vidd for vidd in viddalisti}
    lysigogn = {
        "tafla": {
            "audkenni": gagnasafn["id"],
            "heiti": gagnasafn["label"],
            "uppruni": gagnasafn["source"],
            "endapunktur": gagnasafn["endpoint"],
            "hraskra": gagnasafn["raw_file"],
            "jsonstat_utgafa": gagnasafn["jsonstat_version"],
            "fjoldi_gilda": gagnasafn["value_count"],
            # Varðveitt svo síðan geti útskýrt þau, ekki notuð sem dagsetning/nákvæmni.
            "updated_i_svari": gagnasafn["updated"],
            "aukastafir_i_svari": gagnasafn["decimals"],
        },
        "afmorkun": _afmorkun(viddir),
        "stodur": _stodur(viddir),
        "aukastafir": AUKASTAFIR,
        "fyrirspurn": _fyrirspurnin(samband),
        "viddir": viddalisti,
        "munir": _munir(samband, viddir),
    }
    return byggja_umslag(
        uppfaert=gagnasafn["fetched_at"],
        heimild=_heimild(gagnasafn),
        gogn=_nidurstodur(samband, viddir),
        lysigogn=lysigogn,
    )
