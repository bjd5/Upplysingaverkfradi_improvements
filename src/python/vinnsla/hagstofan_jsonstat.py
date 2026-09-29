"""Lestur á frysta json-stat2-svari Hagstofunnar — röðun einingarinnar í heild.

json-stat2 skilar marghliða töflu sem **flötum** gildalista: víddalýsingin í
``dimension`` segir hvernig á að lesa hann. Rangur lestur gefur tölur sem líta
rétt út en eiga við annað — brautskráningarhlutfall kvenna endar á karlalínunni.
Þess vegna er verkinu skipt upp (regla 6):

* ``hagstofan_snid``        — formin sem lesturinn skilar, engin rökvísi,
* ``hagstofan_sannreyning`` — það sem stöðvar lesturinn: gátsummur, útgáfa og
  að **fjöldi gilda sé nákvæmlega margfeldi víddastærðanna**,
* ``hagstofan_viddir``      — lestur víddalýsingarinnar og kóðabókarinnar,
* þessi skrá                — umbreyting flata listans í eina röð á
  samsetningu, og röðun hlutanna saman.

Bregðist eitthvað er kastað :class:`~.hagstofan_snid.JsonstatVilla` og engin
lína fer í grunninn (regla 6: villur eru aldrei þaggaðar, hálf tafla er verri
en engin).

Einingin snertir hvorki gagnagrunn né net — hún les eingöngu frystu skrárnar í
``data/raw/hagstofan/`` og breytir þeim aldrei (regla 4).
"""

from __future__ import annotations

from collections.abc import Iterator
from itertools import product
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .hagstofan_sannreyning import (
    krefjast_strengs,
    lesa_json,
    sannreyna_gildafjolda,
    sannreyna_summur,
    sannreyna_utgafu,
)
from .hagstofan_snid import (
    LYSIGAGNASKRA,
    SVARSKRA,
    UPPRUNASKRA,
    Gagnasafn,
    JsonstatVilla,
    Maeling,
    Vidd,
)
from .hagstofan_viddir import lesa_viddir


def lesa_gagnasafn(mappa: Path) -> Gagnasafn:
    """Les og sannreynir frysta svarið í ``mappa`` og skilar því lesnu.

    Kastar :class:`~.hagstofan_snid.JsonstatVilla` víki nokkuð frá væntri
    byggingu. Ekkert er skrifað neitt — kallandinn á færsluna.
    """
    upprunagogn = lesa_json(mappa / UPPRUNASKRA)
    sannreyna_summur(mappa, upprunagogn)

    svar = lesa_json(mappa / SVARSKRA)
    lysigogn = lesa_json(mappa / LYSIGAGNASKRA)

    sannreyna_utgafu(svar)
    viddir = lesa_viddir(svar, lysigogn)
    maelingar = lesa_maelingar(svar, viddir)

    endapunktur = krefjast_strengs(upprunagogn, "endpoint", UPPRUNASKRA)
    return Gagnasafn(
        audkenni=_audkenni_ur_endapunkti(endapunktur),
        heiti=krefjast_strengs(svar, "label", SVARSKRA),
        heimild=krefjast_strengs(svar, "source", SVARSKRA),
        endapunktur=endapunktur,
        sott_kl=krefjast_strengs(upprunagogn, "fetched_at_utc", UPPRUNASKRA),
        uppfaert=svar.get("updated"),
        utgafa=str(svar["version"]),
        aukastafir=svar.get("extension", {}).get("px", {}).get("decimals"),
        hraskra=str(mappa / SVARSKRA),
        viddir=viddir,
        maelingar=maelingar,
    )


def _audkenni_ur_endapunkti(endapunktur: str) -> str:
    """Dregur töfluauðkennið (t.d. ``SKO04208b``) út úr slóð endapunktsins."""
    audkenni = Path(urlsplit(endapunktur).path).stem
    if not audkenni:
        raise JsonstatVilla(
            f"Ekkert töfluauðkenni verður lesið úr endapunktinum {endapunktur!r}."
        )
    return audkenni

# --- Flati gildalistinn í raðir ------------------------------------------------
#
# ``value`` í json-stat2 er flatt fylki. Röðunin er skilgreind: víddirnar raðast
# eins og ``id`` gefur þær og SÍÐASTA víddin breytist hraðast, nákvæmlega eins og
# ``itertools.product`` telur. Kóðarnir innan hverrar víddar koma úr
# ``category.index``, ekki úr lyklaröð ``label`` — sjá ``Vidd.valin_gildi``.
#
# Hér er ekkert reiknað og engu sleppt: hvert gildi listans verður að einni
# ``Maeling`` með þeirri samsetningu vídda sem á við það. Stemmi lengd listans
# ekki við margfeldi víddastærðanna er stöðvað áður en fyrsta mælingin verður
# til (``sannreyna_gildafjolda``).

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
