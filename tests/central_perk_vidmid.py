"""Samanburður Central Perk-úttaksins við frosna viðmiðið (issue #14, P2.6).

Viðmiðið er ``docs/vidmid/generated/phoebe-central-perk-*`` — fjórar skrár
sem gamla skriftan (``src/phoebe_central_perk.py`` @ ``2865ed6``) skrifaði og
síðan birti. Það er **lesið**, aldrei afritað inn í prófin.

* ``-summary.json`` er borin saman **bæti fyrir bæti** (engin leyfð frávik).
* ``.svg`` ber hóp og hlutdeild Phoebe í hverju handriti (einn punktur á
  skrá, litur = hópur, ``<title>`` = auðkenni og hlutdeild með einum aukastaf);
  ``svg_points`` les þær út svo bera megi saman við ``-episodes.csv``.
* ``-regex.md`` er endurskapað úr ``-regex.json`` með sniði gömlu skriftunnar
  (``regex_markdown``) og borið saman staf fyrir staf.
* ``-summary.md`` er texti sem vefurinn tekur við (regla 2); tölurnar í honum
  eru allar í ``-summary.json``.

Hjálpareining, ekki prófskrá (``unittest discover`` leitar að ``test*.py``).
"""

from __future__ import annotations

import re

import hjalp  # noqa: F401  — setur src/python á sys.path
from hjalp import ROT

VIDMIDSMAPPA = ROT / "docs" / "vidmid" / "generated"
VIDMID_SUMMARY = VIDMIDSMAPPA / "phoebe-central-perk-summary.json"
VIDMID_SVG = VIDMIDSMAPPA / "phoebe-central-perk.svg"

# Litir hópanna í gömlu myndinni (GROUP_COLOURS í gömlu skriftunni).
SVG_GROUP_COLOURS = {
    "#64748B": "no_central_perk",
    "#0284C7": "central_perk",
    "#7C3AED": "phoebe_sings",
}
SVG_POINT_RE = re.compile(
    r'<circle [^>]*fill="(?P<colour>#[0-9A-F]{6})"[^>]*>'
    r"<title>(?P<episode>[^:<]+): (?P<share>[0-9]+\.[0-9])%</title></circle>"
)
SVG_DECIMALS = 1


def svg_points(svg: str | None = None) -> dict[str, tuple[str, str]]:
    """{handrit: (hópur, hlutdeild í % með einum aukastaf)} úr SVG-viðmiðinu."""
    texti = svg if svg is not None else VIDMID_SVG.read_text(encoding="utf-8")
    punktar = {}
    for m in SVG_POINT_RE.finditer(texti):
        if m["episode"] in punktar:
            raise AssertionError(f"{m['episode']} kemur tvisvar fyrir í SVG-viðmiðinu.")
        punktar[m["episode"]] = (SVG_GROUP_COLOURS[m["colour"]], m["share"])
    if not punktar:
        raise AssertionError("Engir punktar fundust í SVG-viðmiðinu — samanburður sannar ekkert.")
    return punktar


def csv_points(rows: list[dict[str, str]]) -> dict[str, tuple[str, str]]:
    """Sama form og ``svg_points`` úr röðum ``-episodes.csv``."""
    return {
        r["episode_id"]: (r["group"], f"{100 * float(r['phoebe_share']):.{SVG_DECIMALS}f}")
        for r in rows
    }


def regex_markdown(rows: list[dict[str, str]]) -> str:
    """Endurskapar ``-regex.md`` úr röðum ``-regex.json`` (snið ``write_regex_markdown``)."""
    lines: list[str] = []
    for row in rows:
        lines += [f"#### `{row['name']}`", "", "```python", row["pattern"], "```", "",
                  f"**Grípur:** {row['catches']}", "", f"**Sleppur:** {row['misses']}", ""]
    return "\n".join(lines)
