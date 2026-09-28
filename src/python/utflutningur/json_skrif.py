"""Sameiginlega lagið fyrir JSON-útflutning í ``web/gogn/`` (regla 5.4, issue #15).

Hver útflutningseining skilar **umslagi** á föstu sniði::

    {
      "uppfaert": "2026-09-24T11:22:18+00:00",
      "heimild": "Veðurstofa Íslands — api.vedur.is/weather/stations (CC BY 4.0)",
      "gogn": [ ... ],
      "lysigogn": { ... }          # valfrjálst
    }

``uppfaert`` og ``gogn`` eru krafa reglu 5.4, ``heimild`` krafa issue #15.
``lysigogn`` er eini reiturinn sem má bætast við: þar fer það sem síðan þarf
til að *lesa* gögnin rétt — fyrirspurnin sem var send, víddirnar, afmörkunin —
en er ekki sjálft ein röð í ``gogn``. Aðrir reitir stöðva útflutninginn, svo
snið skrárinnar geti ekki vaxið óséð.

Þrjár tryggingar eru hér á einum stað svo engin eining þurfi að muna þær:

* **Sannreyning fyrir skrif.** Umslagið er sannreynt og raðað í bæti *áður*
  en nokkuð er skrifað. ``NaN`` og ``Infinity`` eru ekki JSON og stöðva
  útflutninginn (``allow_nan=False``) í stað þess að enda sem ógild skrá.
* **Atómísk skrif.** Bætin fara í tímabundna skrá í *sömu möppu* og færast svo
  yfir með :func:`os.replace`, sem er atómískt innan sama skráarkerfis. Eldri
  skrá stendur því annaðhvort óbreytt eða er leyst af hólmi í heilu lagi —
  hálfskrifuð JSON-skrá verður aldrei til (regla 6). Misheppnist skrifin er
  tímabundna skráin fjarlægð og villan heldur áfram upp.
* **Ákvarðað úttak.** Sama umslag gefur alltaf sömu bæti (föst inndráttur,
  röð reita eins og einingin gaf hana, ``\\n`` í lokin).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REITIR_SKYLDA = ("uppfaert", "heimild", "gogn")
REITUR_LYSIGOGN = "lysigogn"
LEYFDIR_REITIR = frozenset((*REITIR_SKYLDA, REITUR_LYSIGOGN))

# Þak á eina gagnaskrá. Öll fyrsta hleðsla síðu má vera 500 KB (regla 3.4) og
# síðan ber líka HTML, CSS og letur; ein JSON-skrá sem fer yfir fimmtung þess
# er heil tafla en ekki samantekt og á að stöðva útflutninginn.
HAMARKS_BAETI = 100_000

INNDRATTUR = 2
KODUN = "utf-8"
FORSKEYTI_TIMABUNDIN = "."
VIDSKEYTI_TIMABUNDIN = ".tmp"
# mkstemp býr skrána til með 0600. Vefþjónn þarf að geta lesið hana, svo hún fær
# sömu heimildir og venjuleg skrá í repo-inu áður en hún leysir þá eldri af hólmi.
HEIMILDIR_SKRAR = 0o644


class UtflutningsVilla(RuntimeError):
    """Útflutningur tókst ekki; engri skrá í úttaksmöppunni var breytt."""


def utc_timastimpill(texti: str) -> str:
    """Staðlar ISO 8601 tímastimpil í UTC á sniðinu ``2026-09-24T11:22:18+00:00``.

    Grunnurinn geymir sóknartíma á tveimur sniðum (``...Z`` úr provenance
    veðurstöðvanna, ``...+00:00`` úr Hagstofunni). Síðan á að fá eitt snið.
    Tímastimpill án tímabeltis er tvíræður og stöðvar útflutninginn.
    """
    try:
        stund = datetime.fromisoformat(texti)
    except (TypeError, ValueError) as villa:
        raise UtflutningsVilla(f"Ekki gildur ISO 8601 tímastimpill: {texti!r}") from villa
    if stund.tzinfo is None:
        raise UtflutningsVilla(
            f"Tímastimpillinn {texti!r} hefur ekkert tímabelti og er því tvíræður."
        )
    return stund.astimezone(UTC).isoformat(timespec="seconds")


def byggja_umslag(
    uppfaert: str,
    heimild: str,
    gogn: list[Any],
    lysigogn: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Setur saman umslagið í fastri reitaröð og sannreynir það."""
    umslag: dict[str, Any] = {
        "uppfaert": utc_timastimpill(uppfaert),
        "heimild": heimild,
        "gogn": gogn,
    }
    if lysigogn is not None:
        umslag[REITUR_LYSIGOGN] = lysigogn
    sannreyna_umslag(umslag)
    return umslag


