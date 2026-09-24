"""Ber frosna stöðvalistann saman við frosna viðmiðið úr gömlu síðunni.

Veðurstöðvarnar eru eina safnið þar sem ekkert eldra eintak var til: gamla
verkefnið sótti listann upp á nýtt í hverri byggingu og vistaði svarið aldrei
(sjá ``docs/vidmid/README.md``). Nýja eintakið í ``data/raw/vedurstodvar/`` er
því ný söfnun og **munur við gömlu síðuna er vænt niðurstaða, ekki villa.**

Verkefnið krefst samt að munurinn sé skráður og ekki ágiskaður. Þessi eining
reiknar sömu tölur og gamla skriftan reiknaði — sömu síur, sömu hnit, sama
fjarlægðarreikning — og ber þær við tölurnar sem frosna viðmiðið birtir.
Niðurstaðan fer í ``docs/vedurstodvar-samanburdur.md``.

Viðmiðstölurnar eru LESNAR úr ``docs/vidmid/generated/vedurstofa-siur.md``, ekki
slegnar inn hér; töflur sem eru slegnar inn tvisvar fara á skjön.

Keyrsla frá rót verkefnisins::

    python3 src/python/vinnsla/vedurstodvar_samanburdur.py

Netlaust — les aðeins frosin gögn. Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:  # keyrt beint: python3 src/python/vinnsla/vedurstodvar_samanburdur.py
    from vedurstodvar_skjal import skrifa_skjal
except ImportError:  # flutt inn sem eining innan pakkans
    from .vedurstodvar_skjal import skrifa_skjal

ROT = Path(__file__).resolve().parents[3]
FROSID = ROT / "data" / "raw" / "vedurstodvar"
VIDMID_SIUR = ROT / "docs" / "vidmid" / "generated" / "vedurstofa-siur.md"
UTTAK = ROT / "docs" / "vedurstodvar-samanburdur.md"

# Forsendur gömlu skriftunnar (src/vedurstofa_stodvar.py í upprunarepo-inu).
# Þær eru endurnotaðar óbreyttar: samanburður sem notar aðrar forsendur mælir
# forsendumuninn og ekki gagnamuninn.
VR_II_BREIDD = 64.1386922
VR_II_LENGD = -21.9556406
VR_II_HEIMILD = "Nominatim (OpenStreetMap), flett upp 2026-09-03 í upprunaverkefninu"
RADIUS_KM = 5.0
JORD_RADIUS_KM = 6371.0088
VALIN_STOD = 1469  # stöðin sem gamla síðan valdi fyrir VR-II
AR_AFTUR_I_TIMANN = 50
VIDMIDSAR = 2026  # árið sem gamla síðan var byggð; 50 ár aftur = 1976

# Staðreyndir sem viðmiðið fullyrðir í vedurstofa-nidurstada.md og
# vedurstofa-svor.md. Þær eru ekki í töflu og því ekki þáttanlegar; þær eru
# skráðar hér með tilvísun og bornar við útreikninginn.
VIDMID_SVOR = {
    "naesta": (1469, "Reykjavík Hljómskálagarður", 639),
    "naesta_aflogd": (2, "Sjómannaskóli", 689),
    "langtimastod": (1, "Reykjavík", 2547),
}
VIDMID_1469_START = 2022


class SamanburdarVilla(RuntimeError):
    """Skýr villa þegar samanburðinn er ekki hægt að framkvæma."""


def stutt_slod(slod: Path) -> str:
    """Slóð afstæð við rót verkefnisins þegar hún liggur þar, annars full slóð.

    Villuboð á að vera hægt að birta hvar sem skráin liggur, líka í prófum.
    """
    return slod.relative_to(ROT).as_posix() if slod.is_relative_to(ROT) else str(slod)


def lesa_frosid() -> tuple[str, str, list[dict]]:
    """Les nýjasta frosna stöðvasvarið og skilar (skráarheiti, söfnunartími, stöðvar).

    Söfnunartíminn kemur úr provenance safnsins og ekki úr klukkunni: skjalið sem
    byggt er á þessu á að vera hrein afleiða af frosnu gögnunum og verða eins í
    hverri keyrslu, hvenær sem hún er gerð.
    """
    eintok = sorted(FROSID.glob("stations-*.json"))
    if not eintok:
        raise SamanburdarVilla(
            f"Ekkert frosið eintak í {stutt_slod(FROSID)} — keyrðu "
            "src/python/sofnun/frysta_vedurstodvar.py fyrst."
        )
    skra = eintok[-1]
    provenance = FROSID / "provenance.json"
    if not provenance.is_file():
        raise SamanburdarVilla(
            f"Eintak án provenance í {stutt_slod(FROSID)} — hrágagn án uppruna er "
            "ónothæft (regla 4)."
        )
    sott = json.loads(provenance.read_text(encoding="utf-8"))["fetched_at_utc"]
    return skra.name, sott, json.loads(skra.read_text(encoding="utf-8"))


def haversine_km(breidd1: float, lengd1: float, breidd2: float, lengd2: float) -> float:
    """Fjarlægð milli tveggja hnita í km eftir stórbaug (sama formúla og gamla skriftan)."""
    f1, f2 = math.radians(breidd1), math.radians(breidd2)
    d_f = f2 - f1
    d_l = math.radians(lengd2 - lengd1)
    a = math.sin(d_f / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(d_l / 2) ** 2
    return 2 * JORD_RADIUS_KM * math.asin(math.sqrt(a))


def er_virk(stod: dict) -> bool:
    """Stöð telst virk ef ``ending`` er tómt, þ.e. hún hefur ekki hætt mælingum."""
    return stod.get("ending") is None


def kassi(breidd: float, lengd: float, radius_km: float) -> tuple[float, float, float, float]:
    """Mörk ferhyrnda ``polygon``-kassans sem gamla skriftan sendi þjónustunni.

    Breiddargráða er ~111 km alls staðar en lengdargráða styttist í
    111·cos(breidd). Hnitin eru rúnnuð á fjóra aukastafi eins og WKT-strengurinn
    sem var sendur, svo kassinn sé sá sami og þjónustan sá.
    """
    d_breidd = radius_km / 111.0
    d_lengd = radius_km / (111.0 * math.cos(math.radians(breidd)))
    return (
        round(lengd - d_lengd, 4),
        round(breidd - d_breidd, 4),
        round(lengd + d_lengd, 4),
        round(breidd + d_breidd, 4),
    )


def i_kassa(stod: dict, mork: tuple[float, float, float, float]) -> bool:
    """Er stöðin innan kassans? Sama skilyrði og ``sia_stadbundid`` gamla verkefnisins."""
    min_lengd, min_breidd, max_lengd, max_breidd = mork
    return min_lengd <= stod["lon"] <= max_lengd and min_breidd <= stod["lat"] <= max_breidd


def telja_siur(stodvar: list[dict]) -> dict[str, int]:
    """Reiknar fjöldann sem hver af fimm beiðnum gömlu síðunnar skilaði.

    Ósíaða svarið er yfirmengi hinna fjögurra, svo síurnar eru reiknaðar hér í
    stað þess að senda fjórar beiðnir til viðbótar.
    """
    mork = kassi(VR_II_BREIDD, VR_II_LENGD, RADIUS_KM)
    i_kassanum = [stod for stod in stodvar if i_kassa(stod, mork)]
    return {
        "engin sía": len(stodvar),
        "`active=true`": sum(1 for stod in stodvar if er_virk(stod)),
        "`polygon`": len(i_kassanum),
        "`polygon` + `active=true`": sum(1 for stod in i_kassanum if er_virk(stod)),
        f"`station_id={VALIN_STOD}`": sum(1 for stod in stodvar if stod.get("station") == VALIN_STOD),
    }


def lesa_vidmid_siur() -> dict[str, int]:
    """Þáttar fjöldatöfluna úr ``docs/vidmid/generated/vedurstofa-siur.md``.

    Taflan er heimildin um hvað gamla síðan birti. Bregðist þáttunin er það
    villa og ekki tilefni til að nota innslegnar tölur í staðinn (regla 6).
    """
    if not VIDMID_SIUR.is_file():
        raise SamanburdarVilla(f"Vantar viðmiðið {stutt_slod(VIDMID_SIUR)} (P0.1)")

    tolur: dict[str, int] = {}
    for lina in VIDMID_SIUR.read_text(encoding="utf-8").splitlines():
        if not lina.startswith("|"):
            continue
        hlutar = [hluti.strip() for hluti in lina.strip().strip("|").split("|")]
        if len(hlutar) < 2 or not hlutar[-1].isdigit():
            continue  # fyrirsögn eða skilalína
        tolur[hlutar[0]] = int(hlutar[-1])
    if not tolur:
        raise SamanburdarVilla(f"Fann enga fjöldatölu í {stutt_slod(VIDMID_SIUR)}")
    return tolur


def svor_nuna(stodvar: list[dict]) -> dict[str, tuple[int, str, int]]:
    """Reiknar sömu þrjú stöðvaval og viðmiðið fullyrðir, með fjarlægð í metrum."""
    med_fjarlaegd = sorted(
        (dict(stod, metrar=round(haversine_km(VR_II_BREIDD, VR_II_LENGD, stod["lat"], stod["lon"]) * 1000))
         for stod in stodvar if stod.get("lat") is not None and stod.get("lon") is not None),
        key=lambda stod: stod["metrar"],
    )
    ar = VIDMIDSAR - AR_AFTUR_I_TIMANN

    def fyrsta(skilyrdi) -> tuple[int, str, int]:
        stod = next((stod for stod in med_fjarlaegd if skilyrdi(stod)), None)
        if stod is None:
            raise SamanburdarVilla("Engin stöð stenst skilyrðið — svarið er ósambærilegt")
        return stod["station"], stod["name"] or "(ónefnd stöð)", stod["metrar"]

    return {
        "naesta": fyrsta(er_virk),
        "naesta_aflogd": fyrsta(lambda stod: not er_virk(stod)),
        "langtimastod": fyrsta(lambda stod: er_virk(stod) and stod.get("start", ar + 1) <= ar),
    }


def byggja_samanburd() -> dict:
    """Setur saman allan samanburðinn: síutölur, stöðvaval og lýsigögn."""
    skraarheiti, sott_utc, stodvar = lesa_frosid()
    vidmid, nuna = lesa_vidmid_siur(), telja_siur(stodvar)

    vantar = sorted(set(nuna) - set(vidmid))
    if vantar:
        raise SamanburdarVilla(
            "Viðmiðstaflan nefnir ekki þessar síur: " + ", ".join(vantar) +
            " — samanburðurinn væri þá ekki samanburður."
        )

    valin = next((stod for stod in stodvar if stod.get("station") == VALIN_STOD), None)
    return {
        "eintak": skraarheiti,
        "sott_utc": sott_utc,
        "vr_ii": {
            "breidd": VR_II_BREIDD,
            "lengd": VR_II_LENGD,
            "heimild": VR_II_HEIMILD,
        },
        "siur": [
            {"sia": sia, "vidmid": vidmid[sia], "nuna": fjoldi, "munur": fjoldi - vidmid[sia]}
            for sia, fjoldi in nuna.items()
        ],
        "svor": {
            heiti: {"vidmid": VIDMID_SVOR[heiti], "nuna": gildi}
            for heiti, gildi in svor_nuna(stodvar).items()
        },
        "valin_stod": valin,
        "fjoldi_aflagdra": sum(1 for stod in stodvar if not er_virk(stod)),
    }


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument("--prenta", action="store_true", help="prenta JSON í stað þess að skrifa skjalið")
    stillingar = thattari.parse_args(rok)

    samanburdur = byggja_samanburd()
    if stillingar.prenta:
        print(json.dumps(samanburdur, ensure_ascii=False, indent=2))
        return 0

    skrifa_skjal(samanburdur, UTTAK)
    print(f"Skrifaði {stutt_slod(UTTAK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
