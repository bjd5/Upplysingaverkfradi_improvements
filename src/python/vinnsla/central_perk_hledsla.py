"""Hleðsla Central Perk-niðurstaðnanna í grunninn (issue #10, fyrir #24).

Aðfangið er frosið (``vinnsla.central_perk_adfang``): samantektin, myndin og
segðirnar sem gamla greiningin skrifaði. Handritin eru hvorki lesin né geymd
(issue #3, valkostur A).

Skref hleðslunnar, og hvert þeirra stöðvar keyrsluna við frávik (regla 6):

1. SHA-256 skránna þriggja borin við ``docs/vidmid/provenance.json``.
2. Hver reitur sannreyndur — gerð, mörk, einkvæmni.
3. Samræmi milli skráa: punktar á hóp = ``n``, sönghandritin þau sömu,
   miðgildi punktanna innan námundunar frá miðgildi samantektarinnar,
   miðgildislínur myndarinnar við miðgildin, munurinn = 100·(söngur − CP),
   segðirnar þær sömu og ``central_perk_mynstur`` keyrir.
4. Allt sett inn í einni færslu og grunnurinn spurður á eftir með sömu
   fyrirspurnum og síðan birtir (``src/sql/queries/central-perk-*.sql``).

Endurkeyranleg: töflurnar eru hreinsaðar og allt sett inn á ný með
náttúrulegum lyklum. Eini keyrslustimpillinn er ``central_perk_sources.loaded_at``.

Keyrsla frá rót verkefnisins::

    PYTHONPATH=src/python python3 -m vinnsla.central_perk_hledsla

Netlaust. Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import logging
import sqlite3
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path
from sqlite3 import Connection

from gagnagrunnur import fyrirspurnir
from gagnagrunnur.keyrari import keyra
from gagnagrunnur.tenging import tenging

from . import central_perk_adfang as adfang
from .central_perk_mynstur import CENTRAL_PERK_GROUP, DOCUMENTED_PATTERNS, GROUP_ORDER, PHOEBE_SINGS
from .friends_handrit import SOURCE_COMMIT, SOURCE_REPOSITORY

log = logging.getLogger(__name__)

TRANSCRIPT_REPOSITORY = SOURCE_REPOSITORY.removeprefix("https://github.com/")
ANALYSIS_REPOSITORY = "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe"
ANALYSIS_COMMIT = "2865ed6"
ANALYSIS_SCRIPT = "src/phoebe_central_perk.py"
LEYFI = (
    "Handritin: afrit aðdáenda á höfundarréttarvörðu efni, ekkert leyfi á "
    "textanum; MIT delvinso nær yfir kóðann. Aðeins tölur, þáttakóðar og "
    "segðir geymdar — valkostur A, issue #3."
)
PROSENTUSTIG = 100
# Punktarnir eru námundaðir að 0,1 % = 1 prómill; miðgildi þeirra má því
# víkja um hálft prómill frá óafrúnnuðu miðgildi samantektarinnar.
HALFT_PROMILL = 0.5 / adfang.PROMILL + 1e-12

INNSETNINGAR: tuple[tuple[str, str], ...] = (
    ("central_perk_sources",
     "INSERT INTO central_perk_sources (id, transcript_repository, transcript_commit, "
     "analysis_repository, analysis_commit, analysis_script, input_directory, "
     "provenance_file, licence, loaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"),
    ("central_perk_source_files",
     "INSERT INTO central_perk_source_files (file_name, sha256, size_bytes) VALUES (?, ?, ?)"),
    ("central_perk_groups",
     "INSERT INTO central_perk_groups (group_key, display_order, median_phoebe_share, "
     "mean_phoebe_share, median_friends_to_phoebe_ratio) VALUES (?, ?, ?, ?, ?)"),
    ("central_perk_transcript_files",
     "INSERT INTO central_perk_transcript_files (episode_code, group_key, "
     "phoebe_share_permille) VALUES (?, ?, ?)"),
    ("central_perk_singing",
     "INSERT INTO central_perk_singing (id, singing_scenes) VALUES (?, ?)"),
    ("central_perk_patterns",
     "INSERT INTO central_perk_patterns (pattern_name, display_order, pattern, catches, "
     "misses) VALUES (?, ?, ?, ?, ?)"),
)
# Eytt í öfugri innsetningarröð (börn fyrst). Fastir strengir (regla 5).
EYDINGAR: tuple[str, ...] = (
    "DELETE FROM central_perk_patterns",
    "DELETE FROM central_perk_singing",
    "DELETE FROM central_perk_transcript_files",
    "DELETE FROM central_perk_groups",
    "DELETE FROM central_perk_source_files",
    "DELETE FROM central_perk_sources",
)
TALNING = (
    "SELECT 'central_perk_sources', COUNT(*) FROM central_perk_sources UNION ALL "
    "SELECT 'central_perk_source_files', COUNT(*) FROM central_perk_source_files UNION ALL "
    "SELECT 'central_perk_groups', COUNT(*) FROM central_perk_groups UNION ALL "
    "SELECT 'central_perk_transcript_files', COUNT(*) FROM central_perk_transcript_files "
    "UNION ALL "
    "SELECT 'central_perk_singing', COUNT(*) FROM central_perk_singing UNION ALL "
    "SELECT 'central_perk_patterns', COUNT(*) FROM central_perk_patterns"
)
SAMANTEKT = "central-perk-samantekt"
HOPAR = "central-perk-hopar"
SONGHANDRIT = "central-perk-songhandrit"


def krefjast(skilyrdi: bool, skyring: str) -> None:
    """Stöðvar keyrsluna með skýringu ef skilyrðið bregst."""
    if not skilyrdi:
        raise adfang.CentralPerkVilla(f"Ósamræmi í Central Perk-aðfanginu: {skyring}")


def _nuna() -> str:
    """Tímastimpill í ISO 8601, UTC, á sekúndunákvæmni (klukka keyrslunnar)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def samraemi(samantekt: dict, punktar: list, midgildislinur: dict, segdir: list) -> None:
    """Sannar að skrárnar þrjár — og kóðinn — segi sömu sögu."""
    hopar = samantekt["groups"]
    krefjast(len(punktar) == samantekt["transcript_files"],
             f"{len(punktar)} punktar en {samantekt['transcript_files']} skrár í samantekt.")
    for hopur in GROUP_ORDER:
        gildi = [p.promill / adfang.PROMILL for p in punktar if p.hopur == hopur]
        krefjast(len(gildi) == hopar[hopur]["n"], f"{hopur}: {len(gildi)} punktar, n = "
                 f"{hopar[hopur]['n']}.")
        for maelt, fall in (("median_phoebe_share", statistics.median),
                            ("mean_phoebe_share", statistics.mean)):
            krefjast(abs(fall(gildi) - hopar[hopur][maelt]) <= HALFT_PROMILL,
                     f"{hopur}: {maelt} punktanna {fall(gildi)} víkur frá {hopar[hopur][maelt]}.")
        teiknad = midgildislinur[hopur][2]
        krefjast(abs(teiknad - hopar[hopur]["median_phoebe_share"]) <= HALFT_PROMILL,
                 f"{hopur}: miðgildislínan er við {teiknad}.")
    song = sorted(p.kodi for p in punktar if p.hopur == PHOEBE_SINGS)
    krefjast(song == samantekt["singing_episode_ids"],
             "sönghandritin í myndinni eru ekki þau sem samantektin nefnir.")
    krefjast(len(song) == samantekt["singing_files"], "singing_files ≠ fjöldi sönghandrita.")
    krefjast(samantekt["singing_scenes"] >= len(song), "færri söngsenur en sönghandrit.")
    munur = PROSENTUSTIG * (hopar[PHOEBE_SINGS]["median_phoebe_share"]
                            - hopar[CENTRAL_PERK_GROUP]["median_phoebe_share"])
    krefjast(munur == samantekt["median_difference_percentage_points"],
             f"munurinn {samantekt['median_difference_percentage_points']} ≠ {munur}.")
    krefjast([(n, s) for n, s, _, _ in segdir]
             == [(n, p.pattern) for n, p, _, _ in DOCUMENTED_PATTERNS],
             "segðirnar í regex.md eru ekki þær sem central_perk_mynstur keyrir.")