def sannreyna_umslag(umslag: dict[str, Any]) -> None:
    """Stöðvar með :class:`UtflutningsVilla` ef umslagið stenst ekki sniðið.

    ``uppfaert`` verður að vera þegar staðlað (sjá :func:`utc_timastimpill`):
    tvö snið á sama tíma myndu gefa tvær ólíkar skrár úr sömu gögnum.
    """
    if not isinstance(umslag, dict):
        raise UtflutningsVilla(f"Umslagið á að vera hlutur, fékk {type(umslag).__name__}.")
    vantar = [reitur for reitur in REITIR_SKYLDA if reitur not in umslag]
    if vantar:
        raise UtflutningsVilla("Umslagið vantar reitina: " + ", ".join(vantar))
    aukreitir = sorted(set(umslag) - LEYFDIR_REITIR)
    if aukreitir:
        raise UtflutningsVilla(
            "Óþekktir reitir í umslaginu: " + ", ".join(aukreitir)
            + f". Leyfðir eru {', '.join(sorted(LEYFDIR_REITIR))}."
        )

    uppfaert = umslag["uppfaert"]
    if not isinstance(uppfaert, str) or utc_timastimpill(uppfaert) != uppfaert:
        raise UtflutningsVilla(
            f"'uppfaert' er ekki staðlaður UTC-tímastimpill: {uppfaert!r}"
        )
    heimild = umslag["heimild"]
    if not isinstance(heimild, str) or not heimild.strip():
        raise UtflutningsVilla("'heimild' verður að vera óauður texti — hver tala á sér uppruna (regla 8).")
    gogn = umslag["gogn"]
    if not isinstance(gogn, list) or not gogn:
        raise UtflutningsVilla(
            "'gogn' verður að vera listi með minnst einni færslu. Tómur listi úr "
            "gagnasafni þýðir að lesturinn úr grunninum mistókst."
        )
    if REITUR_LYSIGOGN in umslag and not isinstance(umslag[REITUR_LYSIGOGN], dict):
        raise UtflutningsVilla("'lysigogn' verður að vera hlutur ef hann er með.")


def sem_baeti(umslag: dict[str, Any]) -> bytes:
    """Raðar sannreyndu umslagi í ákvörðuð UTF-8 bæti."""
    sannreyna_umslag(umslag)
    try:
        texti = json.dumps(umslag, ensure_ascii=False, indent=INNDRATTUR, allow_nan=False)
    except (TypeError, ValueError) as villa:
        raise UtflutningsVilla(f"Umslagið er ekki hægt að rita sem JSON: {villa}") from villa
    baeti = (texti + "\n").encode(KODUN)
    if len(baeti) > HAMARKS_BAETI:
        raise UtflutningsVilla(
            f"Skráin yrði {len(baeti)} bæti en þakið er {HAMARKS_BAETI}. Flyttu út "
            "samantekt sem síðan þarf, ekki heila töflu (regla 3.4)."
        )
    return baeti


def skrifa_atomiskt(slod: Path, baeti: bytes) -> None:
    """Skrifar bætin í ``slod`` þannig að eldri skrá sé óbreytt nema allt takist.

    Mappan verður að vera til: sé henni ruglað saman við aðra slóð á villan að
    sjást, ekki ný mappa að verða til einhvers staðar.
    """
    mappa = slod.parent
    if not mappa.is_dir():
        raise UtflutningsVilla(f"Úttaksmappan er ekki til: {mappa}")

    lysing, timabundin = tempfile.mkstemp(
        dir=mappa, prefix=FORSKEYTI_TIMABUNDIN + slod.name + ".", suffix=VIDSKEYTI_TIMABUNDIN
    )
    try:
        with os.fdopen(lysing, "wb") as skra:
            os.fchmod(skra.fileno(), HEIMILDIR_SKRAR)
            skra.write(baeti)
            skra.flush()
            os.fsync(skra.fileno())
        os.replace(timabundin, slod)
    except BaseException:
        Path(timabundin).unlink(missing_ok=True)
        raise


def skrifa_umslag(mappa: Path, skraarheiti: str, umslag: dict[str, Any]) -> Path:
    """Sannreynir, raðar og skrifar umslagið atómískt. Skilar slóð skrárinnar."""
    slod = Path(mappa) / skraarheiti
    skrifa_atomiskt(slod, sem_baeti(umslag))
    return slod
