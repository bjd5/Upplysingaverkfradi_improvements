"""Úttak veðurstöðvamatsins í ``data/processed/`` (issue #14, pakki P2.4).

Gamla skriftan ``src/vedurstofa_stodvar.py`` skrifaði fjórar skrár í
``site/_generated/``: Markdown-töflu, Markdown-svör, Markdown-niðurstöðu og
SVG-súlurit, allt með tölunum límdum inn í texta. **Ekkert af því er flutt.**
HTML og myndrit verða til í ``web/`` (regla 2) og tölur fara í vefinn um
grunninn og útflutningslagið (kafli 0).

Það sem er flutt eru **tölurnar** sem þessar skrár báru, sem ein afleidd skrá:

* ``mat.json`` — matið úr ``vedurstodvar_mat``: stöðvarnar í kassanum raðaðar
  eftir fjarlægð (gögn súluritsins), valda stöðin, næsta aflagða stöð og
  munurinn, hlutfall virkra og 50 ára spurningin.

Skráin er **hrein afleiða frosna eintaksins**: hún ber sóknartíma og SHA-256
úr provenance en engan keyrslutíma, svo tvær keyrslur á sömu gögnum gefa sömu
bæti (lærdómurinn af issue #47). Vinnslan skrifar aldrei í ``web/gogn/``.

Keyrsla án nets, með eigin inngangi (tengingin við ``src/python/main.py`` er
issue #39)::

    PYTHONPATH=src/python python3 -m vinnsla.vedurstodvar_uttak

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from gagnagrunnur.tenging import ROT

from .vedurstodvar_hledsla import FROSID, lesa_eintak, stutt_slod
from .vedurstodvar_mat import Mat, MatVilla, StodIFjarlaegd, meta
from .vedurstodvar_samanburdur import VR_II_HEIMILD

log = logging.getLogger(__name__)

UNNID = ROT / "data" / "processed" / "vedurstodvar"
VEFGOGN = ROT / "web" / "gogn"
MATSKRA = "mat.json"


def _stod(stod: StodIFjarlaegd | None) -> dict | None:
    """Stöð sem JSON-hlutur. Óúnnaða ``km`` fer ekki út — síðan birtir metra."""
    if stod is None:
        return None
    gildi = asdict(stod)
    del gildi["km"]
    gildi["er_virk"] = stod.er_virk
    return gildi


def mat_sem_skjal(mat: Mat, provenance: dict, eintak: Path) -> dict:
    """Setur matið saman í JSON-skjal með uppruna svo hver tala sé rekjanleg (regla 8)."""
    return {
        "uppruni": {
            "eintak": stutt_slod(eintak),
            "sott_utc": str(provenance["fetched_at_utc"]),
            "sha256": str(provenance["sha256"]),
        },
        "vidmidunarpunktur": {
            "breidd": mat.breidd,
            "lengd": mat.lengd,
            "heimild": VR_II_HEIMILD,
            "radius_km": mat.radius_km,
            "kassi": list(mat.kassi),
        },
        "fjoldi_allra": mat.fjoldi_allra,
        "fjoldi_virkra": mat.fjoldi_virkra,
        "hlutfall_virkra_prosent": mat.hlutfall_virkra_prosent,
        "naesta": _stod(mat.naesta),
        "valin": _stod(mat.valin),
        "naesta_aflogd": _stod(mat.naesta_aflogd),
        "munur_metrar": mat.munur_metrar,
        "vidmidunarar": mat.vidmidunarar,
        "valin_naer_aftur": mat.valin_naer_aftur,
        "langtimastod": _stod(mat.langtimastod),
        "naestu": [_stod(stod) for stod in mat.naestu],
    }


def krefjast_utan_vefs(mappa: Path) -> None:
    """Stöðvar skrif inn í ``web/gogn/`` eða undirmöppu hennar.

    Vinnslan á aldrei að skrifa í birtingarlagið (kafli 0). Rétt sjálfgefin
    slóð á ekki að vera eina vörnin.
    """
    rett = mappa.resolve()
    if rett == VEFGOGN or VEFGOGN in rett.parents:
        raise MatVilla(
            f"Vinnslan skrifar ekki í {VEFGOGN}. Þangað fer aðeins JSON frá "
            "útflutningslaginu eftir að grunnurinn hefur verið byggður (kafli 0)."
        )


def vinna_vedurstodvar(
    frosid: Path = FROSID, mappa: Path | str | None = None
) -> tuple[Path, Mat]:
    """Les frosna eintakið, metur það og skrifar ``mat.json``.

    Eintakið er lesið gegnum ``vedurstodvar_hledsla.lesa_eintak``, sem staðfestir
    SHA-256 og sannreynir hverja færslu, svo matið og grunnurinn byggja á sama
    sannreynda inntakinu. Bregðist eitthvað fellur villa og engin hálfunnin
    skrá verður til.
    """
    mappa = Path(mappa) if mappa is not None else UNNID
    krefjast_utan_vefs(mappa)

    provenance, eintak, stodvar = lesa_eintak(frosid)
    mat = meta(stodvar)

    slod = mappa / MATSKRA
    slod.parent.mkdir(parents=True, exist_ok=True)
    texti = json.dumps(
        mat_sem_skjal(mat, provenance, eintak), ensure_ascii=False, indent=2, sort_keys=True
    )
    slod.write_text(texti + "\n", encoding="utf-8")
    return slod, mat


def main(rok: list[str] | None = None) -> int:
    """Keyrir matið á frosna eintakinu og prentar helstu tölurnar."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
    if rok:
        raise SystemExit(f"Þessi eining tekur enga viðbótarröksemd, fékk: {rok}")

    slod, mat = vinna_vedurstodvar()
    log.info(
        "Valin stöð %s (%d), %d m; %d af %d stöðvum virkar (%d %%). Skrifaði %s.",
        mat.valin.name,
        mat.valin.station_id,
        mat.valin.metrar,
        mat.fjoldi_virkra,
        mat.fjoldi_allra,
        mat.hlutfall_virkra_prosent,
        stutt_slod(slod),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
