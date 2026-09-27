"""Umbreyting flata gildalistans í raðir — eina mælingu á hverja samsetningu vídda.

``value`` í json-stat2 er flatt fylki. Röðunin er skilgreind: víddirnar raðast
eins og ``id`` gefur þær og SÍÐASTA víddin breytist hraðast, nákvæmlega eins og
``itertools.product`` telur. Kóðarnir innan hverrar víddar koma úr
``category.index``, ekki úr lyklaröð ``label`` — sjá
:attr:`~.hagstofan_snid.Vidd.valin_gildi`.

Einingin reiknar ekkert og sleppir engu: hvert gildi listans verður að einni
:class:`~.hagstofan_snid.Maeling` með þeirri samsetningu vídda sem á við það.
Stemmi lengd listans ekki við margfeldi víddastærðanna er stöðvað áður en
fyrsta mælingin verður til (``hagstofan_sannreyning.sannreyna_gildafjolda``).
"""

from __future__ import annotations

from collections.abc import Iterator
from itertools import product
from typing import Any

from .hagstofan_sannreyning import sannreyna_gildafjolda
from .hagstofan_snid import SVARSKRA, JsonstatVilla, Maeling, Vidd

# Samsetning vídda fyrir eina mælingu: (víddarkóði, gildiskóði) á hverja vídd.
Samsetning = tuple[tuple[str, str], ...]


def lesa_maelingar(
    svar: dict[str, Any], viddir: tuple[Vidd, ...]
) -> tuple[Maeling, ...]:
    """Flettir flata gildalistanum út í eina mælingu á hverja samsetningu vídda."""
    gildi = _gildalisti(svar)
    sannreyna_gildafjolda(len(gildi), viddir)
    return tuple(
        Maeling(
            flat_stada=stada,
            kodar=samsetning,
            gildi=_tala(gildi[stada], stada, samsetning),
        )
        for stada, samsetning in enumerate(_samsetningar(viddir))
    )


def _gildalisti(svar: dict[str, Any]) -> list[Any]:
    """Sækir ``value`` úr svarinu."""
    gildi = svar.get("value")
    if not isinstance(gildi, list):
        raise JsonstatVilla(f"{SVARSKRA} vantar `value` sem lista.")
    return gildi


def _samsetningar(viddir: tuple[Vidd, ...]) -> Iterator[Samsetning]:
    """Telur samsetningar víddanna í sömu röð og flati listinn liggur."""
    asar = [[(vidd.kodi, g.kodi) for g in vidd.valin_gildi] for vidd in viddir]
    return product(*asar)


def _tala(hragildi: Any, stada: int, samsetning: Samsetning) -> float:
    """Skilar einu gildi sem tölu og stöðvar sé það eitthvað annað.

    ``bool`` er undanskilið sérstaklega: í Python er það undirgerð ``int`` og
    ``True`` myndi annars renna í gegn sem talan 1.
    """
    if isinstance(hragildi, bool) or not isinstance(hragildi, (int, float)):
        raise JsonstatVilla(
            f"Gildi nr. {stada} í `value` er {hragildi!r} en ekki tala. "
            "Eyður í json-stat2 eru ekki studdar hér — samsetningin "
            f"{samsetning} ætti sér þá ekkert gildi."
        )
    return float(hragildi)
