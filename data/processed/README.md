# Unnin gögn

Millistigið í gagnaflæðinu (CLAUDE.md, kafli 0): gögn sem hafa verið hreinsuð
eða reiknuð úr `data/raw/`, en eru ekki enn komin í grunninn.

Að meginreglu er **ekkert hér í git.** `.gitignore` útilokar möppuna, því
unnin gögn eru afleiða — það á að vera hægt að eyða þeim og reikna þau upp á
nýtt úr `data/raw/`. Sú regla hefur eina undanþágu, og hún er skjalfest hér.

---

## 1. `phoebe-stats/` — Friends-tölfræðin (í git)

| Atriði | Gildi |
|---|---|
| Skrár | 17 (9 CSV, 8 JSON) |
| Stærð | 101.857 bæti |
| Upprunalegt verkfæri | `src/phoebe_analysis.py` í upprunaverkefninu |
| Greint (UTC) | 2026-09-17T09:47:09Z |
| Gagnagrunnur greiningarinnar | 227 HTML-handritsskrár = 236 sýndir þættir |
| Í git? | **Já** — undanþága, sjá kafla 1.2 |
| Heimild | [`docs/heimildir.md`](../../docs/heimildir.md), kafli 2.1 |
| Ákvörðun (valkostur A) | [`docs/adferdafraedi.md`](../../docs/adferdafraedi.md), kafli 1.5.1 |
| Afmörkun og aðferð | [`docs/adferdafraedi.md`](../../docs/adferdafraedi.md), kafli 1.5 (þáttun) og 1.5.2 (handritsleit) |

### 1.1 Hvaðan skrárnar koma

Þær eru **bætaeins afrit** af `data/processed/phoebe-stats/` í
upprunaverkefninu — sama slóð og hér, því þessi mappa tekur við sama
hlutverki. SHA-256 hverrar skráar er skráð í
[`docs/vidmid/provenance.json`](../../docs/vidmid/provenance.json).

**Skrárnar eru ekki endurreiknaðar hér og verða það ekki.** Greiningarskriftan
las handritin, og handritin eru ekki í þessu repo-i (kafli 1.3). Það sem er hér
er niðurstaðan, fryst.

**Skrárnar hér eru bæði vinnugagnið og viðmiðið.** Áður lá annað bætaeins
eintak í `docs/vidmid/phoebe-stats/`; því var eytt 28.9.2026 því tvö eins
eintök sönnuðu ekkert umfram SHA-256. Breytist skrá hér — líka ef
`vinnsla.phoebe_uttak` er keyrt á raunhandritunum án `--uttak` — fellur
`provenance.py stadfesta` og `tests/test_vidmid.py`.

README greiningarinnar úr upprunaverkefninu (skilgreiningar og aðferð) er í
git-taginu: `git show vidmid-frosid:docs/vidmid/phoebe-stats/README.md`.

### 1.2 Af hverju þetta er í git þegar annað hér er það ekki

Vegna þess að skrárnar eru **ekki endurbyggjanlegar úr þessu repo-i**.
Aðfangið — handritin — er utan repo-sins og á einkarepo-um sem enginn í
teyminu stýrir. Fyrir þetta repo eru tölurnar því frumgagn, ekki afleiða, og
sama röksemd gildir um þær og um frystu hrágögnin í `data/raw/`: það sem er
aðeins til á einni vél er ekki til.

Þetta er valkostur A í issue #3, sem Björn valdi 27.9.2026. Rökin og
kostirnir sem var hafnað eru í
[`docs/adferdafraedi.md`](../../docs/adferdafraedi.md), kafla 1.5.1.

### 1.3 Það sem er hér — og það sem er ekki

**Er hér:** talningar, hlutföll, ræðuskipti og tíðnitöflur. Tölur *um* textann.

**Er ekki hér og kemur aldrei:** handritstextinn. Þetta repo er opið, og
handritasöfnin eru afrit aðdáenda á höfundarréttarvörðum sjónvarpshandritum.
Lengstu strengirnir í skránum eru þáttatitlar og þriggja orða brot í
tíðnitöflu — engin samfelld setning úr þáttunum.

Sú fullyrðing er ekki traustsatriði heldur **prófuð**:

```bash
python3 src/python/vidmid/handritsleit.py stadfesta
python3 -m unittest tests.test_handritsleit
```

Prófið leitar að strengjagildum sem líta út eins og setningar og fellur ef það
finnur eitt. Það les **aðeins talnaskrárnar** (JSON og CSV). Þröskuldarnir, röksemdin fyrir þeim og
afmörkunin eru í [`docs/adferdafraedi.md`](../../docs/adferdafraedi.md),
kafla 1.5.2.

### 1.4 Hvaða skrifta les þær

| Notandi | Hvað hann gerir |
|---|---|
| `src/python/vinnsla/` — **P1.6, issue #10** | Hleður tölunum í grunninn. Les **aðeins** úr þessari möppu og aldrei úr handritum |
| `src/python/vidmid/handritsleit.py` | Staðfestir að engin skrá geymi samfellda setningu |

Tölurnar birtast síðar á `web/sidur/phoebe-tolfraedi.html` og
`web/sidur/phoebe-central-perk.html` (bylgja 3).

### 1.5 Reglur

1. **Ekkert hér er handbreytt** (regla 10). Skrárnar eru afrit; breyting á
   þeim er villa, ekki uppfærsla.
2. **Ekkert hér er endurreiknað.** Aðfangið vantar og á að vanta.
3. **Handritin koma aldrei hingað** — hvorki afrituð né vendoruð
   (`.gitignore` útilokar `data/external/` og `data/fangj-friends/`). Hvort
   söfnin verða skráð sem submodule (slóð + commit-SHA, enginn texti) er
   **óákveðið** — spurning (a) í issue #3.
4. Staðfestingin er `python3 src/python/vidmid/provenance.py stadfesta`.

---

## 2. Annað sem lendir hér

Unnin gögn annarra safna (t.d. millistig hagstofuvinnslunnar) eru **ekki** í
git og eiga ekki að vera. Bætist safn við sem þarf undanþágu verður hún að vera
rökstudd hér með sömu spurningu: *er þetta endurbyggjanlegt úr `data/raw/` í
þessu repo-i?* Sé svarið já fer það ekki í git.
