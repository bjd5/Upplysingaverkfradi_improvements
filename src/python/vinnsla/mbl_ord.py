"""Sýnilegur texti og orðatalning úr vistuðu HTML-svari mbl.is (spurning 4).

Aðskilið frá hinum fjórum spurningunum af því að þetta er það eina sem þarf
fjölþrepa hreinsun áður en mynstrinu er beitt. Röð þrepanna ræður
niðurstöðunni og er því skjalfest hér, ekki falin inni í útdrættinum.

Hreinsunin fer fram í þessari röð:

1. HTML-athugasemdir og blokkir sem skila engum sýnilegum texta (``head``,
   ``script``, ``style``, ``template``, ``noscript``) eru fjarlægðar með
   innihaldinu.
2. Öðrum töggum er skipt út fyrir **bil** svo orð sitt hvorum megin við tagg
   límist ekki saman.
3. HTML-tákn á borð við ``&nbsp;``, ``&amp;`` og ``&#173;`` eru afkóðuð.
4. Unicode er samræmt (NFC), mjúk bandstrik felld burt, bandstrikaafbrigði
   samræmd og há-/lágstafir jafnaðir.
"""

from __future__ import annotations

import html
import unicodedata

from .mbl_mynstur import MYNSTUR_ORD, MYNSTUR_OSYNILEGT, MYNSTUR_TAGG

# Mjúkt bandstrik er skiptingarmerki, ekki stafur — það hverfur úr orðinu.
MJUKT_BANDSTRIK = "­"

# Öll bandstrikaafbrigði eru lesin sem sama bandstrikið svo „ferða-lög“ og
# „ferða‑lög“ (U+2011) teljist eitt og sama orðið.
BANDSTRIKAAFBRIGDI = "‐‑‒–—−"
BANDSTRIK = "-"


def synilegur_texti(html_texti: str) -> str:
    """Skilar þeim texta HTML-svarsins sem stendur eftir fyrir lesanda.

    Sjá þrepin fjögur í haus einingarinnar. Skilar samræmdum lágstafatexta.
    """
    texti = html_texti
    for mynstur in MYNSTUR_OSYNILEGT:
        texti = mynstur.sub(" ", texti)

    texti = MYNSTUR_TAGG.sub(" ", texti)
    texti = html.unescape(texti)
    texti = unicodedata.normalize("NFC", texti)
    texti = texti.replace(MJUKT_BANDSTRIK, "")
    for afbrigdi in BANDSTRIKAAFBRIGDI:
        texti = texti.replace(afbrigdi, BANDSTRIK)
    return texti.lower()


def synileg_ord(html_texti: str) -> list[str]:
    """Skilar sýnilegu orðunum í birtingarröð, hreinsuðum og lágstöfuðum."""
    return MYNSTUR_ORD.findall(synilegur_texti(html_texti))
