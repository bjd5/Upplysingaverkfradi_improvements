"""``web/gogn/yfirlit.json`` — hvaða gagnaskrár eru til og hvenær gögn þeirra eru frá.

Forsíðan les skrána með ``web/assets/js/stada-gagna.js``, sem er **óbreytt**:
það telur ``gogn`` sem lista („N færslur“), skeytir ``heimild`` inn í texta og
sýnir ``uppfaert`` sem dagsetningu. Umslagið er því það sama og annarra skráa
(``json_skrif``), og hver færsla í ``gogn`` er ein útflutt skrá:

    {"skra": "skjalftar.json", "sida": "sidur/skjalftavaktin.html",
     "uppfaert": "…", "heimild": "…"}

``uppfaert`` er nýjasti gagnastimpill skránna (sóknar- eða reiknitími), ekki
klukkan við útflutning; ``heimild`` er útgefendurnir, hver einu sinni, í röð
skránna. Yfirlitið er reiknað úr hinum umslögunum og les grunninn ekki sjálft.
"""

from __future__ import annotations

from typing import Any

from . import hagstofan_json, mbl_json, phoebe_json, skjalftar_json, vedurstodvar_json
from .json_skrif import UtflutningsVilla, byggja_umslag

SKRAARHEITI = "yfirlit.json"
SKIL = " — "

# Skráarheiti -> síðan sem les hana, afstætt frá web/.
SIDUR: dict[str, str] = {
    skjalftar_json.SKRAARHEITI: "sidur/skjalftavaktin.html",
    hagstofan_json.SKRAARHEITI: "sidur/hagstofan.html",
    vedurstodvar_json.SKRAARHEITI: "sidur/vedurstodvar.html",
    mbl_json.SKRAARHEITI: "sidur/mbl-regex.html",
    phoebe_json.SKRAARHEITI: "sidur/phoebe-tolfraedi.html",
}


def byggja(umslog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Yfirlit yfir umslögin, í röð þeirra; skrá án síðu er villa."""
    vantar = [heiti for heiti in umslog if heiti not in SIDUR]
    if vantar:
        raise UtflutningsVilla(f"Engin síða skráð fyrir {', '.join(vantar)} í yfirliti.")
    faerslur = [
        {"skra": heiti, "sida": SIDUR[heiti],
         "uppfaert": umslag["uppfaert"], "heimild": umslag["heimild"]}
        for heiti, umslag in umslog.items()
    ]
    if not faerslur:
        raise UtflutningsVilla("Ekkert að taka saman í yfirliti.")
    utgefendur = dict.fromkeys(f["heimild"].split(SKIL)[0] for f in faerslur)
    # Allir stimplar eru á sama UTC-sniði (json_skrif.utc_timastimpill): strengjaröð er tímaröð.
    return byggja_umslag(uppfaert=max(f["uppfaert"] for f in faerslur),
                         heimild=", ".join(utgefendur), gogn=faerslur)
