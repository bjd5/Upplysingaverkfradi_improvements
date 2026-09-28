"""Gervihandrit fyrir Friends-prófin — tilbúinn texti, aldrei handritin sjálf.

**Höfundaréttur (issue #3, valkostur A):** Friends-handritin fara aldrei í
þetta repo, hvorki heil, í brotum né sem prófgögn. Allar línur hér eru samdar
fyrir prófin og líkja aðeins eftir *sniðinu* — ``<p>Nafn: texti</p>``,
``[Scene: …]``, ``(sviðsleiðbeining)`` — svo hægt sé að telja í höndunum.

Væntu tölurnar í prófunum eru handtaldar úr ``GERVIHANDRIT`` hér að neðan.
Breytist lína hér þarf að telja upp á nýtt.

Þetta er hjálpareining, ekki prófskrá: ``unittest discover`` leitar að
``test*.py`` og hleður henni aðeins þegar prófin flytja hana inn.
"""

from __future__ import annotations

from pathlib import Path

# Þáttaröð 1, einn þáttur. Þrjár senur; senan „Gata“ er tvíeykissena
# Phoebe og Joey. „All:“ er hóplína, „Transcribed by:“ er ekki ræðumaður og
# „Commercial Break“ er óflokkað. „C'mon Mon“ prófar að c'mon teljist ekki Mon.
THATTUR_0101 = """<html><head><title>Gervi 0101: Fyrsti</title>
<script>var ekki = "Phoebe: telst ekki";</script></head><body>
<h1>Gervi 0101</h1>
<p>[Scene: Kaffihús, allir sitja.]</p>
<p>Phoebe: Hello there (smiles) friends.</p>
<p>Rachel: Hi Pheebs!</p>
<p>Phoebe: Yes?</p>
<p>Ross: Phoebe, look.</p>
<p>All: Wow.</p>
<p>(Phoebe dansar)</p>
<p>[Scene: Íbúð.]</p>
<p>Monica: Come on Joe.</p>
<p>Joey: C'mon Mon.</p>
<p>Chandler: Could it be.</p>
<p>[Scene: Gata.]</p>
<p>Joey: Hey Phoebe how you doin.</p>
<p>Phoebe: Fine.</p>
<p>Transcribed by: Enginn</p>
<p>Commercial Break</p>
</body></html>
"""

# Þáttaröð 2, tvöfaldur þáttur (skráarheitið er í DOUBLE_EPISODE_FILES).
# „Phoe“ og „Mnca“ eru styttingar; Ursula og Phoebe Sr. eru EKKI Phoebe.
THATTUR_0212 = """<html><head><title>Gervi 0212-0213</title></head><body>
[Scene: Garður]<br>
Phoe: Ursula is here.<br>
Ursula: Hi.<br>
Phoebe: Go away.<br>
Phoebe Sr.: Stop.<br>
Mnca: Phoebe!<br>
</body></html>
"""

# Undanskildar skrár: ef þær teldust með myndi hver tala hækka.
UNDANSKILIN = """<html><body><p>Phoebe: Aukaefni sem má ekki teljast.</p></body></html>"""

GERVIHANDRIT = {
    "0101.html": THATTUR_0101,
    "0212-0213.html": THATTUR_0212,
    "0423uncut.html": UNDANSKILIN,
    "07outtakes.html": UNDANSKILIN,
}


def skrifa_gervihandrit(mappa: Path, skrar: dict[str, str] | None = None) -> Path:
    """Skrifar gervihandritin í ``mappa`` og skilar möppunni."""
    mappa.mkdir(parents=True, exist_ok=True)
    for heiti, texti in (skrar if skrar is not None else GERVIHANDRIT).items():
        (mappa / heiti).write_text(texti, encoding="utf-8")
    # Skrá með annarri endingu á ekki að lesast.
    (mappa / "lestu-mig.txt").write_text("Ekki handrit.", encoding="utf-8")
    return mappa
