"""Prófar íslenskt talna- og dagsetningarsnið myndritanna (issue #17).

Staðalsafnið eitt — keyrir alltaf, líka án matplotlib.

    python3 -m unittest discover -s tests
"""

import unittest

import hjalp  # noqa: F401  — setur src/python á sys.path; verður að koma fyrst

from utflutningur.islenskt_snid import (  # noqa: E402
    islensk_dagsetning,
    islensk_prosenta,
    islensk_tala,
)


class TolurTest(unittest.TestCase):
    def test_tugabrotskomma_og_thusundapunktur(self) -> None:
        self.assertEqual("5,5", islensk_tala(5.475, 1))
        self.assertEqual("1.234,50", islensk_tala(1234.5, 2))
        self.assertEqual("1.000.000", islensk_tala(1_000_000))
        self.assertEqual("187", islensk_tala(187))

    def test_ekkert_enskt_snid_laekur_i_gegn(self) -> None:
        for gildi in (0.5, 12345.678, 70.49):
            with self.subTest(gildi=gildi):
                texti = islensk_tala(gildi, 2)
                self.assertIn(",", texti)
                self.assertNotRegex(texti, r"\.\d{2}$")

    def test_neikvaedir_aukastafir_falla(self) -> None:
        with self.assertRaises(ValueError):
            islensk_tala(1.0, -1)

    def test_prosenta(self) -> None:
        self.assertEqual("70,5%", islensk_prosenta(43, 61))
        with self.assertRaises(ValueError):
            islensk_prosenta(1, 0)


class DagsetningarTest(unittest.TestCase):
    def test_stytt_og_fullt(self) -> None:
        self.assertEqual("1. nóv.", islensk_dagsetning("2023-11-01"))
        self.assertEqual("31. desember 2023", islensk_dagsetning("2023-12-31", stytt=False, med_ari=True))
        self.assertEqual("15. maí", islensk_dagsetning("2024-05-15"))

    def test_rangt_snid_fellur(self) -> None:
        for gildi in ("2023-13-01", "1.11.2023", ""):
            with self.subTest(gildi=gildi):
                with self.assertRaises(ValueError):
                    islensk_dagsetning(gildi)


if __name__ == "__main__":
    unittest.main()
