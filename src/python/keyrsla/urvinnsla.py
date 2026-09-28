"""Vinnslurnar sem skrifa í ``data/processed/`` — ``--skref vinna`` (issue #39).

Fjórar vinnslur úr #14, í tveimur flokkum:

* **Netlausar, alltaf keyrðar:** skjálftarnir (P2.3) og veðurstöðvarnar
  (P2.4). Þær lesa aðeins frosnu hrágögnin í ``data/raw/``.
* **Handritavinnslur, aðeins keyrðar sé beðið um þær:** Phoebe (P2.5) og
  Central Perk (P2.6). Aðfang þeirra, Friends-handritin, er utan repo-sins og
  á að vera það (issue #3, valkostur A). Beiðnin er umhverfisbreytan
  ``FRIENDS_HANDRIT_MAPPA`` — sú sama og einingarnar sjálfar lesa.

**Vanti handritin er það sagt, ekki þagað** (regla 6): skrefið klárar netlausu
vinnslurnar og skráir viðvörun sem nefnir báðar handritavinnslurnar, af hverju
þær voru ekki keyrðar og hvernig á að keyra þær. Það er ekki villa, því ekkert
síðar í flæðinu bíður þeirra: Friends-hleðslan les frosnu tölurnar í
``data/processed/phoebe-stats/``. Sé breytan hins vegar stillt og mappan finnst
ekki, er það villa — þá var beðið um eitthvað sem ekki var hægt að gera.

**Frosnu Friends-tölurnar eru aldrei yfirskrifaðar.** ``phoebe_uttak`` skrifar
sjálfgefið í ``data/processed/phoebe-stats/``, en sú mappa er frumgagn í git
(data/processed/README.md, kafli 1.5) og SHA-256 hennar er staðfest við
hleðslu. Endurreiknaða úttakið fer því í ``phoebe-stats-endurreiknad/`` (utan
git), og því er neitað að skrifa ofan í frosnu möppuna.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

from gagnagrunnur.tenging import ROT
from vinnsla import central_perk_uttak, jardskjalftar_uttak, phoebe_uttak
from vinnsla import vedurstodvar_uttak
from vinnsla.friends_handrit import TRANSCRIPT_DIR_ENV, TranscriptError, transcript_dir
from vinnsla.friends_skrar import STATS_MAPPA

from .villa import SkrefVilla

log = logging.getLogger(__name__)

UNNID = ROT / "data" / "processed"
PHOEBE_ENDURREIKNAD = "phoebe-stats-endurreiknad"

# Villur sem vinnslueiningarnar kasta þegar aðfangið stenst ekki (sjá hleðsluna).
VINNSLUVILLUR = (RuntimeError, ValueError, OSError, TranscriptError)


def _skjalftar(unnid: Path, _handrit: Path | None) -> str:
    uttak = jardskjalftar_uttak.vinna_skjalfta(mappa=unnid / jardskjalftar_uttak.UNNID.name)
    return f"{uttak.atburdir} atburðir, {uttak.dagar} dagar"


def _stodvar(unnid: Path, _handrit: Path | None) -> str:
    slod, mat = vedurstodvar_uttak.vinna_vedurstodvar(
        mappa=unnid / vedurstodvar_uttak.UNNID.name
    )
    return f"{mat.fjoldi_allra} stöðvar metnar -> {slod.name}"


def phoebe_mappa(unnid: Path) -> Path:
    """Hvert endurreiknaða Phoebe-úttakið fer — aldrei í frosnu möppuna."""
    mappa = unnid / PHOEBE_ENDURREIKNAD
    if mappa.resolve() == STATS_MAPPA.resolve():
        raise SkrefVilla(
            f"Phoebe-vinnslan skrifar ekki í {STATS_MAPPA}: þar eru frosnu tölurnar "
            "sem Friends-hleðslan staðfestir (data/processed/README.md, kafli 1.5)."
        )
    return mappa


def _phoebe(unnid: Path, handrit: Path | None) -> str:
    skrifadar = phoebe_uttak.run(handrit, phoebe_mappa(unnid))
    return f"{len(skrifadar)} skrár í {PHOEBE_ENDURREIKNAD}/"


def _central_perk(unnid: Path, handrit: Path | None) -> str:
    mappa = unnid / central_perk_uttak.OUTPUT_DIR.name
    return f"{len(central_perk_uttak.run(handrit, mappa))} skrár í {mappa.name}/"


Vinnsla = tuple[str, Callable[[Path, Path | None], str]]

NETLAUSAR: tuple[Vinnsla, ...] = (
    ("jardskjalftar_uttak (P2.3)", _skjalftar),
    ("vedurstodvar_uttak (P2.4)", _stodvar),
)
HANDRITAVINNSLUR: tuple[Vinnsla, ...] = (
    ("phoebe_uttak (P2.5)", _phoebe),
    ("central_perk_uttak (P2.6)", _central_perk),
)


def handritamappa() -> Path | None:
    """Mappan úr ``FRIENDS_HANDRIT_MAPPA``, eða ``None`` sé ekki beðið um handritin."""
    gildi = os.environ.get(TRANSCRIPT_DIR_ENV, "").strip()
    return Path(gildi) if gildi else None


def _keyra(vinnslur: tuple[Vinnsla, ...], unnid: Path, handrit: Path | None) -> list[str]:
    yfirlit = []
    for heiti, vinnsla in vinnslur:
        try:
            lysing = vinnsla(unnid, handrit)
        except VINNSLUVILLUR as villa:
            raise SkrefVilla(f"Vinnslan {heiti} mistókst: {villa}") from villa
        log.info("Vann %s: %s.", heiti, lysing)
        yfirlit.append(f"{heiti}: {lysing}")
    return yfirlit


def vinna_allt(unnid: Path = UNNID, handrit: Path | None = None) -> list[str]:
    """Keyrir netlausu vinnslurnar og, sé ``handrit`` gefin, handritavinnslurnar.

    Skilar einni línu á hverja vinnslu sem var keyrð. Þær sem voru ekki keyrðar
    eru nefndar í viðvörun, aldrei þagðar. Sé beðið um handritin en mappan
    finnst ekki er stöðvað strax, áður en nokkuð er skrifað.
    """
    if handrit is not None:
        try:
            transcript_dir(handrit)
        except TranscriptError as villa:
            raise SkrefVilla(f"{TRANSCRIPT_DIR_ENV} er stillt en: {villa}") from villa
    yfirlit = _keyra(NETLAUSAR, unnid, None)
    if handrit is None:
        log.warning(
            "Ekki keyrt: %s. Friends-handritin eru utan repo-sins (issue #3, "
            "valkostur A) og %s er ekki stillt. Til að keyra þær: "
            "%s=/slóð/á/season python3 src/python/main.py --skref vinna. "
            "Hleðslan þarf þær ekki — hún les frosnu tölurnar í %s.",
            " og ".join(heiti for heiti, _ in HANDRITAVINNSLUR),
            TRANSCRIPT_DIR_ENV,
            TRANSCRIPT_DIR_ENV,
            STATS_MAPPA.relative_to(ROT).as_posix(),
        )
        return yfirlit
    return yfirlit + _keyra(HANDRITAVINNSLUR, unnid, handrit)
