"""Ber skjálftagreininguna saman við tölur gömlu síðunnar (issue #14, pakki P2.3).

Krafa verkefnisins er að nýja síðan sýni sömu tölur og sú gamla
(``docs/endurbygging.md``, kafli 2). Viðmiðið er ``docs/vidmid/vidmid.json``,
fryst úr byggðu gömlu síðunni (tagið ``vidmid-frosid``).

Tvennt skiptir máli um aðferðina:

* **Viðmiðið er lesið, ekki afritað.** Væntingarnar eru hvergi handskrifaðar
  hér; þær eru sóttar úr vidmid.json. Þannig er ekki hægt að laga próf að
  greiningu í stað þess að laga greiningu að viðmiði.
* **Hver uppfletting krefst nákvæmlega einnar samsvörunar.** Samanburður sem
  finnur enga línu stenst alltaf og sannar ekkert (lærdómurinn af issue #47);
  þess vegna fellur uppflettingin bæði á engri og á fleiri en einni línu.

Víki tala er það villa þar til annað er sannað.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import re
import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from vinnsla.jardskjalftar import lesa_skjalfta  # noqa: E402
from vinnsla.jardskjalftar_afmorkun import lesa_afmorkun  # noqa: E402
from vinnsla.jardskjalftar_samantekt import draga_saman  # noqa: E402
from vinnsla.jardskjalftar_talning import dagleg_talning, manadartalning  # noqa: E402

VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
SIDA = "capstone/earthquakes.html"

# Kaflarnir í gömlu síðunni sem tölurnar okkar koma úr.
KAFLI_YFIRLIT = "Fyrsta yfirlit úr hreinsuðum gögnum"
KAFLI_DAGAR = "Daglegur fjöldi eftir mánuðum"

# Gamla síðan birti tvo aukastafi. Við berum saman á sömu nákvæmni.
AUKASTAFIR = 2

# Efnisleg gildi Skjálftavaktarinnar í viðmiðinu. Talan var 90 þar til #38 var
# leyst; bandstrik í auðkenni var talið mínus (PR #45). Breytist hún er viðmiðið
# annað en það sem þessi greining var borin við.
EFNISLEG_GILDI = 89

# Fyrirsögn mánaðartöflu: „Nóvember 2023 30 dagar · Samtals 330“.
TOFLUHAUS = re.compile(r"(?P<ar>[0-9]{4})\s+(?P<dagar>[0-9]+)\s+dagar\s+·\s+Samtals\s+(?P<samtals>[0-9]+)")
# Línuheiti dagatöflunnar: „01.11.“
DAGSLINA = re.compile(r"^(?P<dagur>[0-9]{2})\.(?P<manudur>[0-9]{2})\.$")

SAMTOLULINA = "Samtals"
SULKA_FJOLDA = "Fjöldi"
KVARDATAFLA = "Stærðir eru teknar saman innan hvers skráðs kvarða"


def _vidmidsrader() -> list[dict]:
    """Efnisleg gildi Skjálftavaktarinnar úr vidmid.json.

    Aðeins gildi sem viðmiðsverkfærið merkti ``visst`` eru tekin með: hin eru
    slóðir, kóðabútar og tölur úr skýringartexta og eiga ekkert erindi í
    samanburð á niðurstöðum.
    """
    skjal = json.loads(VIDMID_JSON.read_text(encoding="utf-8"))
    return [rod for rod in skjal["gogn"] if rod["sida"] == SIDA and rod["visst"]]


def _einstok(rader: list[dict], hvad: str) -> dict:
    """Skilar einu gildi; engin samsvörun og margar eru hvor sín villa."""
    if len(rader) != 1:
        raise AssertionError(
            f"Uppflettingin '{hvad}' fann {len(rader)} línur í viðmiðinu, á að finna "
            "nákvæmlega eina. Samanburður við enga línu stenst alltaf og sannar ekkert."
        )
    return rader[0]


def _yfirlitsgildi(texti: str, tegund: str, samhengi: str) -> dict:
    """Flettir upp einni tölu úr yfirlitskaflanum eftir texta, gerð og samhengi."""
    return _einstok(
        [
            rod
            for rod in _vidmidsrader()
            if rod["kafli"][-1] == KAFLI_YFIRLIT
            and rod["texti"] == texti
            and rod["tegund"] == tegund
            and (rod["samhengi"] or "").startswith(samhengi)
        ],
        f"{KAFLI_YFIRLIT}: {texti!r} ({tegund})",
    )


def _kvardagildi(kvardi: str, sulka: str) -> dict:
    """Flettir upp einum reit í stærðartöflu gömlu síðunnar."""
    return _einstok(
        [
            rod
            for rod in _vidmidsrader()
            if rod["kafli"][-1] == KAFLI_YFIRLIT
            and (rod["tafla"] or "").startswith(KVARDATAFLA)
            and rod["lina"] == kvardi
            and rod["sulka"] == sulka
        ],
        f"stærðartafla: {kvardi} / {sulka}",
    )


def _dagatolur_vidmids() -> tuple[dict[str, int], dict[str, tuple[int, int]]]:
    """Dagatalningar og mánaðarsamtölur gömlu síðunnar úr mánaðartöflunum.

    Árið kemur úr fyrirsögn töflunnar og mánuðurinn úr línuheitinu, svo hvorugt
    sé ágiskað. Skilar (dagatalningar, mánaðarsamtölur) þar sem
    mánaðarsamtölurnar eru ``{YYYY-MM: (dagafjöldi, atburðafjöldi)}``.
    """
    dagar: dict[str, int] = {}
    manudir: dict[str, tuple[int, int]] = {}

    for rod in _vidmidsrader():
        if rod["kafli"][-1] != KAFLI_DAGAR or rod["sulka"] != SULKA_FJOLDA:
            continue
        haus = TOFLUHAUS.search(rod["tafla"] or "")
        if haus is None:
            raise AssertionError(f"Fyrirsögn mánaðartöflu er óvænt: {rod['tafla']!r}")
        ar = haus["ar"]

        if rod["lina"] == SAMTOLULINA:
            continue
        lina = DAGSLINA.match(rod["lina"] or "")
        if lina is None:
            raise AssertionError(f"Línuheiti dagatöflu er óvænt: {rod['lina']!r}")

        manudur = f"{ar}-{lina['manudur']}"
        dagar[f"{manudur}-{lina['dagur']}"] = rod["gildi"]
        manudir[manudur] = (int(haus["dagar"]), int(haus["samtals"]))

    return dagar, manudir


def _namunda(gildi: float) -> float:
    """Námundar á sömu nákvæmni og gamla síðan birti."""
    return round(float(gildi), AUKASTAFIR)


class Vidmidid(unittest.TestCase):
    """Viðmiðið sjálft — stenst samanburðurinn á réttu safni?"""

    def test_fjoldi_efnislegra_gilda(self) -> None:
        self.assertEqual(len(_vidmidsrader()), EFNISLEG_GILDI)


class SkjalftatolurStanda(unittest.TestCase):
    """Hver tala greiningarinnar á sér línu í viðmiðinu og þau stemma."""

    @classmethod
    def setUpClass(cls) -> None:
        afmorkun = lesa_afmorkun()
        skjalftar = lesa_skjalfta(None, afmorkun)
        cls.dagatalning = dagleg_talning(skjalftar, afmorkun)
        cls.samantekt = draga_saman(skjalftar, cls.dagatalning)
        cls.manudir = manadartalning(cls.dagatalning)

    def test_fjoldi_atburda_og_daga(self) -> None:
        upphaf = "Úrtakið inniheldur"
        self.assertEqual(
            self.samantekt.atburdir, _yfirlitsgildi("334", "heiltala", upphaf)["gildi"]
        )
        self.assertEqual(
            self.samantekt.dagar, _yfirlitsgildi("61", "heiltala", upphaf)["gildi"]
        )

    def test_daglegur_fjoldi(self) -> None:
        upphaf = "Daglegur fjöldi:"
        dreifing = self.samantekt.dagleg_dreifing
        self.assertEqual(
            _namunda(dreifing.midgildi),
            _yfirlitsgildi("0,00", "desimal", upphaf)["gildi"],
        )
        self.assertEqual(
            dreifing.lagmark, _yfirlitsgildi("0", "heiltala", upphaf)["gildi"]
        )
        self.assertEqual(
            dreifing.hamark, _yfirlitsgildi("187", "heiltala", upphaf)["gildi"]
        )
        self.assertEqual(
            self.samantekt.dagar_an_atburda,
            _yfirlitsgildi("43", "heiltala", upphaf)["gildi"],
        )

    def test_dypt(self) -> None:
        upphaf = "Dýpt:"
        bil = _yfirlitsgildi("0,07–11,26", "bil", upphaf)["bil"]
        self.assertEqual(
            [_namunda(self.samantekt.dypt_km.lagmark), _namunda(self.samantekt.dypt_km.hamark)],
            bil,
        )
        self.assertEqual(
            _namunda(self.samantekt.dypt_km.midgildi),
            _yfirlitsgildi("4,67", "desimal", upphaf)["gildi"],
        )

    def test_staerdir_eftir_kvarda(self) -> None:
        kvardar = {k.magnitude_type: k.dreifing for k in self.samantekt.staerdir}
        self.assertEqual(sorted(kvardar), ["Mlw"])
        dreifing = kvardar["Mlw"]
        self.assertEqual(dreifing.fjoldi, _kvardagildi("Mlw", "Fjöldi")["gildi"])
        self.assertEqual(
            _namunda(dreifing.lagmark), _kvardagildi("Mlw", "Lágmark")["gildi"]
        )
        self.assertEqual(
            _namunda(dreifing.hamark), _kvardagildi("Mlw", "Hámark")["gildi"]
        )
        self.assertEqual(
            _namunda(dreifing.midgildi), _kvardagildi("Mlw", "Miðgildi")["gildi"]
        )

    def test_allar_dagatalningar(self) -> None:
        vidmid, _ = _dagatolur_vidmids()
        self.assertEqual(len(vidmid), self.samantekt.dagar)
        self.assertEqual(
            {dagur.utc_day: dagur.event_count for dagur in self.dagatalning}, vidmid
        )

    def test_manadarsamtolur(self) -> None:
        _, vidmid = _dagatolur_vidmids()
        self.assertEqual(
            {m.month: (m.day_count, m.event_count) for m in self.manudir}, vidmid
        )


if __name__ == "__main__":
    unittest.main()