def _radir(skrar: list, samantekt: dict, punktar: list, segdir: list,
           mappa: Path, provenance: Path) -> dict[str, list]:
    """Raðirnar sem fara í hverja töflu, eftir töfluheiti."""
    hopar = samantekt["groups"]
    return {
        "central_perk_sources": [(
            1, TRANSCRIPT_REPOSITORY, SOURCE_COMMIT, ANALYSIS_REPOSITORY, ANALYSIS_COMMIT,
            ANALYSIS_SCRIPT, adfang.stutt_slod(mappa), adfang.stutt_slod(provenance),
            LEYFI, _nuna())],
        "central_perk_source_files": [(s.heiti, s.sha256, s.staerd) for s in skrar],
        "central_perk_groups": [
            (hopur, rod, hopar[hopur]["median_phoebe_share"], hopar[hopur]["mean_phoebe_share"],
             hopar[hopur]["median_friends_to_phoebe_ratio"])
            for rod, hopur in enumerate(GROUP_ORDER, start=1)],
        "central_perk_transcript_files": [(p.kodi, p.hopur, p.promill) for p in punktar],
        "central_perk_singing": [(1, samantekt["singing_scenes"])],
        "central_perk_patterns": [(n, rod, s, g, sl)
                                  for rod, (n, s, g, sl) in enumerate(segdir, start=1)],
    }


