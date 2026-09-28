"""Gervieintök fyrir mbl-prófin — tilbúið HTML, aldrei hrágögnin sjálf.

Frosna eintakið í ``data/raw/mbl/`` er **eina afritið sem til er** og því
aðeins lesið, aldrei skrifað (regla 10). Prófin sem þurfa að prófa jaðartilvik
— týnt mynstur, tvíræða niðurstöðu, tvö eintök í sömu töflu — smíða því sín
eigin gervieintök hér.

Gervi-HTML-ið hermir aðeins eftir þeim brotum sem mynstrin fimm leita að. Það
er ekki afrit af mbl.is og inniheldur engan fréttatexta.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Tvöföld fréttaslóð og tvöfalt auglýsingaauðkenni eru viljandi: þannig prófast
# afritahreinsunin, ekki bara talningin.
GERVI_HTML = """<!DOCTYPE html>
<html lang="is"><head><title>Hausinn telst ekki með</title>
<script>var leyniord = "ekki synilegt";</script>
<style>.falid { display: none; }</style></head>
<body>
<nav><a href="/frettir/">Fréttir</a><a href="/frettir/innlent/">Innlent</a></nav>
<a href="/frettir/innlent/2026/09/16/fyrsta_frettin/"><img alt="mynd"></a>
<a href="/frettir/innlent/2026/09/16/fyrsta_frettin/">Fyrsta fréttin</a>
<a href="https://www.mbl.is/frettir/erlent/2026/09/16/onnur_frett/">Önnur frétt</a>
<select>
<option value="1">Akureyri</option>
<option value="2" selected>Reykjavík</option>
</select>
<div class="vedur"><span class="value">11</span><span class="unit">&deg;</span></div>
<p>Sýnilegur texti með&nbsp;íslenskum stöfum.</p>
<!-- athugasemd sem telst ekki -->
<script>arrCurrency[3] = new MakeItem("USD", "121.33");</script>
<script>
Ads.renderSlot("1234-5678", {});
Ads.renderSlot("1234-5678", {});
Ads.renderSlot("9999-1", {});
</script>
</body></html>
"""

# Það sem GERVI_HTML á að gefa. Fast hér svo prófin lýsi væntingunni á einum stað.
GERVI_SVOR: dict[str, float] = {
    "einstakar-frettir": 2.0,
    "hitastig-reykjavik": 11.0,
    "gengi-usd": 121.33,
    "synileg-ord": 13.0,
    "auglysingareitir": 2.0,
}

GERVI_UPPRUNASLOD = "https://www.mbl.is/frettir/"


def iso_stund(stund: str) -> str:
    """Breytir ``20260916T120851Z`` í ``2026-09-16T12:08:51Z``."""
    dagur, klukka = stund.split("T")
    ar, manudur, dagsetning = dagur[:4], dagur[4:6], dagur[6:8]
    klst, minuta, sekunda = klukka[:2], klukka[2:4], klukka[4:6]
    return f"{ar}-{manudur}-{dagsetning}T{klst}:{minuta}:{sekunda}Z"


def skrifa_eintak(
    mappa: Path,
    sotta_stund: str,
    html_texti: str = GERVI_HTML,
    *,
    stada: int = 200,
    md5: str | None = None,
    staerd: int | None = None,
) -> Path:
    """Skrifar gervieintak — HTML og samnefnd lýsigögn — og skilar HTML-slóðinni.

    ``sotta_stund`` er á forminu ``20260916T120851Z`` og ræður skráarheitinu.
    ``md5``, ``staerd`` og ``stada`` má setja vísvitandi röng til að prófa að
    sannreyningin í ``mbl_eintak`` stöðvi keyrslu (regla 6).
    """
    mappa.mkdir(parents=True, exist_ok=True)
    html_slod = mappa / f"mbl-{sotta_stund}.html"
    baeti = html_texti.encode("utf-8")
    html_slod.write_bytes(baeti)

    lysigogn = {
        "schema_version": 1,
        "source_url": GERVI_UPPRUNASLOD,
        "fetched_at_utc": iso_stund(sotta_stund),
        "status_code": stada,
        "content_type": "text/html; charset=UTF-8",
        "content_length_bytes": len(baeti) if staerd is None else staerd,
        "md5": hashlib.md5(baeti).hexdigest() if md5 is None else md5,
        "user_agent": "prófun",
    }
    html_slod.with_suffix(".json").write_text(
        json.dumps(lysigogn, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return html_slod
