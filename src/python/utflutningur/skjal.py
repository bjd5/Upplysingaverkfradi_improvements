"""Sameiginlegt snið allra skráa í ``web/gogn/`` (regla 5.4, issue #15).

Hver skrá er::

    {"uppfaert": "<ISO 8601, UTC>", "heimild": "<þjónusta — slóð (leyfi)>", "gogn": …}

**``uppfaert`` er dagsetning gagnanna, aldrei klukkan við útflutning.** Klukkan
gerði úttakið óákvarðað: tvær keyrslur sömu gagna gæfu ólík bæti eftir því
hvorum megin sekúndumarka þær lentu (lærdómurinn af #47 og athugasemd á #14,
liður 8). Í staðinn stendur hér *sóknartími* safnsins — hvenær vefþjónustan
svaraði — lesinn úr grunninum (``fetch_log``, ``hagstofan_datasets``,
``mbl_snapshots``) eða úr provenance frosna safnsins, og fyrir Friends
*reiknitími greiningarinnar* (``friends_sources.analysis_generated_utc``).
Á síðunni merkir „Gögn uppfærð“ því: *hvenær þessi gögn voru sótt eða reiknuð*.
Tímastimpillinn er styttur í heilar sekúndur og færður í UTC-snið
``YYYY-MM-DDTHH:MM:SS+00:00`` sem ``new Date()`` í vafranum les.

**``heimild`` er strengur** af því að ``stada-gagna.js`` skeytir honum beint
inn í texta; ítarlegri uppruni (slóð, sóknartími, leyfi, hrágagnaskrá) er í
``gogn["uppruni"]`` svo síðan geti sýnt rekjanleikann (regla 8).

**Námundun gerist hér, ekki í vafranum** (fyrirspurnirnar skila óafrúnnuðu,
sjá ``gagnagrunnur.fyrirspurnir``). ``namunda`` notar ``round`` Python — sömu
venju og gamla síðan og ``utflutningur.islenskt_snid``.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

LYKLAR = ("uppfaert", "heimild", "gogn")
STRIK = " — "


class UtflutningsVilla(RuntimeError):
    """Gögnin í grunninum duga ekki í skrána sem síðan þarf."""


@dataclass(frozen=True)
class Uppruni:
    """Hvaðan safnið kemur: það sem ``heimild`` og ``gogn["uppruni"]`` sýna."""

    thjonusta: str
    slod: str
    leyfi: str
    sott: str
    hragogn: str

    @property
    def heimild(self) -> str:
        """``Veðurstofa Íslands — api.vedur.is/quakes/events (CC BY 4.0)``."""
        return f"{self.thjonusta}{STRIK}{stutt_slod(self.slod)} ({self.leyfi})"

    def sem_gogn(self) -> dict:
        return {
            "thjonusta": self.thjonusta,
            "slod": self.slod,
            "leyfi": self.leyfi,
            "sott": utc_stimpill(self.sott),
            "hragogn": self.hragogn,
        }


def stutt_slod(slod: str) -> str:
    """Slóð án ``https://`` og ``www.`` — eins og issue #15 sýnir heimildina."""
    for forskeyti in ("https://", "http://", "www."):
        if slod.startswith(forskeyti):
            slod = slod[len(forskeyti):]
    return slod.rstrip("/")


def utc_stimpill(texti: str) -> str:
    """ISO-tími úr gögnunum sem ``YYYY-MM-DDTHH:MM:SS+00:00``.

    Tími án tímabeltis er hafnað: hann gæti verið staðartími og þá væri
    dagsetningin á síðunni ágiskun (regla 6).
    """
    try:
        stund = datetime.fromisoformat(str(texti))
    except ValueError as villa:
        raise UtflutningsVilla(f"{texti!r} er ekki ISO 8601 tími.") from villa
    if stund.tzinfo is None:
        raise UtflutningsVilla(f"{texti!r} hefur ekkert tímabelti; UTC er ekki ágiskað.")
    return stund.astimezone(UTC).replace(microsecond=0).isoformat()


def namunda(gildi: float | int | None, aukastafir: int) -> float | int | None:
    """Námundar birtingargildi; heiltölur og ``None`` fara óbreytt í gegn."""
    if gildi is None or isinstance(gildi, int):
        return gildi
    return round(float(gildi), aukastafir)


def skjal(uppruni: Uppruni, gogn: dict | list, uppfaert: str | None = None) -> dict:
    """Skrá á sniði reglu 5.4. ``uppfaert`` er sóknartími safnsins nema annað sé gefið."""
    return {
        "uppfaert": utc_stimpill(uppfaert if uppfaert is not None else uppruni.sott),
        "heimild": uppruni.heimild,
        "gogn": gogn,
    }


def lesa_provenance(slod: Path, reitir: tuple[str, ...]) -> dict:
    """Les provenance frosins safns og krefst reitanna sem útflutningurinn notar.

    Aðeins fyrir það sem grunnurinn geymir ekki (t.d. sóknartíma skjálftanna,
    sem 002 skráir hvergi): gildið er þá lesið úr sömu skrá og hleðslan
    sannreyndi, aldrei slegið inn í kóða.
    """
    try:
        skjal_ = json.loads(slod.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as villa:
        raise UtflutningsVilla(f"Gat ekki lesið provenance {slod}: {villa}") from villa
    vantar = [reitur for reitur in reitir if not skjal_.get(reitur)]
    if vantar:
        raise UtflutningsVilla(f"{slod} vantar reitina {', '.join(vantar)}.")
    return skjal_


def ein_rod(radir: list, lysing: str) -> object:
    """Nákvæmlega ein röð — engin eða fleiri þýða að grunnurinn er ekki eins og síðan væntir."""
    if len(radir) != 1:
        raise UtflutningsVilla(f"{lysing}: vænti einnar raðar, fékk {len(radir)}.")
    return radir[0]
