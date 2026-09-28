"""Sýnidæmi myndritalagsins: daglegir skjálftar á Reykjanesi (issues #17 og #20).

Stöplarit með einni súlu á hvern UTC-dag úrtaksins (61 dagur). Tölurnar koma úr
``vinnsla.jardskjalftar_talning`` á frosnu hrágögnunum — hér er ekkert talið,
aðeins teiknað.

**Lograkvarði á y-ás**, eins og á gömlu síðunni: stærsti dagurinn (187 atburðir)
myndi annars fletja alla hina út. Kvarðinn hefur tvær afleiðingar sem eru
leystar hér en ekki faldar:

* Súla fyrir 1 atburð hefði hæðina núll ef ásinn byrjaði í 1. Ásinn byrjar því
  í ``NEDRA_MARK`` (0,5) og allar súlur rísa þaðan.
* **Núll á sér engan stað á lograkvarða.** Dagar án atburðar fá því enga súlu
  heldur **opinn hring** við grunnlínuna, og skýringin nefnir hann með texta.
  Munurinn á súludegi og núll-degi er þannig borinn af *lögun og texta*, ekki
  af lit einum (regla 3.3) — prófin þvinga það.

Keyrsla (skrifar bæði þemu í ``web/assets/img/``)::

    PYTHONPATH=src/python python -m utflutningur.myndrit_skjalftar
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter

from vinnsla.jardskjalftar import lesa_skjalfta
from vinnsla.jardskjalftar_afmorkun import SkjalftaVilla, lesa_afmorkun
from vinnsla.jardskjalftar_talning import DagsTalning, dagar_an_atburda, dagleg_talning

from . import myndrit, myndrit_litir as hlutverk
from .islenskt_snid import islensk_dagsetning, islensk_prosenta, islensk_tala
from .tokens import DOKKT, LJOST, Thema, TokenVilla, lesa_tokens

log = logging.getLogger(__name__)

SKRAARHEITI = {
    LJOST: "skjalftar-dagar-ljost.svg",
    DOKKT: "skjalftar-dagar-dokkt.svg",
}

TITILL = "Skjálftar á dag á Reykjanesi, {fra}–{til}"
# Titillinn notar styttu mánaðarheitin svo hann rúmist í BREIDD myndritsins.
Y_TEXTI = "Atburðir á dag (lograkvarði)"
X_TEXTI = "Dagur (UTC)"
SKYRING_SULA = "Atburðir þann dag"
SKYRING_NULL = "Enginn atburður í úrtakinu (0)"
HEIMILD = (
    "Heimild: Veðurstofa Íslands (CC BY 4.0). {atburdir} atburðir á {dagar} dögum; "
    "{null} dagar án atburðar ({hlutfall})."
)

# Lograkvarðinn byrjar hér svo súla fyrir 1 atburð sjáist (sjá docstring).
NEDRA_MARK = 0.5
# Núll-merkið situr mitt á milli NEDRA_MARK og 1 á lograkvarða (√0,5), þar sem
# engin súla er á núll-degi — merkið skarast því aldrei við súlu.
NULL_HAED = NEDRA_MARK ** 0.5
# Rými ofan við hæstu súluna fyrir skýringuna, sem margfeldi á lograkvarða.
EFRA_RYMI = 1.8
SULUBREIDD = 0.8
NULL_MERKI = "o"  # opinn hringur — önnur lögun en súla
NULL_STAERD = 5
NULL_LINA = 1.5
LOG_GRUNNUR = 10
# Merktir dagar á x-ás: 1. og 15. hvers mánaðar.
MERKTIR_DAGAR = ("01", "15")
# Heimildarlínan byrjar við vinstri brún myndarinnar, undir ásunum.
HEIMILD_X = 0.0

# Eitt auðkenni á einn hlut: núll-merkin eru ein lína í SVG-inu. Súlurnar fá
# ekkert gid, því matplotlib setti það á hverja súlu og id verður að vera einkvæmt.
MERKI_NULL = "null-dagar"


def byggja_mynd(dagatalning: list[DagsTalning], thema: Thema) -> Figure:
    """Teiknar stöplaritið fyrir eitt þema. Kalla verður í það innan ``thema_samhengi``."""
    if not dagatalning:
        raise SkjalftaVilla("Dagatalningin er tóm; ekkert myndrit verður til úr engu.")

    mynd = myndrit.nytt_myndrit()
    asar = mynd.add_subplot()
    stadir = range(len(dagatalning))
    fjoldi = [dagur.event_count for dagur in dagatalning]

    sulur = [(x, n) for x, n in zip(stadir, fjoldi) if n > 0]
    nulldagar = [x for x, n in zip(stadir, fjoldi) if n == 0]

    asar.set_yscale("log", base=LOG_GRUNNUR)
    asar.bar(
        [x for x, _ in sulur],
        [n - NEDRA_MARK for _, n in sulur],
        bottom=NEDRA_MARK,
        width=SULUBREIDD,
        color=thema.litur(hlutverk.FLOTUR),
        label=SKYRING_SULA,
    )
    asar.plot(
        nulldagar,
        [NULL_HAED] * len(nulldagar),
        linestyle="none",
        marker=NULL_MERKI,
        markersize=NULL_STAERD,
        markerfacecolor="none",
        markeredgewidth=NULL_LINA,
        markeredgecolor=thema.litur(hlutverk.NULL),
        label=SKYRING_NULL,
        gid=MERKI_NULL,
    )

    asar.set_ylim(NEDRA_MARK, max(fjoldi) * EFRA_RYMI)
    asar.set_xlim(-SULUBREIDD, len(dagatalning) - 1 + SULUBREIDD)
    asar.yaxis.set_major_locator(LogLocator(base=LOG_GRUNNUR))
    asar.yaxis.set_major_formatter(FuncFormatter(lambda gildi, _: islensk_tala(gildi)))
    asar.yaxis.set_minor_formatter(NullFormatter())
    asar.grid(axis="y")

    merktir = [x for x, d in zip(stadir, dagatalning) if d.utc_day[-2:] in MERKTIR_DAGAR]
    asar.xaxis.set_major_locator(FixedLocator(merktir))
    asar.set_xticklabels([islensk_dagsetning(dagatalning[x].utc_day) for x in merktir])

    fyrsti, sidasti = dagatalning[0].utc_day, dagatalning[-1].utc_day
    asar.set_title(
        TITILL.format(
            fra=islensk_dagsetning(fyrsti),
            til=islensk_dagsetning(sidasti, med_ari=True),
        )
    )
    asar.set_ylabel(Y_TEXTI)
    asar.set_xlabel(X_TEXTI)
    # Súlan fyrst í skýringunni: hún er gagnið, hringurinn undantekningin.
    handfong, heiti = asar.get_legend_handles_labels()
    rod = [heiti.index(SKYRING_SULA), heiti.index(SKYRING_NULL)]
    asar.legend([handfong[i] for i in rod], [heiti[i] for i in rod], loc="upper right")

    # supxlabel en ekki mynd.text: constrained-uppsetningin tekur frá pláss fyrir
    # supxlabel, en venjulegur texti skarast við x-ástextann.
    mynd.supxlabel(
        heimildarlina(dagatalning),
        x=HEIMILD_X,
        ha="left",
        color=thema.litur(hlutverk.TEXTI_DAUFT),
        fontsize=myndrit.rem_i_px(thema.texti("--texti-xs")),
    )
    return mynd


def heimildarlina(dagatalning: list[DagsTalning]) -> str:
    """Heimild og lykiltölur úrtaksins, allar reiknaðar úr dagatalningunni."""
    null = dagar_an_atburda(dagatalning)
    return HEIMILD.format(
        atburdir=islensk_tala(sum(d.event_count for d in dagatalning)),
        dagar=islensk_tala(len(dagatalning)),
        null=islensk_tala(null),
        hlutfall=islensk_prosenta(null, len(dagatalning)),
    )


def teikna_svg(dagatalning: list[DagsTalning], thema: Thema) -> bytes:
    """Byggir og skrifar myndritið fyrir eitt þema sem SVG-bæti."""
    with myndrit.thema_samhengi(thema):
        return myndrit.svg_baeti(byggja_mynd(dagatalning, thema))


def skrifa(mappa: Path = myndrit.MYNDAMAPPA) -> dict[str, Path]:
    """Les frosnu hrágögnin og tokens, teiknar bæði þemu og skilar slóðunum."""
    afmorkun = lesa_afmorkun()
    dagatalning = dagleg_talning(lesa_skjalfta(None, afmorkun), afmorkun)
    themu = lesa_tokens()

    fallnar = hlutverk.fallnar(themu)
    if fallnar:
        raise TokenVilla(
            "Litir myndritsins standast ekki andstæðukröfuna (regla 3.3):\n"
            + "\n".join(m.lina() for m in fallnar)
        )

    slodir = {}
    for heiti, skraarheiti in SKRAARHEITI.items():
        slod = myndrit.vista(teikna_svg(dagatalning, themu[heiti]), mappa / skraarheiti)
        log.info("Skrifaði %s (%d bæti)", slod, slod.stat().st_size)
        slodir[heiti] = slod
    return slodir


def main() -> int:
    """Inngangur fyrir ``python -m``; skilar 1 með skýringu ef eitthvað bregst."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        skrifa()
    except (SkjalftaVilla, TokenVilla, OSError) as villa:
        log.error("Myndritið varð ekki til: %s", villa)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
