"""Útdráttur svaranna fimm úr vistuðu HTML-svari mbl.is (issue #9).

Hver spurning fær sitt fall. Öll lesa **vistaðan texta** og senda enga
vefbeiðni — eintakið í ``data/raw/mbl/`` er eina frumgagnið (regla 4).

Sameiginlega reglan: finnist mynstur ekki, eða gefi það ósamræmda niðurstöðu,
er kastað :class:`UtdrattarVilla` með lýsandi skilaboðum. Fall skilar aldrei
þöglu núlli eða tómum lista (regla 6) — breyting á HTML-sniði mbl.is á að
stöðva keyrsluna, ekki framleiða trúverðuga en ranga tölu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .mbl_mynstur import (
    MYNSTUR_AUGLYSINGAREITUR,
    MYNSTUR_FRETTASLOD,
    MYNSTUR_HITI_REYKJAVIK,
    MYNSTUR_ORD,
    MYNSTUR_OSYNILEGT,
    MYNSTUR_SCRIPT_BLOKK,
    MYNSTUR_USD_GENGI,
    SPURNING_EFTIR_LYKLI,
    Spurning,
    UtdrattarVilla,
    flaggaheiti,
)
from .mbl_ord import synileg_ord

# Sýnishornið er sönnunargagn, ekki afrit af efninu: nóg til að sjá hvað
# mynstrið hitti á, of lítið til að endurbirta frétt (höfundaréttur).
SYNISHORN_HAMARK = 160
SYNISHORN_ORDAFJOLDI = 10
BIL = re.compile(r"\s+")


@dataclass(frozen=True)
class Utdrattur:
    """Eitt svar ásamt mynstrinu sem framkallaði það.

    Mynstrið fylgir svarinu alla leið í grunninn því talan er annars
    órekjanleg (regla 8).
    """

    spurning: Spurning
    mynsturheiti: str
    mynstur: str
    mynsturflogg: str
    afmorkun_heiti: str | None
    afmorkun_mynstur: str | None
    gildi: float
    gildistexti: str
    tilvik: int
    einstok: int
    synishorn: str


def synishorn(texti: str) -> str:
    """Styttir texta í eina línu með úrfellingu í miðju."""
    ein_lina = BIL.sub(" ", texti).strip()
    if len(ein_lina) <= SYNISHORN_HAMARK:
        return ein_lina
    helmingur = (SYNISHORN_HAMARK - 1) // 2
    return f"{ein_lina[:helmingur]}…{ein_lina[-helmingur:]}"


def islensk_heiltala(tala: int) -> str:
    """Heiltala með punkti sem þúsundaskilum, eins og hún birtist á íslensku."""
    return f"{tala:,}".replace(",", ".")


def islensk_kommutala(tala: float) -> str:
    """Kommutala með íslensku kommusniði; heil tala fær enga aukastafi."""
    if tala == int(tala):
        return islensk_heiltala(int(tala))
    return f"{tala}".replace(".", ",")


def draga_ut_einstakar_frettir(html_texti: str) -> Utdrattur:
    """1. Hversu margar einstakar fréttir eru á síðunni?"""
    tilvik = MYNSTUR_FRETTASLOD.findall(html_texti)
    if not tilvik:
        raise UtdrattarVilla(
            "Engin fréttaslóð fannst í HTML-textanum. Mynstrið "
            "MYNSTUR_FRETTASLOD bíður eftir /frettir/<flokkur>/ÁÁÁÁ/MM/DD/<nafn>/."
        )
    # Sama grein getur tengst bæði úr mynd og fyrirsögn; birtingarröð er varðveitt.
    einstakar = list(dict.fromkeys(tilvik))
    return Utdrattur(
        spurning=SPURNING_EFTIR_LYKLI["einstakar-frettir"],
        mynsturheiti="MYNSTUR_FRETTASLOD",
        mynstur=MYNSTUR_FRETTASLOD.pattern,
        mynsturflogg=flaggaheiti(MYNSTUR_FRETTASLOD),
        afmorkun_heiti=None,
        afmorkun_mynstur=None,
        gildi=float(len(einstakar)),
        gildistexti=f"{islensk_heiltala(len(einstakar))} einstakar fréttir",
        tilvik=len(tilvik),
        einstok=len(einstakar),
        synishorn=synishorn(einstakar[0]),
    )


def draga_ut_hitastig(html_texti: str) -> Utdrattur:
    """2. Hvert er hitastigið í Reykjavík?"""
    samsvaranir = list(MYNSTUR_HITI_REYKJAVIK.finditer(html_texti))
    if not samsvaranir:
        raise UtdrattarVilla(
            "Hitastig Reykjavíkur fannst ekki í HTML-textanum. Mynstrið "
            "MYNSTUR_HITI_REYKJAVIK bíður eftir valinni Reykjavík og "
            "value/unit-reitum veðurkassans."
        )

    gildi = {m.group("temperature").replace(",", ".") for m in samsvaranir}
    if len(gildi) > 1:
        raise UtdrattarVilla(
            "Fleiri en eitt hitastig fannst fyrir Reykjavík: "
            f"{', '.join(sorted(gildi))}. Útdrátturinn velur ekki milli þeirra."
        )

    hiti = float(gildi.pop())
    return Utdrattur(
        spurning=SPURNING_EFTIR_LYKLI["hitastig-reykjavik"],
        mynsturheiti="MYNSTUR_HITI_REYKJAVIK",
        mynstur=MYNSTUR_HITI_REYKJAVIK.pattern,
        mynsturflogg=flaggaheiti(MYNSTUR_HITI_REYKJAVIK),
        afmorkun_heiti=None,
        afmorkun_mynstur=None,
        gildi=hiti,
        gildistexti=f"{islensk_kommutala(hiti)} °C",
        tilvik=len(samsvaranir),
        einstok=1,
        synishorn=synishorn(samsvaranir[0].group(0)),
    )


def draga_ut_gengi_usd(html_texti: str) -> Utdrattur:
    """3. Hvert er gengi Bandaríkjadals?"""
    samsvaranir = [
        m
        for blokk in MYNSTUR_SCRIPT_BLOKK.finditer(html_texti)
        for m in MYNSTUR_USD_GENGI.finditer(blokk.group("body"))
    ]
    if not samsvaranir:
        raise UtdrattarVilla(
            "Gengi Bandaríkjadals fannst ekki í script-blokkum HTML-textans. "
            "Mynstrið MYNSTUR_USD_GENGI bíður eftir "
            'arrCurrency[n]=new MakeItem("USD", "<gengi>").'
        )

    gildi = {m.group("rate") for m in samsvaranir}
    if len(gildi) > 1:
        raise UtdrattarVilla(
            f"Ósamræmd USD-gengi í sama svari: {', '.join(sorted(gildi))}. "
            "Útdrátturinn velur ekki milli þeirra."
        )

    gengi = float(gildi.pop())
    if gengi <= 0:
        raise UtdrattarVilla(f"USD-gengi verður að vera jákvætt, fannst {gengi}.")

    return Utdrattur(
        spurning=SPURNING_EFTIR_LYKLI["gengi-usd"],
        mynsturheiti="MYNSTUR_USD_GENGI",
        mynstur=MYNSTUR_USD_GENGI.pattern,
        mynsturflogg=flaggaheiti(MYNSTUR_USD_GENGI),
        afmorkun_heiti="MYNSTUR_SCRIPT_BLOKK",
        afmorkun_mynstur=MYNSTUR_SCRIPT_BLOKK.pattern,
        gildi=gengi,
        gildistexti=f"{islensk_kommutala(gengi)} ISK fyrir 1 USD",
        tilvik=len(samsvaranir),
        einstok=1,
        synishorn=synishorn(samsvaranir[0].group(0)),
    )


def draga_ut_synileg_ord(html_texti: str) -> Utdrattur:
    """4. Hversu mörg sýnileg orð eru á síðunni?"""
    ord_listi = synileg_ord(html_texti)
    if not ord_listi:
        raise UtdrattarVilla(
            "Ekkert sýnilegt orð fannst í HTML-textanum. Annaðhvort er svarið "
            "tómt eða hreinsunin fjarlægði allan texta — hvorugt er eðlilegt "
            "fyrir fréttasíðu."
        )

    return Utdrattur(
        spurning=SPURNING_EFTIR_LYKLI["synileg-ord"],
        mynsturheiti="MYNSTUR_ORD",
        mynstur=MYNSTUR_ORD.pattern,
        mynsturflogg=flaggaheiti(MYNSTUR_ORD),
        afmorkun_heiti="MYNSTUR_OSYNILEGT",
        afmorkun_mynstur="\n".join(m.pattern for m in MYNSTUR_OSYNILEGT),
        gildi=float(len(ord_listi)),
        gildistexti=f"{islensk_heiltala(len(ord_listi))} sýnileg orð",
        tilvik=len(ord_listi),
        einstok=len(set(ord_listi)),
        synishorn=synishorn(" ".join(ord_listi[:SYNISHORN_ORDAFJOLDI])),
    )


def draga_ut_auglysingareiti(html_texti: str) -> Utdrattur:
    """5. Hversu margir auglýsingareitir eru skilgreindir?"""
    tilvik = [m.group("slot") for m in MYNSTUR_AUGLYSINGAREITUR.finditer(html_texti)]
    if not tilvik:
        raise UtdrattarVilla(
            "Enginn auglýsingareitur fannst í HTML-textanum. Mynstrið "
            "MYNSTUR_AUGLYSINGAREITUR bíður eftir Ads.renderSlot('<auðkenni>',."
        )

    einstok = list(dict.fromkeys(tilvik))
    return Utdrattur(
        spurning=SPURNING_EFTIR_LYKLI["auglysingareitir"],
        mynsturheiti="MYNSTUR_AUGLYSINGAREITUR",
        mynstur=MYNSTUR_AUGLYSINGAREITUR.pattern,
        mynsturflogg=flaggaheiti(MYNSTUR_AUGLYSINGAREITUR),
        afmorkun_heiti=None,
        afmorkun_mynstur=None,
        gildi=float(len(einstok)),
        gildistexti=f"{islensk_heiltala(len(einstok))} auglýsingareitir",
        tilvik=len(tilvik),
        einstok=len(einstok),
        synishorn=synishorn(f"Ads.renderSlot('{einstok[0]}',"),
    )


UTDRAETTIR = (
    draga_ut_einstakar_frettir,
    draga_ut_hitastig,
    draga_ut_gengi_usd,
    draga_ut_synileg_ord,
    draga_ut_auglysingareiti,
)


def draga_ut_allt(html_texti: str) -> list[Utdrattur]:
    """Svarar öllum spurningunum fimm í röð.

    Falli ein spurning fellur keyrslan öll: hálft svar er ekki niðurstaða.
    """
    return [utdrattur(html_texti) for utdrattur in UTDRAETTIR]
