"""Hjálpargögn Friends-prófanna: gervihandrit og samanburður við viðmiðið.

**Gervihandritin** eru tilbúinn texti, aldrei handritin sjálf (issue #3,
valkostur A). Þau líkja aðeins eftir *sniðinu* — ``<p>Nafn: texti</p>``,
``[Scene: …]``, ``(sviðsleiðbeining)`` — svo hægt sé að telja í höndunum.
Væntu tölurnar í prófunum eru handtaldar úr ``GERVIHANDRIT``; breytist lína
þarf að telja upp á nýtt.

**Viðmiðið** er ``data/processed/phoebe-stats/`` — 17 skrár sem gamla skriftan
skrifaði, tryggðar með SHA-256 í ``docs/vidmid/provenance.json``. Það er
**lesið**, aldrei afritað inn í prófin, svo ekki sé hægt að laga próf að
greiningu í stað þess að laga greiningu að viðmiði. Samanburðurinn er **bæti
fyrir bæti**; einu leyfðu frávikin eru þau sem ``vinnsla.phoebe_samningur``
lýsir: vegguklukkustimplar felldir brott, ``generator``/``note`` vísa á nýju
eininguna og ``source_commit`` bætist aftast í ``_meta.json``.

Hjálpareining, ekki prófskrá (``unittest discover`` leitar að ``test*.py``).
"""

from __future__ import annotations

import json
from pathlib import Path

import hjalp  # noqa: F401  — setur src/python á sys.path
from hjalp import ROT

from vinnsla.friends_handrit import SOURCE_COMMIT  # noqa: E402
from vinnsla.phoebe_samningur import GENERATOR, SUMMARY_NOTE  # noqa: E402


# --- Gervihandrit --------------------------------------------------------------

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


# --- Samanburður við viðmiðið --------------------------------------------------

VIDMIDSMAPPA = ROT / "data" / "processed" / "phoebe-stats"
VIDMIDSMETA = VIDMIDSMAPPA / "_meta.json"

# skrá -> (stimpill sem er felldur brott, {lykill: nýtt gildi}, {aftast bætt við})
LEYFD_FRAVIK = {
    "_meta.json": ("generated_utc", {"generator": GENERATOR},
                   {"source_commit": SOURCE_COMMIT}),
    "summary.json": ("generated_at", {"note": SUMMARY_NOTE}, {}),
}


def vidmidsskrar() -> list[str]:
    """Heiti skránna sem viðmiðið geymir og úttakið verður að skrifa."""
    heiti = sorted(p.name for p in VIDMIDSMAPPA.iterdir())
    if not heiti:
        raise AssertionError(f"Viðmiðið í {VIDMIDSMAPPA} er tómt — samanburður sannar ekkert.")
    return heiti


def vidmidsmeta() -> dict:
    """Staðfestu tölurnar í ``_meta.json`` viðmiðsins."""
    return json.loads(VIDMIDSMETA.read_text(encoding="utf-8"))


def vaent_baeti(heiti: str) -> bytes:
    """Bætin sem úttaksskráin á að hafa: viðmiðið með leyfðu frávikunum einum."""
    frumrit = (VIDMIDSMAPPA / heiti).read_bytes()
    if heiti not in LEYFD_FRAVIK:
        return frumrit
    stimpill, skipt, baett = LEYFD_FRAVIK[heiti]
    gamalt = json.loads(frumrit)
    if stimpill not in gamalt:
        raise AssertionError(f"{heiti}: viðmiðið hefur ekki {stimpill} — fráviksskráin er úrelt.")
    nytt = {}
    for lykill, gildi in gamalt.items():
        if lykill == stimpill:
            continue
        nytt[lykill] = skipt.get(lykill, gildi)
    nytt.update(baett)
    return (json.dumps(nytt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def munur_vid_vidmid(mappa: Path) -> list[str]:
    """Skrár sem víkja frá viðmiðinu (eða vantar/eru umfram). Tómur listi = eins."""
    vaentar = vidmidsskrar()
    munur = []
    for heiti in vaentar:
        slod = mappa / heiti
        if not slod.is_file():
            munur.append(f"{heiti}: vantar")
        elif slod.read_bytes() != vaent_baeti(heiti):
            munur.append(f"{heiti}: önnur bæti")
    for aukaleg in sorted({p.name for p in mappa.iterdir()} - set(vaentar)):
        munur.append(f"{aukaleg}: umfram viðmiðið")
    return munur


def skrifa_vaent(mappa: Path) -> Path:
    """Skrifar væntu bætin í ``mappa`` — til að prófa samanburðinn sjálfan."""
    mappa.mkdir(parents=True, exist_ok=True)
    for heiti in vidmidsskrar():
        (mappa / heiti).write_bytes(vaent_baeti(heiti))
    return mappa
