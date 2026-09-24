"""Lestur á frysta json-stat2-svari Hagstofunnar — röðun einingarinnar í heild.

json-stat2 skilar marghliða töflu sem **flötum** gildalista: víddalýsingin í
``dimension`` segir hvernig á að lesa hann. Rangur lestur gefur tölur sem líta
rétt út en eiga við annað — brautskráningarhlutfall kvenna endar á karlalínunni.
Þess vegna er verkinu skipt í þrennt og hver hluti á sína skrá (regla 6):

* ``hagstofan_snid``        — formin sem lesturinn skilar, engin rökvísi,
* ``hagstofan_sannreyning`` — það sem stöðvar lesturinn: gátsummur, útgáfa og
  að **fjöldi gilda sé nákvæmlega margfeldi víddastærðanna**,
* ``hagstofan_viddir``      — lestur víddalýsingarinnar og kóðabókarinnar,
* ``hagstofan_gildi``       — umbreyting flata listans í eina röð á samsetningu.

Þessi skrá raðar þeim saman og gerir ekkert annað. Bregðist eitthvað er kastað
:class:`~.hagstofan_snid.JsonstatVilla` og engin lína fer í grunninn (regla 6:
villur eru aldrei þaggaðar, hálf tafla er verri en engin).

Einingin snertir hvorki gagnagrunn né net — hún les eingöngu frystu skrárnar í
``data/raw/hagstofan/`` og breytir þeim aldrei (regla 4).
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from .hagstofan_gildi import lesa_maelingar
from .hagstofan_sannreyning import (
    krefjast_strengs,
    lesa_json,
    sannreyna_summur,
    sannreyna_utgafu,
)
from .hagstofan_snid import (
    LYSIGAGNASKRA,
    SVARSKRA,
    UPPRUNASKRA,
    Gagnasafn,
    JsonstatVilla,
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
