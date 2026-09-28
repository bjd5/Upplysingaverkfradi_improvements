"""Prófar reglu 3.6 í CLAUDE.md: texti á vefsíðunni er stuttur og auðlesinn.

Keyrt með staðalsafninu einu:  python3 -m unittest discover -s tests
"""

from __future__ import annotations

import html
import re
import unittest

from test_vefur import SIDUR, lesa

HAMARK_ORD_INNGANGUR = 25
HAMARK_ORD_MALSGREIN = 45

MALSGREIN = re.compile(r"<(p|li|dd)\b([^>]*)>(.*?)</\1>", re.DOTALL)
MERKI = re.compile(r"<[^>]+>")
# Innri hugtök sem lesandi þarf ekki að sjá: slóðir í repo-inu og verkpakkanúmer.
INNRI_HUGTOK = re.compile(r"\b(?:web|docs|src|config)/|\bP\d\.\d+\b|\bissue #\d+")


def malsgreinar(sida: str) -> list[tuple[str, str]]:
    """(class-eigind, hreinn texti) fyrir hverja málsgrein í <main>."""
    efni = re.search(r"<main\b.*?</main>", lesa(sida), re.DOTALL).group(0)
    return [
        (eigindi, " ".join(html.unescape(MERKI.sub(" ", texti)).split()))
        for _, eigindi, texti in MALSGREIN.findall(efni)
    ]


class TextalengdTest(unittest.TestCase):
    def test_inngangar_eru_stuttir(self) -> None:
        for sida in SIDUR:
            for eigindi, texti in malsgreinar(sida):
                if "inngangur" in eigindi:
                    with self.subTest(sida=sida):
                        self.assertLessEqual(len(texti.split()), HAMARK_ORD_INNGANGUR, texti)

    def test_malsgreinar_eru_stuttar(self) -> None:
        for sida in SIDUR:
            for _, texti in malsgreinar(sida):
                with self.subTest(sida=sida, upphaf=texti[:40]):
                    self.assertLessEqual(len(texti.split()), HAMARK_ORD_MALSGREIN, texti)

    def test_engin_innri_hugtok_utan_adferdafraedi(self) -> None:
        for sida in SIDUR:
            if sida.endswith("adferdafraedi.html"):
                continue  # aðferðin lýsir möppum verkefnisins af ásetningi
            for _, texti in malsgreinar(sida):
                with self.subTest(sida=sida, upphaf=texti[:40]):
                    self.assertIsNone(INNRI_HUGTOK.search(texti), texti)


if __name__ == "__main__":
    unittest.main()
