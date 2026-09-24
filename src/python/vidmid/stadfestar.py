"""Tölur sem eru þegar staðfestar og VERÐA að koma fram í viðmiðinu.

Verklýsing P0.2 telur þessar tölur upp; þær eru sóttar úr _meta.json og
provenance-skránum sem P0.1 fryssti. Hér eru þær skráðar sem gögn svo
tolur.py geti sannreynt að viðmiðið hitti þær — og svo P2.8 geti gert það sama
án þess að lesa verklýsingu.

`leid` er slóð inn í _meta.json (punktaskilin), eða None fyrir tölur sem koma
annars staðar. `i_html` segir hvort talan stendur sem texti í byggðu síðunni:
er hún False þá birtir gamla síðan hana með útreikningi í vafra og HTML-lestur
einn nær henni ekki.
"""

from __future__ import annotations

from typing import NamedTuple

META = "friends/phoebe-stats/_meta.json"
SKJALFTAR = "capstone/earthquakes.html"
PHOEBE = "friends/phoebe-statistics.html"


class Stadfest(NamedTuple):
    heiti: str
    gildi: float | int
    eining: str | None
    sida: str
    leid: str | None      # slóð inn í _meta.json, ef talan kemur þaðan
    i_html: bool          # stendur talan sem texti í HTML-inu?


STADFESTAR: tuple[Stadfest, ...] = (
    Stadfest("jarðskjálftar", 334, "atburðir", SKJALFTAR, None, True),
    Stadfest("dagar í glugganum", 61, "dagar", SKJALFTAR, None, True),
    Stadfest("handritsskrár", 227, "skrár", PHOEBE,
             "transcript_files_used", True),
    Stadfest("þættir", 236, "þættir", PHOEBE,
             "aired_episodes_covered", True),
    Stadfest("textablokkir alls", 70553, "textablokkir", PHOEBE,
             "parse_quality.total_text_blocks", True),
    Stadfest("tilsvör", 61161, "tilsvör", PHOEBE,
             "parse_quality.speaker_lines", True),
    Stadfest("sviðsfyrirsagnir", 4055, "sviðsfyrirsagnir", PHOEBE,
             "parse_quality.scene_headings", False),
    Stadfest("sviðsleiðbeiningar", 3259, "sviðsleiðbeiningar", PHOEBE,
             "parse_quality.stage_directions", False),
    Stadfest("óflokkað", 2078, "textablokkir", PHOEBE,
             "parse_quality.unclassified", True),
    Stadfest("óflokkað hlutfall", 2.95, "%", PHOEBE,
             "parse_quality.unclassified_pct", True),
    Stadfest("línur Phoebe", 7483, "línur", PHOEBE,
             "friends_line_totals.phoebe", False),
    Stadfest("línur Rachel", 9259, "línur", PHOEBE,
             "friends_line_totals.rachel", False),
    Stadfest("línur Ross", 9058, "línur", PHOEBE,
             "friends_line_totals.ross", False),
    Stadfest("línur Chandler", 8446, "línur", PHOEBE,
             "friends_line_totals.chandler", False),
    Stadfest("línur Monica", 8395, "línur", PHOEBE,
             "friends_line_totals.monica", False),
    Stadfest("línur Joey", 8183, "línur", PHOEBE,
             "friends_line_totals.joey", False),
)

# Síður sem reikna tölurnar sínar í vafra lesandans og birta þær því hvergi í
# HTML-textanum. Fyrir þær er gagnaskráin viðmiðið, ekki síðan.
GAGNADRIFNAR = (
    {
        "sida": PHOEBE,
        "hattur": "observable-js",
        "gagnaskrar": (
            "friends/phoebe-stats/_meta.json",
            "friends/phoebe-stats/phoebe-extra-stats.json",
            "friends/phoebe-stats/phoebe-top-talkers.json",
            "friends/phoebe-stats/phoebe-screentime-by-season.json",
            "friends/phoebe-stats/phoebe-mentions-by-season.json",
            "friends/phoebe-stats/phoebe-per-episode.csv",
            "friends/phoebe-stats/phoebe-distinctive-words.csv",
        ),
        "skyring": (
            "Myndrit og töflur eru byggð með Observable Plot í vafranum úr "
            "þessum sjö skrám. Tölurnar sem lesandinn sér standa hvergi í "
            "HTML-inu; þar er aðeins OJS-kóðinn sem reiknar þær."
        ),
    },
    {
        "sida": "tokens/index.html",
        "hattur": "innbakað-csv",
        "gagnaskrar": ('<script type="text/plain" id="tk-gogn"> (innbakað CSV)',),
        "skyring": (
            "Teljararnir eru summaðir í JavaScript úr CSV sem Quarto bakaði "
            "inn í skjalið á byggingartíma. Engin tala á síðunni stendur í "
            "HTML-textanum."
        ),
    },
)
