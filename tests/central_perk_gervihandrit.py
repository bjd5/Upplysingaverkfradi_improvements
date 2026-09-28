"""Gervihandrit fyrir Central Perk-prófin — tilbúinn texti, aldrei handritin sjálf.

**Höfundaréttur (issue #3, valkostur A):** Friends-handritin fara aldrei í
þetta repo, hvorki heil, í brotum né sem prófgögn. Allar línur hér eru samdar
fyrir prófin og líkja aðeins eftir *sniðinu* sem Central Perk-greiningin les:
``<p>``-málsgreinar, ``<br>``-snið þáttaraðar 2, ``[Scene: …]`` og söngmerkingar.

Væntu tölurnar (``VAENT``) eru **handtaldar** úr textanum hér að neðan, ekki
lesnar úr úttaki kóðans. Breytist lína þarf að telja upp á nýtt.

Hjálpareining, ekki prófskrá (``unittest discover`` leitar að ``test*.py``).
"""

from __future__ import annotations

from pathlib import Path

# Uppfyllingarlínur svo 0101 nái 20 málsgreinum og lesist á <p>-sniðinu.
UPPFYLLING = "<p>Ross: Yes.</p>\n" * 7

# 0101 — <p>-snið, 20 málsgreinar, fjórar senur.
#   Sena 1 (CP): Phoebe (singing) → söngsena. Ross (singing) er ekki Phoebe.
#                „Monica and Phoebe“ er hópur og telst engum. „Pheobe“ = Phoebe.
#   Sena 2 (íbúð): Phoebe (sings) utan Central Perk → ekki söngsena.
#   Sena 3 (CP): sjálfstæð sviðslýsing „Phoebe is singing“ → söngsena.
#   Sena 4 ([Time lapse], ekki CP): tala og bandstrik prófa orðamynstrið.
# Orð: Phoebe 3+2+2=7 · Rachel 3 · Joey 1 · Chandler 5 · Ross 1+7=8 · Monica 0.
THATTUR_0101 = """<html><head><title>Gervi 0101</title></head><body>
<h1>Phoebe: titill utan p telst ekki</h1>
<p>[Scene: Central Perk, allir sitja.]</p>
<p>Phoebe: (singing) La la kisa.</p>
<p>Ross: (singing) Nope.</p>
<p>Monica and Phoebe: Hello both.</p>
<p>Pheobe: Hi you.</p>
<p>[Scene: Monica's Apartment.]</p>
<p>Phoebe: (sings) Not here.</p>
<p>Rachel: Don't go [to Ross] now.</p>
<p>[Scene: Central Perk, later.]</p>
<p>Phoebe is singing at the mic.</p>
<p>Joey: Wow.</p>
<p>[Time lapse]</p>
<p>Chandler: Could it be 2 well-known.</p>
""" + UPPFYLLING + "</body></html>\n"

# 0212-0213 — <br>-snið (ein málsgrein): tvö <br> skilja að tilsvör, stakt
# <br> er línuskil í sama tilsvari. Ross nefnir að Phoebe komi fram — það er
# tilsvar annarrar persónu og telst EKKI söngur.
# Orð: Phoebe 3 · Monica 1 · Ross 4 · Chandler 1.
THATTUR_0212 = """<html><head><title>Gervi 0212-0213</title></head><body>
<p>[Scene: Central Perk, allir sitja.]<br><br>
Phoe: Hello<br>there friends.<br><br>
Mnca: Hi.<br><br>
Ross: Phoebe is performing tonight.<br><br>
Chan: Okay.
</p>
</body></html>
"""

# 0305 — engin Central Perk-sena. Gestur telst ekki. Orð: Phoebe 3 · Joey 1.
THATTUR_0305 = """<html><body>
<p>[Scene: Monica's Apartment.]</p>
<p>Phoebe: One two three.</p>
<p>Joey: Hey.</p>
<p>Guest: Ignored words here.</p>
</body></html>
"""

# 0306 — bætin 0x92 eru cp1252-úrfellingarmerki og ógild í UTF-8. Lesið sem
# utf-8/replace verður „don�t“ að tveimur orðum (`don`, `t`): Joey 4.
# (friends_handrit.read_html myndi afkóða sem cp1252 og telja 3.)
THATTUR_0306 = (
    b"<html><body>\n<p>[Scene: Central Perk.]</p>\n"
    b"<p>Joey: I don\x92t know.</p>\n<p>Phoebe: Ok.</p>\n</body></html>\n"
)

# Undanskilin skrá með söng í Central Perk: teldist hún með breyttist allt.
UNDANSKILIN = """<html><body><p>[Scene: Central Perk.]</p>
<p>Phoebe: (singing) Aukaefni.</p></body></html>"""

GERVIHANDRIT: dict[str, str | bytes] = {
    "0101.html": THATTUR_0101,
    "0212-0213.html": THATTUR_0212,
    "0305.html": THATTUR_0305,
    "0306.html": THATTUR_0306,
    "0423uncut.html": UNDANSKILIN,
    "07outtakes.html": UNDANSKILIN,
}

# Handtalið: (hópur, söngsenur, orð Rachel, Monica, Phoebe, Joey, Chandler, Ross)
VAENT = {
    "0101": ("phoebe_sings", 2, (3, 0, 7, 1, 5, 8)),
    "0212-0213": ("central_perk", 0, (0, 1, 3, 0, 1, 4)),
    "0305": ("no_central_perk", 0, (0, 0, 3, 1, 0, 0)),
    "0306": ("central_perk", 0, (0, 0, 1, 4, 0, 0)),
}


def skrifa_gervihandrit(mappa: Path, skrar: dict[str, str | bytes] | None = None) -> Path:
    """Skrifar gervihandritin í ``mappa`` og skilar möppunni."""
    mappa.mkdir(parents=True, exist_ok=True)
    for heiti, efni in (skrar if skrar is not None else GERVIHANDRIT).items():
        if isinstance(efni, bytes):
            (mappa / heiti).write_bytes(efni)
        else:
            (mappa / heiti).write_text(efni, encoding="utf-8")
    # Skrá með annarri endingu á ekki að lesast.
    (mappa / "lestu-mig.txt").write_text("Ekki handrit.", encoding="utf-8")
    return mappa
