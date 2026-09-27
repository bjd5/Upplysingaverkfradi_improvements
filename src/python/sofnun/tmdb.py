"""Friends og hlutverk Phoebe í gagnagrunni TMDB (gagnasafn 5).

Flutt úr ``src/fetch_tmdb.py`` upprunaverkefnisins. Tvö köll:
grunnupplýsingar þáttarins og ``aggregate_credits``, sem safnar öllum hlutverkum
sömu manneskju í eina færslu — þess vegna er þáttafjöldi Phoebe réttur þar en
tvítalinn í venjulegu ``credits``.

**Þetta er eina safnið sem krefst lykils.** Hann kemur úr ``TMDB_TOKEN`` í
umhverfinu eða ``.env`` og er gefinn ``sofnun.http`` sem leynihaus: hann fer í
beiðnina og hvergi annað — ekki í provenance, ekki í logg, ekki í villuboð
(regla 4). Repo-ið er opið og lykillinn er persónulegur aðgangur að þjónustu.

Safnið náðist ekki að frysta í P0.3 því enginn lykill var til; það er skráð
ófryst í ``data/raw/frysting.json``. Þangað til lykill er settur inn hefur
síðan sem byggir á þessu safni engar tölur að birta.
"""

from __future__ import annotations

from . import stillingar
from .beidni import Beidni
from .hragogn import Svar
from .http import saekja

LYKILS_BREYTA = "TMDB_TOKEN"
LYKILS_SKYRING = (
    "hún geymir „API Read Access Token\" af https://www.themoviedb.org/settings/api"
)

GRUNNSLOD = "https://api.themoviedb.org/3"
SKJOLUN = "https://developer.themoviedb.org/reference/tv-series-details"
THATTUR = 1668          # Friends á TMDB: https://www.themoviedb.org/tv/1668-friends

# Tungumálið er hluti af úrtakinu: hlutverkaheiti eru þýdd og önnur stilling
# gæfi önnur nöfn í sömu reitum.
TUNGUMAL = "en-US"


def _beidni(vidskeyti: str, heiti: str) -> Beidni:
    """Byggir beiðni á TMDB-endapunkt. Lykillinn kemur hvergi hér nærri."""
    return Beidni(
        thjonusta="tmdb",
        veitandi="The Movie Database (TMDB)",
        slod=f"{GRUNNSLOD}/tv/{THATTUR}{vidskeyti}",
        heiti=heiti,
        skjolun=SKJOLUN,
        breytur={"language": TUNGUMAL},
        hausar={"Accept": "application/json"},
        leyfi="TMDB Terms of Use",
        leyfisslod="https://www.themoviedb.org/terms-of-use",
    )


THATTAR_BEIDNI = _beidni("", "thattur")
LEIKARA_BEIDNI = _beidni("/aggregate_credits", "leikarar")


def leynihausar(lykill: str | None = None) -> dict[str, str]:
    """Skilar auðkenningarhausnum. Lykillinn kemur úr umhverfinu nema hann sé gefinn."""
    gildi = lykill if lykill is not None else stillingar.krefjast(
        LYKILS_BREYTA, LYKILS_SKYRING
    )
    return {"Authorization": f"Bearer {gildi}"}


def saekja_tmdb(*, lykill: str | None = None, **rok) -> tuple[Svar, Svar]:
    """Sækir þátt og leikaraskrá og skilar báðum svörum.

    Aukabreytur fara óbreyttar í ``sofnun.http.saekja``.
    """
    hausar = leynihausar(lykill)
    thattur = saekja(THATTAR_BEIDNI, leynihausar=hausar, **rok)
    leikarar = saekja(LEIKARA_BEIDNI, leynihausar=hausar, **rok)
    return thattur, leikarar
