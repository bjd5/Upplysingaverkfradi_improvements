"""Stillingar gagnasöfnunar — umhverfisbreytur og ``.env`` (regla 4).

Lyklar, tengiliðaupplýsingar og aðrar stillingar eru **aldrei í kóða**. Þær
koma úr umhverfinu eða úr ``.env`` í rót verkefnisins, sem er í ``.gitignore``;
``config/.env.example`` sýnir hvaða breytur þarf að setja.

Forgangsröðin er: raunveruleg umhverfisbreyta gengur fyrir gildi úr ``.env``.
Þannig getur CI-keyrsla sett gildi án þess að nokkur skrá sé til.

Gildin sjálf fara hvorki í logg, villuskilaboð né provenance. Villur nefna
**heiti breytunnar, aldrei gildið** — annars læki lykill út um villuboð.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

ROT = Path(__file__).resolve().parents[3]
ENV_SKRA = ROT / ".env"


class StillingaVilla(RuntimeError):
    """Stillingu vantar eða hún er ónothæf. Nefnir breytu, aldrei gildi."""


def _an_gaesalappa(texti: str) -> str:
    """Fjarlægir gæsalappir utan af gildi ef þær eru pöraðar."""
    if len(texti) >= 2 and texti[0] == texti[-1] and texti[0] in "\"'":
        return texti[1:-1]
    return texti


@lru_cache(maxsize=None)
def lesa_env_skra(slod: Path = ENV_SKRA) -> dict[str, str]:
    """Les ``.env`` og skilar korti af nafni í gildi; tómu korti sé skráin ekki til.

    Niðurstaðan er í skyndiminni. Í prófum (eða eftir að skránni er breytt)
    má hreinsa það með ``lesa_env_skra.cache_clear()``.
    """
    if not slod.is_file():
        return {}

    gildi: dict[str, str] = {}
    for numer, lina in enumerate(slod.read_text(encoding="utf-8").splitlines(), start=1):
        hreinsud = lina.strip()
        if not hreinsud or hreinsud.startswith("#"):
            continue
        if "=" not in hreinsud:
            # Línan er ekki endurtekin í villunni: hún gæti innihaldið lykil.
            raise StillingaVilla(
                f"Lína {numer} í {slod.name} er ekki á forminu NAFN=gildi."
            )
        nafn, _, texti = hreinsud.partition("=")
        gildi[nafn.strip()] = _an_gaesalappa(texti.strip())
    return gildi


def texti(nafn: str, sjalfgefid: str | None = None) -> str | None:
    """Skilar stillingu úr umhverfi, svo úr ``.env``, annars sjálfgefna gildinu."""
    ur_umhverfi = os.environ.get(nafn)
    if ur_umhverfi is not None and ur_umhverfi.strip():
        return ur_umhverfi.strip()
    ur_skra = lesa_env_skra().get(nafn)
    if ur_skra is not None and ur_skra.strip():
        return ur_skra.strip()
    return sjalfgefid


def krefjast(nafn: str, skyring: str) -> str:
    """Skilar stillingu sem verður að vera til, annars ``StillingaVilla``.

    ``skyring`` segir notandanum hvað breytan er fyrir. Hvorki hún né villan
    mega innihalda gildið sjálft (regla 4).
    """
    gildi = texti(nafn)
    if gildi is None:
        raise StillingaVilla(
            f"Umhverfisbreytuna {nafn} vantar — {skyring}. "
            f"Settu hana í umhverfið eða í .env (sjá config/.env.example)."
        )
    return gildi


def tala(nafn: str, sjalfgefid: float) -> float:
    """Skilar tölustillingu; fellur með skýrri villu sé gildið ekki tala."""
    gildi = texti(nafn)
    if gildi is None:
        return sjalfgefid
    try:
        return float(gildi)
    except ValueError as villa:
        # Gildið er ekki endurtekið hér: sama breyta gæti annars staðar
        # geymt lykil og villuboð eiga aldrei að bera gildi (regla 4).
        raise StillingaVilla(f"{nafn} á að vera tala í sekúndum.") from villa
