"""Samanburður Phoebe-úttaksins við frosna viðmiðið (issue #14, pakki P2.5).

Viðmiðið er ``data/processed/phoebe-stats/`` — 17 skrár sem gamla skriftan
skrifaði og síðan birti, tryggðar með SHA-256 í ``docs/vidmid/provenance.json``. Það er **lesið**, aldrei afritað inn í prófin, svo
ekki sé hægt að laga próf að greiningu í stað þess að laga greiningu að
viðmiði.

Samanburðurinn er **bæti fyrir bæti**. Einu frávikin sem eru leyfð eru þau
sem ``vinnsla.phoebe_samningur`` lýsir, og þau eru nefnd hér eitt af öðru:
vegguklukkustimplar felldir brott, ``generator``/``note`` vísa á nýju
eininguna og ``source_commit`` bætist aftast í ``_meta.json``. Allt annað —
hver tala, hver lykill, röð lykla, línuskil — verður að stemma.

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py`` og hleður henni aðeins þegar prófin flytja hana inn.
"""

from __future__ import annotations

import json
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path
from hjalp import ROT

from vinnsla.friends_handrit import SOURCE_COMMIT  # noqa: E402
from vinnsla.phoebe_samningur import GENERATOR, SUMMARY_NOTE  # noqa: E402

VIDMIDSMAPPA = ROT / "data" / "processed" / "phoebe-stats"
VIDMIDSMETA = VIDMIDSMAPPA / "_meta.json"

# skrá -> (stimpill sem er felldur brott, {lykill: nýtt gildi}, {aftast bætt við})
LEYFD_FRAVIK = {
    "_meta.json": ("generated_utc", {"generator": GENERATOR},
                   {"source_commit": SOURCE_COMMIT}),
    "summary.json": ("generated_at", {"note": SUMMARY_NOTE}, {}),
}


def vidmidsskrar() -> list[str]:
    """Heiti skránna sem viðmiðið geymir og úttakið verður að skrifa."""
    heiti = sorted(p.name for p in VIDMIDSMAPPA.iterdir())
    if not heiti:
        raise AssertionError(f"Viðmiðið í {VIDMIDSMAPPA} er tómt — samanburður sannar ekkert.")
    return heiti


def vidmidsmeta() -> dict:
    """Staðfestu tölurnar í ``_meta.json`` viðmiðsins."""
    return json.loads(VIDMIDSMETA.read_text(encoding="utf-8"))


def vaent_baeti(heiti: str) -> bytes:
    """Bætin sem úttaksskráin á að hafa: viðmiðið með leyfðu frávikunum einum."""
    frumrit = (VIDMIDSMAPPA / heiti).read_bytes()
    if heiti not in LEYFD_FRAVIK:
        return frumrit
    stimpill, skipt, baett = LEYFD_FRAVIK[heiti]
    gamalt = json.loads(frumrit)
    if stimpill not in gamalt:
        raise AssertionError(f"{heiti}: viðmiðið hefur ekki {stimpill} — fráviksskráin er úrelt.")
    nytt = {}
    for lykill, gildi in gamalt.items():
        if lykill == stimpill:
            continue
        nytt[lykill] = skipt.get(lykill, gildi)
    nytt.update(baett)
    return (json.dumps(nytt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def munur_vid_vidmid(mappa: Path) -> list[str]:
    """Skrár sem víkja frá viðmiðinu (eða vantar/eru umfram). Tómur listi = eins."""
    vaentar = vidmidsskrar()
    munur = []
    for heiti in vaentar:
        slod = mappa / heiti
        if not slod.is_file():
            munur.append(f"{heiti}: vantar")
        elif slod.read_bytes() != vaent_baeti(heiti):
            munur.append(f"{heiti}: önnur bæti")
    for aukaleg in sorted({p.name for p in mappa.iterdir()} - set(vaentar)):
        munur.append(f"{aukaleg}: umfram viðmiðið")
    return munur


def skrifa_vaent(mappa: Path) -> Path:
    """Skrifar væntu bætin í ``mappa`` — til að prófa samanburðinn sjálfan."""
    mappa.mkdir(parents=True, exist_ok=True)
    for heiti in vidmidsskrar():
        (mappa / heiti).write_bytes(vaent_baeti(heiti))
    return mappa
