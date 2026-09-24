"""Frystir söfnin sem ÞEGAR eru vistuð í upprunaverkefninu — afritun, ekki söfnun.

Jarðskjálftagögnin og Hagstofugögnin voru vistuð með provenance í gamla
verkefninu og komust í git þar. Þau þurfa því ekki nýja söfnun; þau þurfa að
komast hingað **óbreytt**, svo endurbyggingin sé möguleg án nets (regla 4).

Afritið er sannreynt gegn provenance sem fylgdi safninu: SHA-256 hverrar skráar
er reiknað upp á nýtt og borið saman við summuna sem upprunaverkefnið skráði
þegar það sótti gögnin. Stemmi hún sannar það tvennt í einu — að afritið sé
ósnert og að frumgagnið hafi ekki breyst síðan það var sótt.

Keyrsla frá rót verkefnisins::

    python3 src/python/sofnun/frysta_afrit.py
    python3 src/python/sofnun/frysta_afrit.py --uppruni /önnur/slóð/data/raw

Engir nýir pakkar — eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:  # keyrt beint: python3 src/python/sofnun/frysta_afrit.py
    from frysting import (
        HRAGOGN, ROT, lesa_frystingu, log, lysa_skrar, nuna_utc, skra_safn, vaentar_summur,
    )
except ImportError:  # flutt inn sem eining innan pakkans
    from .frysting import (
        HRAGOGN, ROT, lesa_frystingu, log, lysa_skrar, nuna_utc, skra_safn, vaentar_summur,
    )

# Upprunaverkefnið. Slóðin er skráð með ~ í provenance: repo-ið er opið og full
# slóð segir ekkert umfram þetta (sama venja og í src/python/vidmid/sofn.py).
SJALFGEFINN_UPPRUNI = Path("~/PycharmProjects/idn302g-2026-team-friends-thesveinn/data/raw")
UPPRUNAREPO = "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe"

SOFN = (
    {
        "heiti": "vedur-quakes",
        "mappa": "data/raw/vedur-quakes",
        "skyring": (
            "334 yfirfarnir SIL-jarðskjálftar á Reykjanesi 1.11.2023–1.1.2024, "
            "stærð 3–7 og dýpt 0–50 km. Hráa svarið frá api.vedur.is/quakes/events "
            "með provenance. Leyfi: CC BY 4.0."
        ),
        "les_skrifta": "src/python/vinnsla/ (P1.2, issue #6)",
    },
    {
        "heiti": "hagstofan",
        "mappa": "data/raw/hagstofan",
        "skyring": (
            "Brautskráning af háskólastigi (json-stat2) úr SKO04208b.px: "
            "innritunarár 2017, tímapunkturinn n+3. Fjórar skrár — lýsigögn, "
            "fyrirspurn, svar og provenance."
        ),
        "les_skrifta": "src/python/vinnsla/ (P1.3, issue #7)",
    },
)


def upprunaslod(slod: Path) -> str:
    """Slóð með ``~`` fyrir heimamöppuna — repo-ið er opið og full slóð bætir engu við."""
    slod = slod.expanduser()
    return (
        f"~/{slod.relative_to(Path.home()).as_posix()}"
        if slod.is_relative_to(Path.home())
        else slod.as_posix()
    )


def fyrra_frosid(heiti: str) -> str:
    """Skilar frystingartíma safns úr ``frysting.json``, eða núinu sé hann óskráður."""
    fyrra = lesa_frystingu()["sofn"].get(heiti, {})
    return fyrra.get("frosid_utc", nuna_utc())


def afrita_safn(safn: dict, upprunarot: Path) -> dict:
    """Afritar eitt safn óbreytt og skilar frystingarfærslunni fyrir það.

    ``shutil.copy2`` varðveitir breytingartíma eins og ``cp -p`` — tímastimpill
    upprunaskráarinnar er sjálfstæð vísbending um hvenær gagnið varð til og má
    ekki tapast í afrituninni.
    """
    til = ROT / safn["mappa"]
    thegar_fryst = til.is_dir() and any(til.iterdir())

    if thegar_fryst:
        # Regla 4: safn sem er þegar fryst er hvorki sótt né afritað upp á nýtt.
        # Það er samt sannreynt hér að neðan — þögult „sleppt" segir ekkert um
        # hvort gagnið sé enn ósnert.
        log.info("%s er þegar fryst — afrita ekki, sannreyni í staðinn.", safn["mappa"])
    else:
        fra = (upprunarot / safn["heiti"]).expanduser()
        if not fra.is_dir():
            raise FileNotFoundError(
                f"Finn ekki upprunamöppuna {fra}. Sé upprunaverkefnið annars staðar: "
                "keyrðu með --uppruni."
            )
        til.mkdir(parents=True, exist_ok=True)
        for skra in sorted(fra.rglob("*")):
            if skra.is_dir() or skra.name.startswith("."):
                continue
            afangastadur = til / skra.relative_to(fra)
            afangastadur.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skra, afangastadur)

    # Provenance upprunaverkefnisins fylgdi með afritinu; það er heimildin um
    # hvaða summur eiga að koma út.
    skrar = lysa_skrar(til, vaentar_summur(til))
    sannreyndar = sum(1 for skra in skrar if skra["stadfest_vid_provenance"])
    log.info(
        "%s: %d skrár, %.1f kB — %d sannreyndar gegn provenance",
        safn["mappa"],
        len(skrar),
        sum(skra["staerd_baet"] for skra in skrar) / 1000,
        sannreyndar,
    )

    return {
        "heiti": safn["heiti"],
        "mappa": safn["mappa"],
        "adferd": "afrit",
        "skyring": safn["skyring"],
        "les_skrifta": safn["les_skrifta"],
        "uppruni": upprunaslod(upprunarot / safn["heiti"]),
        "upprunarepo": UPPRUNAREPO,
        # Tíminn sem safnið var fryst, ekki tíminn sem það var síðast sannreynt.
        "frosid_utc": fyrra_frosid(safn["heiti"]) if thegar_fryst else nuna_utc(),
        "fjoldi_skraa": len(skrar),
        "staerd_baet": sum(skra["staerd_baet"] for skra in skrar),
        "fjoldi_sannreyndra": sannreyndar,
        "skrar": skrar,
    }


def frysta(upprunarot: Path = SJALFGEFINN_UPPRUNI) -> int:
    """Afritar öll söfn í ``SOFN`` og skráir þau í ``data/raw/frysting.json``."""
    HRAGOGN.mkdir(parents=True, exist_ok=True)
    for safn in SOFN:
        skra_safn(afrita_safn(safn, upprunarot))
    return 0


def main(rok: list[str] | None = None) -> int:
    thattari = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    thattari.add_argument(
        "--uppruni",
        type=Path,
        default=SJALFGEFINN_UPPRUNI,
        help=f"data/raw í upprunaverkefninu (sjálfgefið: {SJALFGEFINN_UPPRUNI})",
    )
    return frysta(thattari.parse_args(rok).uppruni)


if __name__ == "__main__":
    sys.exit(main())
