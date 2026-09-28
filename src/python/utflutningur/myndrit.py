"""Myndritalagið: matplotlib teiknar SVG í litum sjónræna kerfisins (issue #17).

Ákvörðunin 27.9.2026 (issue #17, valkostur A): Python teiknar myndritin sem SVG
við útflutning og síðan vísar í þau með ``<picture>``/``<img>``. Myndritið er
þá til þótt JavaScript sé slökkt (regla 3.4), og gagnatafla í HTML-inu ber
sömu tölur fyrir þá sem sjá ekki myndina (regla 3.3).

matplotlib er samþykkt **eingöngu** hér, í ``src/python/utflutningur/``. Allt
sem flytur inn þessa einingu þarfnast því pakkans; prófin á henni sleppa sér
þegar hann er ekki til, svo prófasafnið keyrir áfram á staðalsafninu einu.

Þrjár reglur sem lagið framfylgir, svo einstök myndrit þurfi ekki að muna þær:

* **Litir úr tokens.css.** Allir litir koma úr ``Thema`` sem ``lesa_tokens()``
  skilar. Hér er enginn litur skrifaður (regla 3.1).
* **Ákvarðað úttak.** Sama gögn og sömu tokens gefa sömu bæti: fast
  ``svg.hashsalt`` og engin ``Date`` í lýsigögnum. SVG sem breytist við hverja
  keyrslu lætur git halda að myndin sé ný — sama gildra og issue #47.
* **Ekkert innfellt letur.** ``svg.fonttype = "none"`` skrifar texta sem
  ``<text>`` í stað ferla. Skráin verður margfalt minni (regla 3.4), textinn er
  leitanlegur, og vafrinn teiknar hann með letri síðunnar.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ekkert gluggakerfi; aðeins skrár

from matplotlib import rc_context  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from . import myndrit_litir as hlutverk  # noqa: E402
from .tokens import Thema, TokenVilla  # noqa: E402

ROT = Path(__file__).resolve().parents[3]
MYNDAMAPPA = ROT / "web" / "assets" / "img"

# SVG-bakendi matplotlib teiknar á 72 punktum á tommu: 1 pt = 1 eining í viewBox.
PUNKTAR_A_TOMMU = 72
# Stærð myndritsins í viewBox-einingum. <img width/height> fær sömu tölur svo
# vafrinn taki frá plássið áður en myndin hleðst (engin útlitshliðrun).
BREIDD = 640
HAED = 360

# CSS rem er 16 px í sjálfgefnum vafra; tokens eru í rem en SVG í px.
PX_A_REM = 16
# Fast salt gefur sömu auðkenni (clip-path o.fl.) í hverri keyrslu.
HASHSALT = "upplysingaverkfradi-myndrit"
# Lýsigögn án ``Date``: dagsetning keyrslunnar er ekki eiginleiki myndarinnar.
LYSIGOGN = {"Date": None}
# matplotlib þarf letur á vélinni til að MÆLA texta við uppsetningu. Ekkert
# letranna í --letur-texti fylgir Linux, svo DejaVu Sans (fylgir matplotlib) er
# sett aftast. Vafrinn velur fyrst letur úr tokens; DejaVu er breiðara en þau,
# svo texti sem passar við mælinguna passar líka í vafranum.
MAELILETUR = "DejaVu Sans"
_ALMENN_FJOLSKYLDA = "sans-serif"


def rem_i_px(gildi: str) -> float:
    """Breytir ``0.9375rem`` eða ``1px`` úr tokens í px; annað snið er villa."""
    hreint = gildi.strip()
    try:
        if hreint.endswith("rem"):
            return float(hreint[: -len("rem")]) * PX_A_REM
        if hreint.endswith("px"):
            return float(hreint[: -len("px")])
    except ValueError as villa:
        raise TokenVilla(f"Gat ekki lesið stærðina {gildi!r} úr tokens.css.") from villa
    raise TokenVilla(
        f"Stærðin {gildi!r} er hvorki í rem né px; myndrit þurfa fasta stærð "
        "(clamp() og vw eiga við skjá, ekki mynd)."
    )


def leturfjolskyldur(thema: Thema) -> list[str]:
    """Skilar ``--letur-texti`` sem lista, án gæsalappa og almenna heitisins."""
    heiti = [hluti.strip().strip("\"'") for hluti in thema.texti("--letur-texti").split(",")]
    return [h for h in heiti if h and h != _ALMENN_FJOLSKYLDA] + [MAELILETUR]


def stillingar(thema: Thema) -> dict[str, object]:
    """Skilar rcParams matplotlib fyrir eitt þema — allt úr tokens.css."""
    bak = thema.litur(hlutverk.BAKGRUNNUR)
    texti = thema.litur(hlutverk.TEXTI)
    asar = thema.litur(hlutverk.AS)
    lina = rem_i_px(thema.texti("--rammi-breidd"))
    return {
        "svg.fonttype": "none",
        "svg.hashsalt": HASHSALT,
        "figure.facecolor": bak,
        "savefig.facecolor": bak,
        "axes.facecolor": bak,
        "axes.edgecolor": asar,
        "axes.linewidth": lina,
        "axes.labelcolor": texti,
        "axes.titlecolor": texti,
        "axes.titlelocation": "left",
        "axes.titlesize": rem_i_px(thema.texti("--texti-base")),
        "axes.titleweight": int(thema.texti("--thyngd-feit")),
        "axes.labelsize": rem_i_px(thema.texti("--texti-xs")),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.axisbelow": True,
        "grid.color": thema.litur(hlutverk.GRIND),
        "grid.linewidth": lina,
        "xtick.color": asar,
        "ytick.color": asar,
        "xtick.labelcolor": texti,
        "ytick.labelcolor": texti,
        "xtick.labelsize": rem_i_px(thema.texti("--texti-xs")),
        "ytick.labelsize": rem_i_px(thema.texti("--texti-xs")),
        "text.color": texti,
        "legend.frameon": False,
        "legend.labelcolor": texti,
        "legend.fontsize": rem_i_px(thema.texti("--texti-xs")),
        "font.family": [_ALMENN_FJOLSKYLDA],
        "font.sans-serif": leturfjolskyldur(thema),
        "font.size": rem_i_px(thema.texti("--texti-sm")),
    }


@contextmanager
def thema_samhengi(thema: Thema) -> Iterator[None]:
    """Setur stillingar þemans á meðan myndrit er byggt og vistað.

    matplotlib les rcParams bæði þegar hlutur verður til og þegar SVG er
    skrifað, svo hvort tveggja verður að gerast innan sama samhengis.
    """
    with rc_context(stillingar(thema)):
        yield


def nytt_myndrit() -> Figure:
    """Tómt myndrit í fastri stærð. Kalla verður í það innan ``thema_samhengi``."""
    return Figure(
        figsize=(BREIDD / PUNKTAR_A_TOMMU, HAED / PUNKTAR_A_TOMMU),
        dpi=PUNKTAR_A_TOMMU,
        layout="constrained",
    )


def svg_baeti(mynd: Figure) -> bytes:
    """Skrifar myndritið sem SVG í minni. Kalla verður í það innan ``thema_samhengi``."""
    buffer = io.BytesIO()
    mynd.savefig(buffer, format="svg", metadata=LYSIGOGN)
    return buffer.getvalue()


def vista(baeti: bytes, slod: Path) -> Path:
    """Skrifar SVG-bæti á disk og skilar slóðinni."""
    slod.parent.mkdir(parents=True, exist_ok=True)
    slod.write_bytes(baeti)
    return slod