def _setja_inn(samband: Connection, radir: dict[str, list]) -> dict[str, int]:
    """Hreinsar töflurnar og setur raðirnar inn; skilar fjölda í hverri töflu."""
    for eyding in EYDINGAR:
        samband.execute(eyding)
    for tafla, innsetning in INNSETNINGAR:
        try:
            samband.executemany(innsetning, radir[tafla])
        except sqlite3.IntegrityError as villa:
            raise adfang.CentralPerkVilla(f"{tafla}: grunnurinn hafnaði færslu — {villa}") from villa
    fjoldi = dict(samband.execute(TALNING).fetchall())
    for tafla, _ in INNSETNINGAR:
        krefjast(fjoldi.get(tafla) == len(radir[tafla]),
                 f"{tafla}: {len(radir[tafla])} raðir sendar en {fjoldi.get(tafla)} í töflunni.")
    return fjoldi


def _stadfesta_ur_sql(samband: Connection, samantekt: dict) -> None:
    """Spyr fyrirspurna síðunnar og ber svörin við samantektina — nákvæmlega."""
    rad = fyrirspurnir.keyra(samband, SAMANTEKT)[0]
    fengid = (rad["transcript_files"], rad["singing_files"], rad["singing_scenes"],
              rad["median_difference_pp"])
    vaent = (samantekt["transcript_files"], samantekt["singing_files"],
             samantekt["singing_scenes"], samantekt["median_difference_percentage_points"])
    krefjast(fengid == vaent, f"{SAMANTEKT} gaf {fengid}, samantektin segir {vaent}.")

    hopar = [(r["group_key"], r["transcript_files"], r["median_phoebe_share"],
              r["mean_phoebe_share"], r["median_friends_to_phoebe_ratio"])
             for r in fyrirspurnir.keyra(samband, HOPAR)]
    vaent_hopar = [(h, *samantekt["groups"][h].values()) for h in GROUP_ORDER]
    krefjast(hopar == vaent_hopar, f"{HOPAR} gaf {hopar}.")

    song = [r["episode_code"] for r in fyrirspurnir.keyra(samband, SONGHANDRIT)]
    krefjast(song == samantekt["singing_episode_ids"], f"{SONGHANDRIT} gaf {song}.")


def hlada(samband: Connection, mappa: Path = adfang.ADFANGSMAPPA,
          provenance: Path = adfang.PROVENANCE) -> dict[str, int]:
    """Hleður Central Perk-niðurstöðunum og skilar fjölda raða í hverri töflu.

    Kallandinn á færsluna (``gagnagrunnur.tenging.tenging``: commit eða
    rollback), svo grunnurinn situr aldrei með hálfa hleðslu.
    """
    skrar = adfang.stadfesta_skrar(mappa, provenance)
    samantekt = adfang.lesa_samantekt(mappa)
    punktar, midgildislinur = adfang.lesa_punkta(mappa)
    segdir = adfang.lesa_segdir(mappa)
    samraemi(samantekt, punktar, midgildislinur, segdir)
    fjoldi = _setja_inn(samband, _radir(skrar, samantekt, punktar, segdir, mappa, provenance))
    _stadfesta_ur_sql(samband, samantekt)
    return fjoldi


def main(rok: list[str] | None = None) -> int:
    """Keyrir migrations og hleður Central Perk-niðurstöðunum í grunninn."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    if rok:
        raise SystemExit(f"Þessi eining tekur enga viðbótarröksemd, fékk: {rok}")
    with tenging() as samband:
        keyra(samband)
        fjoldi = hlada(samband)
        rad = fyrirspurnir.keyra(samband, SAMANTEKT)[0]
    log.info("Hlóð Central Perk: %d handritsskrár, %d sönghandrit, %d söngsenur, %d segðir.",
             fjoldi["central_perk_transcript_files"], rad["singing_files"],
             rad["singing_scenes"], fjoldi["central_perk_patterns"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
