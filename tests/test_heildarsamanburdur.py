"""Samanburður frá enda til enda við gamla verkefnið (issue #16).

Pípan er keyrð eins og notandi keyrir hana — ``main.py --skref vinna``,
``hlada`` og ``flytja-ut``, hvert í sínu undirferli og án nets — á frosnu
gögnunum. Sex viðmiðunargildi issue-sins eru svo borin við gömlu síðuna á
þremur stigum: í úttaki vinnslunnar, í grunninum og í útfluttu JSON-skránum
sem síðan les.

Væntu tölurnar eru **lesnar úr** ``docs/vidmid/vidmid.json`` (``stadfestar``)
gegnum ``friends_grunnur.vidmid_gildi``, sem krefst nákvæmlega einnar
samsvörunar: ein tala, ein heimild. Engin þeirra er handskrifuð hér.

``safna`` er ekki keyrt: TMDB var aldrei fryst, og sé lykill í ``.env`` sækir
skrefið það af netinu og skrifar í ``data/raw/``. Grunnur og úttak fara í
tímabundna möppu; raunverulegu ``web/gogn/`` og ``data/processed/`` eru aðeins
lesnar, og það er prófað.

Samanburðurinn er líka prófaður þar sem hann á að **bresta** (kafli 6 í
``docs/agenta-verkefni.md``): hverju viðmiði er ruglað í minni, og afrit af
úttaki hvers stigs er skemmt — í báðum tilvikum verður rétti punkturinn að falla.

    PYTHON=python3.12 python3.12 -m unittest discover -s tests -p test_heildarsamanburdur.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from friends_grunnur import vidmid_gildi
from hjalp import PYTHON_ROT, ROT

from gagnagrunnur.tenging import UMHVERFISBREYTA as GRUNNBREYTA  # noqa: E402
from keyrsla.hledsla import SOFN  # noqa: E402
from utflutningur import phoebe_json, skjalftar_json  # noqa: E402
from utflutningur.flytja_ut import SKRAR  # noqa: E402
from vinnsla import jardskjalftar_uttak as skjalftauttak  # noqa: E402
from vinnsla.friends_handrit import TRANSCRIPT_DIR_ENV  # noqa: E402

BIDTIMI_SEK = 120
SKREF = ("vinna", "hlada", "flytja-ut")
VERNDADAR = (ROT / "web" / "gogn", ROT / "data" / "processed")

# Sex viðmiðunargildi issue #16, eftir heiti sínu í vidmid.json. Issue-ið segir
# „dagar í tímaröð“ og „línur greindar“; viðmiðið kallar sömu tölur „dagar í
# glugganum“ og „tilsvör“ (speaker_lines í phoebe-stats/_meta.json).
SEX_GILDI = ("jarðskjálftar", "dagar í glugganum", "handritsskrár", "þættir", "tilsvör",
             "óflokkað hlutfall")

# Hvaða gildi hvert stig ber. Vinnslan endurreiknar ekki Friends-tölurnar:
# handritin eru utan repo-sins (#3) og hleðslan les frosnu tölurnar. Endurreikn-
# ingurinn er borinn saman bæti fyrir bæti í test_phoebe_uttak.
STIG = {"vinnsla": SEX_GILDI[:2], "grunnur": SEX_GILDI, "útflutningur": SEX_GILDI}

# (heiti, fyrirspurn). unclassified_pct er sýn sem reiknar hlutfallið úr
# blokkafjöldanum (006_friends.sql) — talan er reiknuð, ekki afrituð.
GRUNNFYRIRSPURNIR = (
    ("jarðskjálftar", "SELECT COUNT(*) FROM earthquakes"),
    ("jarðskjálftar", "SELECT SUM(event_count) FROM earthquake_days"),
    ("dagar í glugganum", "SELECT COUNT(*) FROM earthquake_days"),
    ("handritsskrár", "SELECT COUNT(*) FROM friends_transcript_files"),
    ("þættir", "SELECT SUM(aired_episodes) FROM friends_transcript_files"),
    ("tilsvör", "SELECT speaker_lines FROM friends_parse_quality"),
    ("óflokkað hlutfall", "SELECT unclassified_pct FROM friends_parse_quality"),
)

# (heiti, skrá, slóð reitsins í umslaginu).
JSON_REITIR = (
    ("jarðskjálftar", skjalftar_json.SKRAARHEITI, ("lysigogn", "samantekt", "atburdir")),
    ("dagar í glugganum", skjalftar_json.SKRAARHEITI, ("lysigogn", "samantekt", "dagar")),
    ("handritsskrár", phoebe_json.SKRAARHEITI, ("lysigogn", "umfang", "handritsskrar")),
    ("þættir", phoebe_json.SKRAARHEITI, ("lysigogn", "umfang", "thaettir")),
    ("tilsvör", phoebe_json.SKRAARHEITI, ("lysigogn", "umfang", "thattunargaedi", "tilsvor")),
    ("óflokkað hlutfall", phoebe_json.SKRAARHEITI,
     ("lysigogn", "umfang", "thattunargaedi", "oflokkad_prosent")),
)

# main.py les grunninn úr umhverfisbreytu, en data/processed/ og web/gogn/ eru
# fastar í einingunni (GOGN_UNNIN, VEFGOGN). Undirferlið ræsir main eins og
# `python src/python/main.py` gerir (src/python fremst á sys.path), beinir
# föstunum tveimur í tímabundnu möppuna og kallar í main() með skipanalínunni.
RAESIR = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path[0] = sys.argv[1]\n"
    "import main\n"
    "main.GOGN_UNNIN, main.VEFGOGN = Path(sys.argv[2]), Path(sys.argv[3])\n"
    "sys.exit(main.main(sys.argv[4:]))\n"
)


@dataclass(frozen=True)
class Maelipunktur:
    """Ein tala úr pípunni: stig, hvaðan hún er lesin, og viðmiðið sem hún á að hitta."""

    stig: str
    heiti: str
    hvadan: str
    gildi: object


def frabrigdi(punktar: list[Maelipunktur], vaent: dict[str, object]) -> list[Maelipunktur]:
    """Mælipunktarnir sem víkja frá viðmiðinu."""
    return [p for p in punktar if p.gildi != vaent[p.heiti]]


def lysa(punktur: Maelipunktur, vaent: dict[str, object]) -> str:
    return (f"{punktur.hvadan} = {punktur.gildi!r}; viðmiðið "
            f"„{punktur.heiti}“ er {vaent[punktur.heiti]!r}")


def _fingrafar(moppur: tuple[Path, ...]) -> str:
    """SHA-256 yfir slóðir og bæti allra skráa í möppunum."""
    summa = hashlib.sha256()
    for mappa in moppur:
        for slod in sorted(p for p in mappa.rglob("*") if p.is_file()):
            summa.update(slod.relative_to(ROT).as_posix().encode())
            summa.update(slod.read_bytes())
    return summa.hexdigest()


def _csv_radir(slod: Path) -> int:
    with slod.open(encoding="utf-8", newline="") as skra:
        return sum(1 for _ in csv.DictReader(skra))


def _fletta(umslag: object, slod: tuple[str, ...]) -> object:
    """Reiturinn á ``slod``, eða ``None`` vanti hann — sem stemmir ekki við neitt viðmið."""
    for lykill in slod:
        if not isinstance(umslag, dict) or lykill not in umslag:
            return None
        umslag = umslag[lykill]
    return umslag


def keyra_skref(skref: str, grunnur: Path, unnid: Path, vefgogn: Path
                ) -> subprocess.CompletedProcess[str]:
    """``main.py --skref <skref>`` í eigin ferli, með allt úttak í tímabundnu möppunum."""
    umhverfi = {k: v for k, v in os.environ.items() if k != TRANSCRIPT_DIR_ENV}
    return subprocess.run(
        [sys.executable, "-c", RAESIR, str(PYTHON_ROT), str(unnid), str(vefgogn),
         "--skref", skref],
        capture_output=True,
        text=True,
        env={**umhverfi, GRUNNBREYTA: str(grunnur)},
        cwd=ROT,
        timeout=BIDTIMI_SEK,
    )


def vinnslupunktar(unnid: Path) -> list[Maelipunktur]:
    mappa = unnid / skjalftauttak.UNNID.name
    samantekt = json.loads((mappa / skjalftauttak.SAMANTEKTARSKRA).read_text(encoding="utf-8"))
    return [
        Maelipunktur("vinnsla", "jarðskjálftar", "samantekt.json: atburdir",
                     samantekt.get("atburdir")),
        Maelipunktur("vinnsla", "jarðskjálftar", f"línur í {skjalftauttak.ATBURDASKRA}",
                     _csv_radir(mappa / skjalftauttak.ATBURDASKRA)),
        Maelipunktur("vinnsla", "dagar í glugganum", "samantekt.json: dagar",
                     samantekt.get("dagar")),
        Maelipunktur("vinnsla", "dagar í glugganum", f"línur í {skjalftauttak.DAGASKRA}",
                     _csv_radir(mappa / skjalftauttak.DAGASKRA)),
    ]


def grunnpunktar(grunnur: Path) -> list[Maelipunktur]:
    with closing(sqlite3.connect(grunnur)) as samband:
        return [Maelipunktur("grunnur", heiti, sql, samband.execute(sql).fetchone()[0])
                for heiti, sql in GRUNNFYRIRSPURNIR]


def utflutningspunktar(vefgogn: Path) -> list[Maelipunktur]:
    umslog = {heiti: json.loads((vefgogn / heiti).read_text(encoding="utf-8"))
              for heiti in {skra for _, skra, _ in JSON_REITIR}}
    punktar = [Maelipunktur("útflutningur", heiti, f"{skra}: {'.'.join(slod)}",
                            _fletta(umslog[skra], slod))
               for heiti, skra, slod in JSON_REITIR]
    # Tímaröðin sjálf, sem myndritið teiknar, verður að ná yfir sömu atburði og daga.
    dagar = umslog[skjalftar_json.SKRAARHEITI]["gogn"]
    return punktar + [
        Maelipunktur("útflutningur", "jarðskjálftar", f"{skjalftar_json.SKRAARHEITI}: "
                     "summa gogn[].fjoldi", sum(d["fjoldi"] for d in dagar)),
        Maelipunktur("útflutningur", "dagar í glugganum",
                     f"{skjalftar_json.SKRAARHEITI}: fjöldi í gogn", len(dagar)),
    ]


class HeildarsamanburdurProf(unittest.TestCase):
    """Ein keyrsla pípunnar; sex tölur bornar við viðmiðið á hverju stigi."""

    @classmethod
    def setUpClass(cls) -> None:
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        mappa = Path(tmp.name)
        cls.grunnur = mappa / "rannsokn.sqlite"
        cls.unnid, cls.vefgogn = mappa / "processed", mappa / "gogn"
        cls.fingrafar_fyrir = _fingrafar(VERNDADAR)

        cls.keyrslur = {}
        for skref in SKREF:
            keyrsla = keyra_skref(skref, cls.grunnur, cls.unnid, cls.vefgogn)
            cls.keyrslur[skref] = keyrsla
            if keyrsla.returncode != 0:
                raise AssertionError(
                    f"main.py --skref {skref} skilaði {keyrsla.returncode}:\n{keyrsla.stderr}")

        cls.vaent = {heiti: vidmid_gildi(heiti) for heiti in SEX_GILDI}
        cls.punktar = [*vinnslupunktar(cls.unnid), *grunnpunktar(cls.grunnur),
                       *utflutningspunktar(cls.vefgogn)]

    def test_uttakid_for_i_timabundnu_moppurnar(self) -> None:
        """Skrefin skrifuðu þangað sem þeim var beint — ekki í repo-ið."""
        self.assertIn(f"Hlóð {len(SOFN)} gagnasöfnum í {self.grunnur}",
                      self.keyrslur["hlada"].stderr)
        self.assertIn(f"Flutti út {len(SKRAR)} skrár í {self.vefgogn}",
                      self.keyrslur["flytja-ut"].stderr)
        self.assertEqual(sorted(p.name for p in self.vefgogn.iterdir()), sorted(SKRAR))
        self.assertEqual(_fingrafar(VERNDADAR), self.fingrafar_fyrir,
                         "web/gogn/ eða data/processed/ breyttist í keyrslunni.")

    def test_hvert_stig_ber_sin_gildi(self) -> None:
        """Stig sem skilar engum punkti stæðist samanburðinn án þess að sanna neitt."""
        for stig, heiti in STIG.items():
            with self.subTest(stig=stig):
                self.assertEqual({p.heiti for p in self.punktar if p.stig == stig}, set(heiti))
        self.assertEqual({p.stig for p in self.punktar}, set(STIG))

    def test_sex_gildin_stemma_vid_gomlu_siduna(self) -> None:
        for stig in STIG:
            with self.subTest(stig=stig):
                punktar = [p for p in self.punktar if p.stig == stig]
                self.assertEqual([lysa(p, self.vaent) for p in frabrigdi(punktar, self.vaent)], [])

    def test_rangt_vidmid_fellur_a_hverju_stigi(self) -> None:
        """Hverju gildi ruglað í minni: allir punktar þess falla, engir aðrir."""
        for heiti in SEX_GILDI:
            vaent = self.vaent[heiti]
            ruglad = {**self.vaent, heiti: vaent + (1 if isinstance(vaent, int) else 0.01)}
            with self.subTest(heiti=heiti):
                fallnir = frabrigdi(self.punktar, ruglad)
                self.assertEqual(fallnir, [p for p in self.punktar if p.heiti == heiti])
                self.assertEqual({p.stig for p in fallnir},
                                 {stig for stig, nofn in STIG.items() if heiti in nofn})

    def test_skemmt_uttak_fellur_a_rettum_punkti(self) -> None:
        """Hin áttin: lesararnir lesa það sem pípan skrifaði, ekki web/gogn/ í repo-inu.

        Afrit af úttaki hvers stigs er skemmt á einum stað — atburð vantar í
        CSV og í grunninn, reit vantar í JSON — og nákvæmlega sá punktur fellur.
        """
        with tempfile.TemporaryDirectory() as tmp:
            afrit = Path(tmp)
            unnid = Path(shutil.copytree(self.unnid, afrit / "processed"))
            atburdir = unnid / skjalftauttak.UNNID.name / skjalftauttak.ATBURDASKRA
            linur = atburdir.read_text(encoding="utf-8").splitlines(keepends=True)
            atburdir.write_text("".join(linur[:-1]), encoding="utf-8")

            grunnur = Path(shutil.copyfile(self.grunnur, afrit / "rannsokn.sqlite"))
            with closing(sqlite3.connect(grunnur)) as samband, samband:
                samband.execute("DELETE FROM earthquakes WHERE event_id = "
                                "(SELECT MAX(event_id) FROM earthquakes)")

            vefgogn = Path(shutil.copytree(self.vefgogn, afrit / "gogn"))
            _, skra, slod = next(r for r in JSON_REITIR if r[0] == "tilsvör")
            umslag = json.loads((vefgogn / skra).read_text(encoding="utf-8"))
            del _fletta(umslag, slod[:-1])[slod[-1]]
            (vefgogn / skra).write_text(json.dumps(umslag), encoding="utf-8")

            punktar = [*vinnslupunktar(unnid), *grunnpunktar(grunnur),
                       *utflutningspunktar(vefgogn)]
            self.assertEqual(
                {p.hvadan for p in frabrigdi(punktar, self.vaent)},
                {f"línur í {skjalftauttak.ATBURDASKRA}", GRUNNFYRIRSPURNIR[0][1],
                 f"{skra}: {'.'.join(slod)}"},
            )


if __name__ == "__main__":
    unittest.main()
