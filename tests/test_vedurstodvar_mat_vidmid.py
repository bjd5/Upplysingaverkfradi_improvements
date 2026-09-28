"""Ber veðurstöðvamatið saman við gömlu síðuna og prófar úttakið (issue #14, P2.4).

Frosna eintakið í ``data/raw/vedurstodvar/`` er **ný söfnun** og mátti víkja
frá gömlu síðunni (``docs/vedurstodvar-samanburdur.md``). Það gerir það ekki:
matið á að gefa hverja tölu sem gamla síðan birti í svörum æfingarinnar og á
súluritinu. Víki tala er það skráð frávik, ekki eitthvað sem prófið lagar sig að.

Viðmiðið er **lesið, ekki afritað**: tölurnar koma úr ``docs/vidmid/vidmid.json``
og ``docs/vidmid/generated/vedurstofa-stodvar.svg``. Hver uppfletting ber saman
**alla** röð talnanna í svarinu, svo tala sem vantar, bætist við eða víkur
fellir prófið — og uppfletting sem finnur ekkert fellur líka (kafli 15).

Prófin skrifa aðeins í tímabundnar möppur; ``data/`` og ``web/gogn/`` eru
óhreyfð (regla 10).

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst
from hjalp import ROT  # noqa: E402

from vinnsla import vedurstodvar_uttak as uttak  # noqa: E402
from vinnsla.vedurstodvar_hledsla import FROSID, HledsluVilla, lesa_eintak  # noqa: E402
from vinnsla.vedurstodvar_mat import MatVilla, meta  # noqa: E402
from vinnsla.vedurstodvar_samanburdur import AR_AFTUR_I_TIMANN, lesa_vidmid_siur  # noqa: E402

VIDMID_JSON = ROT / "docs" / "vidmid" / "vidmid.json"
VIDMID_SVG = ROT / "docs" / "vidmid" / "generated" / "vedurstofa-stodvar.svg"
SIDA = "lotur/vefthjonustur/vedurstofan.html"
KAFLI_SVOR = "Svör við spurningum æfingarinnar"
KAFLI_NIDURSTADA = "Niðurstaða"

# Súluritið sýndi tíu næstu stöðvarnar. Talan er framsetningarval gömlu
# síðunnar, ekki hluti matsins — hún er aðeins notuð til að þátta viðmiðið.
LINUR_A_MYND = 10

SVG_NAFN = re.compile(r'text-anchor="end">(?P<nafn>.+) \((?P<audkenni>[0-9]+)\)</text>')
SVG_GILDI = re.compile(r'>(?P<metrar>[0-9]+) m · (?P<start>[0-9]{4})–(?P<lok>[0-9]{4})?</text>')


def _tolur_i_svari(kafli: str, upphaf: str = "") -> tuple[int, ...]:
    """Allar tölur gömlu síðunnar í einu svari, í þeirri röð sem þær birtust."""
    skjal = json.loads(VIDMID_JSON.read_text(encoding="utf-8"))
    rader = [
        rod
        for rod in skjal["gogn"]
        if rod["sida"] == SIDA
        and rod["kafli"][-1] == kafli
        and rod["flokkur"] == "malsgrein"
        and (rod["samhengi"] or "").startswith(upphaf)
        and rod["gildi"] is not None
    ]
    if not rader:
        raise AssertionError(
            f"Engin tala fannst í viðmiðinu fyrir {kafli!r} / {upphaf!r}. "
            "Samanburður við ekkert stenst alltaf og sannar ekkert."
        )
    return tuple(int(rod["gildi"]) for rod in sorted(rader, key=lambda rod: rod["id"]))


class MatFrosnaEintaksinsGegnVidmidi(unittest.TestCase):
    """Sama spurning, sama svar: hver tala svaranna á gömlu síðunni."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mat = meta(lesa_eintak()[2])

    def test_nidurstadan_nefnir_somu_stod(self) -> None:
        m = self.mat
        self.assertEqual(_tolur_i_svari(KAFLI_NIDURSTADA), (m.valin.station_id, m.valin.metrar))

    def test_svar_1_naesta_stod_og_hvort_hun_se_virk(self) -> None:
        m = self.mat
        self.assertEqual(
            _tolur_i_svari(KAFLI_SVOR, "Hver er næsta veðurstöð"),
            (m.naesta.station_id, m.naesta.metrar),
        )
        # Gamla síðan svaraði „mælir enn“ — það á aðeins við sé næsta stöð virk.
        self.assertTrue(m.naesta.er_virk)

    def test_svar_2_naesta_virka_naesta_aflagda_og_munurinn(self) -> None:
        m = self.mat
        self.assertEqual(
            _tolur_i_svari(KAFLI_SVOR, "Hver er næsta virka stöðin"),
            (
                m.valin.station_id, m.valin.metrar,
                m.naesta_aflogd.station_id, m.naesta_aflogd.metrar,
                m.naesta_aflogd.end_year, m.munur_metrar,
            ),
        )

    def test_svar_3_hlutfall_virkra(self) -> None:
        m = self.mat
        self.assertEqual(
            _tolur_i_svari(KAFLI_SVOR, "Hversu margar af stöðvunum"),
            (m.fjoldi_virkra, m.fjoldi_allra, m.hlutfall_virkra_prosent),
        )

    def test_svar_5_langtimastodin(self) -> None:
        m = self.mat
        self.assertFalse(m.valin_naer_aftur)  # gamla síðan svaraði „Nei.“
        self.assertEqual(
            _tolur_i_svari(KAFLI_SVOR, "Dygði sama stöð"),
            (
                AR_AFTUR_I_TIMANN, m.valin.station_id, m.valin.start_year,
                m.vidmidunarar, m.langtimastod.station_id,
                m.langtimastod.metrar, m.langtimastod.start_year,
            ),
        )

    def test_kassinn_hefur_jafnmargar_stodvar_og_polygon_sian(self) -> None:
        vidmid = lesa_vidmid_siur()
        self.assertEqual(len(self.mat.naestu), vidmid["`polygon`"])
        self.assertEqual(
            sum(1 for stod in self.mat.naestu if stod.er_virk),
            vidmid["`polygon` + `active=true`"],
        )

    def test_rodunin_er_su_sama_og_a_sulnaritinu(self) -> None:
        texti = VIDMID_SVG.read_text(encoding="utf-8")
        nofn = [(m["nafn"], int(m["audkenni"])) for m in SVG_NAFN.finditer(texti)]
        gildi = [
            (int(m["metrar"]), int(m["start"]), int(m["lok"]) if m["lok"] else None)
            for m in SVG_GILDI.finditer(texti)
        ]
        self.assertEqual((len(nofn), len(gildi)), (LINUR_A_MYND, LINUR_A_MYND))
        self.assertEqual(
            list(zip(nofn, gildi)),
            [
                ((s.name, s.station_id), (s.metrar, s.start_year, s.end_year))
                for s in self.mat.naestu[:LINUR_A_MYND]
            ],
        )


