"""Les breytingar úr klóni upprunarepo-sins með git.

Eina einingin í pakkanum sem talar við git. Allt annað vinnur á hreinum
gögnum og er prófað án git.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

STODUHEITI = {
    "A": "bætt við",
    "M": "breytt",
    "D": "eytt",
    "R": "fært",
    "C": "afritað",
    "T": "gerð breytt",
}


class SoguVilla(RuntimeError):
    """git gat ekki svarað: klónið vantar, commit finnst ekki o.s.frv."""


@dataclass(frozen=True)
class Breyting:
    """Ein breytt skrá milli tveggja commita."""

    stada: str
    slod: str
    gomul_slod: str | None = None

    @property
    def lysing(self) -> str:
        """Breytingin á íslensku, t.d. „fært frá `a.py`“."""
        heiti = STODUHEITI.get(self.stada, self.stada)
        return f"{heiti} frá `{self.gomul_slod}`" if self.gomul_slod else heiti


def _git(klon: Path, *rok: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(klon), *rok], check=True, capture_output=True
        ).stdout
    except FileNotFoundError as villa:
        raise SoguVilla("git er ekki uppsett á þessari vél.") from villa
    except subprocess.CalledProcessError as villa:
        skilabod = villa.stderr.decode("utf-8", "replace").strip()
        raise SoguVilla(f"`git {' '.join(rok)}` mistókst: {skilabod}") from villa


def commit(klon: Path, tilvisun: str) -> str:
    """Skilar fullu SHA commits sem `tilvisun` vísar á."""
    return _git(klon, "rev-parse", "--verify", f"{tilvisun}^{{commit}}").decode().strip()


def dagsetning(klon: Path, tilvisun: str) -> str:
    """Skilar commit-tíma sem ISO-dagsetningu (YYYY-MM-DD)."""
    return _git(klon, "log", "-1", "--format=%cs", tilvisun).decode().strip()


def fjoldi_commita(klon: Path, fra: str, til: str) -> int:
    """Telur commit sem eru í `til` en ekki í `fra`."""
    return int(_git(klon, "rev-list", "--count", f"{fra}..{til}").decode().strip())


def er_forfadir(klon: Path, fra: str, til: str) -> bool:
    """Satt ef `fra` er í sögu `til` — annars var sagan endurskrifuð."""
    try:
        _git(klon, "merge-base", "--is-ancestor", fra, til)
    except SoguVilla:
        commit(klon, fra)  # kastar skýrari villu ef fra er ekki til í klóninu
        return False
    return True


def lesa_breytingar(uttak: bytes) -> list[Breyting]:
    """Þáttar úttak `git diff -z --name-status` í lista af breytingum."""
    hlutar = uttak.decode("utf-8").split("\0")
    breytingar: list[Breyting] = []
    i = 0
    while i < len(hlutar) and hlutar[i]:
        stada = hlutar[i][0]
        if stada in "RC":
            breytingar.append(Breyting(stada, hlutar[i + 2], hlutar[i + 1]))
            i += 3
        else:
            breytingar.append(Breyting(stada, hlutar[i + 1]))
            i += 2
    return breytingar


def breytingar(klon: Path, fra: str, til: str) -> list[Breyting]:
    """Allar skrár sem breyttust milli `fra` og `til`, í stafrófsröð."""
    uttak = _git(klon, "diff", "-z", "--name-status", "-M", fra, til)
    return sorted(lesa_breytingar(uttak), key=lambda b: b.slod)


def skrar(klon: Path, til: str) -> list[str]:
    """Allar skrár í tré `til`."""
    return _git(klon, "ls-tree", "-r", "-z", "--name-only", til).decode().split("\0")[:-1]


def innihald(klon: Path, til: str, slod: str) -> bytes:
    """Innihald skráar eins og hún er í `til`."""
    return _git(klon, "show", f"{til}:{slod}")
