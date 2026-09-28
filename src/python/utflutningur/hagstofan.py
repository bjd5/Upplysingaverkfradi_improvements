"""``web/gogn/hagstofan.json`` — brautskráning af háskólastigi (issue #21).

Allt kemur úr grunninum gegnum ``src/sql/queries/``: taflan og sóknartíminn
(``hagstofan-gagnasafn``), beiðnin sjálf — ``query.json`` sem var sent með
``POST`` (``gagnasofnun-skraning``, reiturinn ``params``) — og tölurnar
(``hagstofan-hlutfoll``, ``-summur``, ``-munur``).

**Leyfið er ekki til sem gögn.** Provenance safnsins skráir ekkert leyfi og
skilmálar Hagstofunnar voru ekki lesnir (``docs/heimildir.md`` kafli 5, opin
spurning 1). Heimildin segir það berum orðum í stað þess að giska.

Námundun: einn aukastafur, eins og gamla síðan birti prósenturnar og
prósentustigin.

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

import json
from sqlite3 import Connection

from gagnagrunnur import fyrirspurnir

from .skjal import Uppruni, UtflutningsVilla, ein_rod, namunda, skjal

SKRA = "hagstofan.json"
SIDA = "web/sidur/hagstofan.html"
THJONUSTA = "Hagstofa Íslands (PxWeb)"  # fetch_log.service, sama og vinnsla.hagstofan
LEYFI_OSTADFEST = "leyfi óstaðfest"
AUKASTAFIR = 1

# Mismunirnir sem æfingin spyr um: (lýsing, stöðukóði, svið A, kyn A, svið B, kyn B).
# Þetta eru SPURNINGAR æfingarinnar, ekki gögn — svörin koma úr hagstofan-munur.
BRAUTSKRADIR = "5"
MISMUNIR = (
    ("Brautskráðir: verkfræði á móti öllum sviðum", BRAUTSKRADIR, "07", "Alls", "Alls", "Alls"),
    ("Brautskráðir í verkfræði: konur á móti körlum", BRAUTSKRADIR, "07", "2", "07", "1"),
    ("Brautskráðir á öllum sviðum: konur á móti körlum", BRAUTSKRADIR, "Alls", "2", "Alls", "1"),
)

FYRIRSPURNIR = (
    "hagstofan-gagnasafn",
    "gagnasofnun-skraning",
    "hagstofan-hlutfoll",
    "hagstofan-summur",
    "hagstofan-munur",
)


def _hlutfoll(samband: Connection, tafla: str) -> list[dict]:
    return [
        {
            "svid_kodi": rad["field_code"],
            "svid": rad["field_label"],
            "kyn_kodi": rad["sex_code"],
            "kyn": rad["sex_label"],
            "stada_kodi": rad["student_status_code"],
            "stada": rad["student_status_label"],
            "hlutfall": namunda(rad["percentage"], AUKASTAFIR),
        }
        for rad in fyrirspurnir.keyra(samband, "hagstofan-hlutfoll", (tafla,))
    ]


def _summur(samband: Connection, tafla: str) -> list[dict]:
    return [
        {
            "svid_kodi": rad["field_code"],
            "svid": rad["field_label"],
            "kyn_kodi": rad["sex_code"],
            "kyn": rad["sex_label"],
            "summa": namunda(rad["percentage_sum"], AUKASTAFIR),
        }
        for rad in fyrirspurnir.keyra(samband, "hagstofan-summur", (tafla,))
    ]


def _mismunir(samband: Connection, tafla: str) -> list[dict]:
    ut = []
    for lysing, stada, svid_a, kyn_a, svid_b, kyn_b in MISMUNIR:
        rad = ein_rod(
            fyrirspurnir.keyra(
                samband, "hagstofan-munur", (tafla, stada, svid_a, kyn_a, svid_b, kyn_b)
            ),
            lysing,
        )
        ut.append({
            "lysing": lysing,
            "stada_kodi": stada,
            "hopur_a": {"svid_kodi": svid_a, "kyn_kodi": kyn_a},
            "hopur_b": {"svid_kodi": svid_b, "kyn_kodi": kyn_b},
            "prosentustig": namunda(rad["difference_pp"], AUKASTAFIR),
        })
    return ut


def byggja(samband: Connection) -> dict:
    """Skráin sem Hagstofusíðan les: beiðnin, hlutföllin, summurnar og mismunirnir."""
    tafla = ein_rod(fyrirspurnir.keyra(samband, "hagstofan-gagnasafn"), "Hagstofutafla")
    skraning = ein_rod(
        fyrirspurnir.keyra(samband, "gagnasofnun-skraning", (THJONUSTA,)), THJONUSTA
    )
    if skraning["endpoint"] != tafla["endpoint"]:
        raise UtflutningsVilla(
            f"fetch_log og hagstofan_datasets nefna ólíkar slóðir: "
            f"{skraning['endpoint']} / {tafla['endpoint']}"
        )
    uppruni = Uppruni(
        thjonusta=THJONUSTA.split(" (")[0],
        slod=str(tafla["endpoint"]),
        leyfi=LEYFI_OSTADFEST,
        sott=str(tafla["fetched_at"]),
        hragogn=str(tafla["raw_file"]),
    )
    try:
        beidni = json.loads(skraning["params"])
    except (TypeError, json.JSONDecodeError) as villa:
        raise UtflutningsVilla(f"Beiðnin í fetch_log er ekki gilt JSON: {villa}") from villa
    gogn = {
        "uppruni": {
            **uppruni.sem_gogn(),
            "tafla": tafla["id"],
            "titill": tafla["label"],
            "frumheimild": tafla["source"],
            "snid": f"json-stat {tafla['jsonstat_version']}",
            "fjoldi_gilda": tafla["value_count"],
            "beidni": beidni,
        },
        "hlutfoll": _hlutfoll(samband, tafla["id"]),
        "summur": _summur(samband, tafla["id"]),
        "mismunir": _mismunir(samband, tafla["id"]),
    }
    return skjal(uppruni, gogn)
