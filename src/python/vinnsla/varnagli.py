"""Varnagli: vinnslan skrifar aldrei í ``web/gogn/`` (kafli 0 í CLAUDE.md).

Flæðið er einstefna. Vinnslan skrifar afleiddar töflur í ``data/processed/``;
``web/gogn/`` fær aðeins JSON frá útflutningslaginu eftir að grunnurinn hefur
verið byggður. Hver vinnsla sem skrifar á disk kallar í
:func:`krefjast_utan_vefs` áður en nokkuð verður til. Rétt sjálfgefin slóð á
ekki að vera eina vörnin: mappa úr röksemd getur bent hvert sem er.

Möppur eru bornar saman eftir ``resolve()``, ekki sem strengir:
``web/gogn-annad`` er ekki ``web/gogn``, en ``data/../web/gogn`` er það.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from pathlib import Path

from gagnagrunnur.tenging import ROT

VEFGOGN = ROT / "web" / "gogn"


def krefjast_utan_vefs(mappa: Path | str, villa: type[Exception] = ValueError) -> None:
    """Stöðvar skrif í ``web/gogn/`` eða undirmöppu hennar.

    ``villa`` er villuklasi kallandans (t.d. ``SkjalftaVilla``), svo hver
    vinnsla falli með sinni eigin villu og ``keyrsla.urvinnsla`` grípi hana.
    """
    rett = Path(mappa).resolve()
    vefgogn = VEFGOGN.resolve()
    if rett == vefgogn or vefgogn in rett.parents:
        raise villa(
            f"Vinnslan skrifar ekki í {VEFGOGN}. Þangað fer aðeins JSON frá "
            "útflutningslaginu eftir að grunnurinn hefur verið byggður (kafli 0)."
        )
