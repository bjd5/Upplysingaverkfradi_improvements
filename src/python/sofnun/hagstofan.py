"""Brautskráning af háskólastigi úr PxWeb-þjónustu Hagstofunnar (gagnasafn 2).

Flutt úr ``src/hagstofan.py`` upprunaverkefnisins. Söfnunin er tvö köll og það
seinna verður ekki til án þess fyrra:

1. ``GET`` sækir **lýsigögn** töflunnar — hvaða breytur hún hefur og hvaða
   gildi standa til boða.
2. ``POST`` sendir **fyrirspurn** sem er sett saman úr þeim lýsigögnum.

Þess vegna er fyrirspurnarsmíðin hér en ekki í vinnslulaginu: hún er hluti af
því að mynda beiðnina. Hún er líka staðurinn þar sem æfingin stöðvast ef taflan
breytist undir henni — kóði sem sendir fyrirspurn um breytu sem er horfin fengi
annars svar sem lítur rétt út en svarar annarri spurningu.

Fyrirspurnin sjálf er ekki vistuð sem sérstök skrá. Hún er föst afleiðing
lýsigagnanna, sem **eru** vistuð, og ``request_body_sha256`` í provenance
staðfestir að sú fyrirspurn sem var send sé einmitt sú sem ``byggja_fyrirspurn``
myndar úr þeim (regla 8).
"""

from __future__ import annotations

import json

from .beidni import Beidni
from .frosid import krefjast_thvingunar
from .hragogn import HRAGOGN, Svar
from .http import saekja

ENDAPUNKTUR = (
    "https://px.hagstofa.is/pxis/api/v1/is/Samfelag/skolamal/"
    "4_haskolastig/1_hsProf/SKO04208b.px"
)

# Afmörkun úrtaksins. Kóðarnir eru þjónustunnar eigin, ekki okkar nafngift, og
# breytuheitin eru íslensk af sömu ástæðu. Af hverju einmitt þessi ár og þessi
# námssvið er skráð í docs/adferdafraedi.md.
VAL = {
    "Innritunarár": ["2017"],
    "Tími": ["n+3"],
    "Nemendur": ["5", "6", "7"],
    "Fjöldi/Hlutfall": ["1"],
    "Námssvið": ["Alls", "05", "06", "07"],
    "Kyn": ["Alls", "1", "2"],
}

# Þessar tvær forsendur ráða túlkun allra talna sem byggðar eru á svarinu:
# tímapunkturinn og mælieiningin. Breytist önnur hvor merkir taflan annað en
# textinn á síðunni segir, og þá stöðvast söfnunin.
FORSENDUR = {
    ("Tími", "n+3"): "Sex árum eftir innritun",
    ("Fjöldi/Hlutfall", "1"): "Hlutfall %",
}

# Frosna eintakið úr upprunaverkefninu ber gamla skráarheitið.
FROSID_MYNSTUR = "response.json"
AF_HVERJU = "Taflan uppfærist og ný sókn gæfi aðrar tölur en síðan birtir."


class HagstofuVilla(RuntimeError):
    """Taflan svarar ekki þeim forsendum sem úrtakið byggir á."""


def merkingar(lysigogn: dict) -> dict[str, dict[str, str]]:
    """Parar ``values`` við ``valueTexts``; heiti eru ekki fyrirspurnarkóðar."""
    kort: dict[str, dict[str, str]] = {}
    for breyta in lysigogn.get("variables", []):
        kodar, textar = breyta["values"], breyta["valueTexts"]
        if len(kodar) != len(textar) or len(set(kodar)) != len(kodar):
            raise HagstofuVilla("Ósamræmi í values/valueTexts lýsigagnanna.")
        kort[breyta["code"]] = dict(zip(kodar, textar))
    if set(kort) != set(VAL):
        raise HagstofuVilla(
            "Breytur Hagstofutöflunnar hafa breyst; yfirfarið lýsigögnin "
            "áður en fyrirspurn er send."
        )
    return kort


def byggja_fyrirspurn(lysigogn: dict) -> dict:
    """Setur saman json-stat2 fyrirspurn úr lýsigögnum töflunnar."""
    kort = merkingar(lysigogn)
    for kodi, gildi in VAL.items():
        if not set(gildi) <= kort[kodi].keys():
            raise HagstofuVilla(f"Valdir kóðar fyrir {kodi} finnast ekki í lýsigögnum.")
    for (kodi, gildi), vaentur_texti in FORSENDUR.items():
        if kort[kodi][gildi] != vaentur_texti:
            raise HagstofuVilla(
                f"Merking {kodi}/{gildi} hefur breyst úr '{vaentur_texti}' í "
                f"'{kort[kodi][gildi]}'; yfirfarið textann á síðunni."
            )
    return {
        "query": [
            {"code": kodi, "selection": {"filter": "item", "values": gildi}}
            for kodi, gildi in VAL.items()
        ],
        "response": {"format": "json-stat2"},
    }


def fyrirspurnarstofn(fyrirspurn: dict) -> bytes:
    """Kóðar fyrirspurnina eins og hún fer í POST-líkamann."""
    return (json.dumps(fyrirspurn, ensure_ascii=False) + "\n").encode("utf-8")


LYSIGAGNA_BEIDNI = Beidni(
    thjonusta="hagstofan",
    veitandi="Hagstofa Íslands",
    slod=ENDAPUNKTUR,
    heiti="lysigogn",
    skjolun="https://px.hagstofa.is/pxis/api/v1/",
    hausar={"Accept": "application/json"},
)


def fyrirspurnar_beidni(fyrirspurn: dict) -> Beidni:
    """Beiðnin sem sækir sjálf gögnin — sama slóð, en POST með fyrirspurn."""
    return Beidni(
        thjonusta="hagstofan",
        veitandi="Hagstofa Íslands",
        slod=ENDAPUNKTUR,
        heiti="svar",
        adferd="POST",
        skjolun=LYSIGAGNA_BEIDNI.skjolun,
        hausar={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
        },
        gagnastofn=fyrirspurnarstofn(fyrirspurn),
    )


def saekja_hagstofuna(*, thvinga: bool = False, **rok) -> tuple[Svar, Svar]:
    """Sækir lýsigögn og gögn, í þeirri röð, og skilar báðum svörum.

    Fellur með ``FrosidVilla`` sé frosna eintakið til, nema ``thvinga=True``.
    Aukabreytur fara óbreyttar í ``sofnun.http.saekja``.
    """
    krefjast_thvingunar(
        LYSIGAGNA_BEIDNI.thjonusta,
        FROSID_MYNSTUR,
        thvinga=thvinga,
        af_hverju=AF_HVERJU,
        rot=rok.get("rot", HRAGOGN),
    )
    lysigogn_svar = saekja(LYSIGAGNA_BEIDNI, thvinga=thvinga, **rok)
    fyrirspurn = byggja_fyrirspurn(json.loads(lysigogn_svar.baeti))
    gagna_svar = saekja(fyrirspurnar_beidni(fyrirspurn), thvinga=thvinga, **rok)
    return lysigogn_svar, gagna_svar