class UttakMatsins(unittest.TestCase):
    """``mat.json`` í data/processed: hrein afleiða og aldrei í web/gogn."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mappa = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_tvaer_keyrslur_gefa_somu_baeti(self) -> None:
        fyrri, _ = uttak.vinna_vedurstodvar(mappa=self.mappa / "a")
        seinni, _ = uttak.vinna_vedurstodvar(mappa=self.mappa / "b")
        self.assertEqual(fyrri.read_bytes(), seinni.read_bytes())

    def test_skjalid_ber_uppruna_en_engan_keyrslutima(self) -> None:
        slod, mat = uttak.vinna_vedurstodvar(mappa=self.mappa)
        skjal = json.loads(slod.read_text(encoding="utf-8"))
        provenance = json.loads((FROSID / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(skjal["uppruni"]["sha256"], provenance["sha256"])
        self.assertEqual(skjal["uppruni"]["sott_utc"], provenance["fetched_at_utc"])
        self.assertEqual(skjal["valin"]["station_id"], mat.valin.station_id)
        self.assertEqual(len(skjal["naestu"]), len(mat.naestu))
        self.assertNotIn("km", skjal["valin"])
        # Eini tímastimpillinn er sóknartíminn; enginn stimpill keyrslunnar.
        stimplar = re.findall(r"\d{4}-\d{2}-\d{2}T[0-9:]+Z", slod.read_text(encoding="utf-8"))
        self.assertEqual(set(stimplar), {provenance["fetched_at_utc"]})

    def test_breytt_eintak_stodvar_matid_og_ekkert_er_skrifad(self) -> None:
        frosid = self.mappa / "frosid"
        shutil.copytree(FROSID, frosid)
        provenance = json.loads((frosid / "provenance.json").read_text(encoding="utf-8"))
        eintak = frosid / provenance["response_file"]
        eintak.write_bytes(eintak.read_bytes().replace(b"1469", b"1468", 1))
        with self.assertRaisesRegex(HledsluVilla, "SHA-256"):
            uttak.vinna_vedurstodvar(frosid=frosid, mappa=self.mappa / "ut")
        self.assertFalse((self.mappa / "ut" / uttak.MATSKRA).exists())

    def test_skrifar_ekki_i_web_gogn(self) -> None:
        for mappa in (uttak.VEFGOGN, uttak.VEFGOGN / "vedurstodvar"):
            with self.subTest(mappa=mappa), self.assertRaisesRegex(MatVilla, "web"):
                uttak.vinna_vedurstodvar(mappa=mappa)

    def test_systurmappa_web_gogn_er_leyfd(self) -> None:
        # Varnaglinn ber saman möppur, ekki strengi: "gogn-x" er ekki "gogn".
        uttak.krefjast_utan_vefs(self.mappa / "web" / "gogn")
        uttak.krefjast_utan_vefs(uttak.VEFGOGN.with_name("gogn-annad"))


if __name__ == "__main__":
    unittest.main()
