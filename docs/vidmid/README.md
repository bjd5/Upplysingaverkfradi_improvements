# Viðmiðið — frosið afrit af gamla verkefninu

Þessi mappa er **sönnunargagn, ekki vinnugögn.** Hér liggur afrit af því sem
gamla Quarto-verkefnið skilaði af sér, fryst eins og það var, svo hægt sé að
svara einni spurningu þegar nýja síðan er tilbúin:

> **Sýnir nýja síðan sömu tölur og sú gamla?**

Krafan er að svarið sé já (sjá [`../endurbygging.md`](../endurbygging.md),
kafla 2). Breytist tala er það villa þar til annað er sannað. Án frosins
viðmiðs er ekki hægt að sanna neitt — þá er bara hægt að vona.

Ekkert hér er handbreytt og ekkert hér verður handbreytt. Innihaldið er
afritað óbreytt (`cp -p`, breytingartímar varðveittir) og hver einasta skrá er
tryggð með SHA-256 í [`provenance.json`](provenance.json).

---

## 1. Af hverju þurfti að bjarga þessu

Gögnin fjögur hér að neðan áttu það sameiginlegt að vera **aðeins til á einni
vél**. Þau voru `gitignore`-uð í upprunaverkefninu að yfirlögðu ráði — sum af
því að þau eru afleidd, sum af því að þau voru of stór — og hefðu því horfið
með vélinni. Hvorki GitHub né CI hefði getað endurskapað þau: tvær af
vefþjónustunum skila öðru svari í dag en þær gerðu í september.

| Mappa | Skrár | Stærð | Hvað þetta er |
|---|---:|---:|---|
| [`vefur/`](vefur/) | 71 | 4,33 MB | Byggða gamla Quarto-síðan, 28 HTML-síður |
| [`generated/`](generated/) | 19 | 0,08 MB | Afleidd úttök greininganna sem Quarto límdi inn |
| [`phoebe-stats/`](phoebe-stats/) | 18 | 0,11 MB | Friends-tölfræðin fullreiknuð |
| `../../data/raw/mbl/` | 2 | 0,37 MB | mbl.is-eintakið — eina eintakið sem til er |
| **Samtals** | **110** | **4,89 MB** | |

### `vefur/` — byggða gamla síðan

Eina heildarskráin yfir hverja einustu tölu sem gamla síðan birtir. Tölurnar
eru þó aðeins til sem texti inni í HTML. **P0.2** las möppuna og skrifaði
vélleshæft viðmið: [`vidmid.json`](vidmid.json) og [`vidmid.md`](vidmid.md)
(sjá kafla 4).

`site_libs/` fylgir með óbreytt (Bootstrap, jQuery, popper). Það er ekki efni
heldur Quarto-umbúðir, og er einmitt hluti af ástæðunni fyrir endurbyggingunni
— nýja síðan er hreint HTML/CSS/JS án framework (CLAUDE.md, regla 3.4).

### `generated/` — afleidd úttök

Markdown- og JSON-bútar sem Quarto límdi inn í síðurnar. **`vedurstofa-*.md`
eru EINA ummerkið um veðurstöðvagögnin** — hráa API-svarið var aldrei vistað,
heldur sótt upp á nýtt í hverri byggingu. Gamla veðurstöðvasíðan sýndi því
aðrar tölur í dag en í gær. P0.3 sækir nýtt eintak og ber það saman við þessar
skrár; munurinn er vænt niðurstaða, ekki villa.

### `phoebe-stats/` — Friends-tölfræðin

Fullreiknaðar tölur: línufjöldi á persónu, senur, hlutföll, orðtíðni.
[`_meta.json`](phoebe-stats/_meta.json) geymir viðmiðstölurnar sem P1.6 og
P2.8 verða að hitta: 227 handritsskrár, 236 þættir, 61.161 tilsvar, 2,95%
óflokkað.

**Höfundaréttur:** handritin sjálf eru **ekki** hér og fara ekki í þetta repo.
`fangj/friends` hefur ekkert leyfi og þetta repo er opið. Það sem er hér eru
tölur *um* textann — tíðnitöflur og talningar, ekki textinn sjálfur. Lengstu
strengirnir eru stuttir frasar í tíðnitöflu (`signature-phrases.csv`).
Endanleg ákvörðun er í issue #3.

### `../../data/raw/mbl/` — mbl.is-eintakið

Liggur í `data/raw/` en ekki hér, því þetta eru **hrágögn**, ekki afleiða —
gagnaflæðið byrjar þar (CLAUDE.md, kafli 0). Provenance-færslan er þó hér með
hinum, enda sama björgunarverk. Sótt af `https://www.mbl.is/frettir/`
(**ekki** forsíðunni sjálfri) 2026-09-16.

---

## 2. Úr hvaða commit er byggða síðan? — leiðrétting

Verklýsing P0.1 sagði að byggða síðan væri frá commit `2865ed6`.
**Það stenst ekki.** Hið rétta er flóknara og skiptir máli fyrir P0.2.

`2865ed6` er frá **2026-09-20 11:51Z**, en engin skrá í byggingunni er yngri
en **2026-09-17 09:51:40Z**. Byggingin er þremur dögum eldri en commitið sem
hún átti að koma úr.

Það sem verra er: **þetta er ekki ein bygging heldur þrjár.** Quarto
endurbyggir aðeins þær síður sem hafa breyst, svo `vefur/` er samsett úr
þremur byggingum á tveimur dögum:

| Commit | Tími | Á sögu `main`? | Síður |
|---|---|---|---:|
| `5510cab` | 2026-09-16 14:55Z | ❌ **Nei** | 4 |
| `9cf667d` | 2026-09-16 23:06Z | ✅ Já | 2 |
| `fdf1261` | 2026-09-17 08:53Z | ✅ Já | 22 |

Fjórar síðurnar úr `5510cab` eru byggðar á grein (`tmp/samrunaprof`) sem
**rataði aldrei á `main`**. Og það eru ekki jaðarsíður:

- `friends/phoebe-statistics.html`
- `lotur/regex/mbl.html`
- `lotur/vefthjonustur/hagstofan.html`
- `friends/index.html`

Þrjár af kjarnasíðum rannsóknarinnar. Full sundurliðun — hver síða á sinni
lotu — er í `vidmidsbygging` í [`provenance.json`](provenance.json).

**Hvernig þetta var staðfest:** `docs/` var `gitignore`-uð í upprunarepo-inu
(lína 29), svo byggingin á sér ekkert beint git-ummerki. Sönnunin er
breytingartími hverrar skráar — varðveittur í afrituninni með `cp -p` — borinn
saman við `reflog` upprunarepo-sins, sem segir hvaða `HEAD` var virkur á þeim
tíma. Þær tvær heimildir stemma nákvæmlega og allar 28 síðurnar falla innan
lotu; engin er óflokkuð.

**Til samanburðar:** `origin/main` í upprunarepo-inu var kominn í `fb15d2a`
þegar afritað var — 16 commit á undan `2865ed6` og **22 á undan yngstu
byggingarlotunni**. Viðmiðið er þessi bygging, ekki `main` eins og hann er í
dag.

### Hvað þetta þýðir fyrir P0.2 — og hvað P0.2 fann

Viðmiðið er gilt sem viðmið — það er nákvæmlega það sem gamla síðan birti. En
það er **ekki innbyrðis samstæð bygging**, og P0.2 gerði ráð fyrir því:

- Ósamræmi milli síðna er væntanlegt og er sjálfstæð niðurstaða, ekki
  lestrarvilla. Síða úr `5510cab` þarf ekki að sýna sömu tölu og síða úr
  `fdf1261`. **Fimm slík atriði eru skráð** í
  [`vidmid.md`](vidmid.md), kafla 5 — tvö þeirra alvarleg.
- `phoebe-stats/_meta.json` var búið til **2026-09-17 09:47:09Z**, í yngstu
  lotunni, en `friends/phoebe-statistics.html` er frá deginum áður. **Þessi
  áhætta kom ekki fram:** eintökin tvö af `_meta.json` eru eins að öðru leyti
  en tímastimplinum, svo allar staðfestar tölur stemma við bæði.
  `phoebe-top-talkers.json` er hins vegar **í tveimur röðum** — sömu gildi,
  önnur röð, af því að jafntefli í röðuninni er brotið án fasts viðmiðs.

---

## 3. Að staðfesta að viðmiðið sé ósnert

```bash
python3 src/python/vidmid/provenance.py stadfesta
```

Skipunin reiknar SHA-256 af hverri skrá upp á nýtt og ber saman við
`provenance.json`. Hún gerir athugasemd við breytta skrá, horfna skrá **og**
skrá sem hefur bæst við án þess að vera skráð. Skili hún öðru en núlli er
viðmiðið ekki lengur ósnert og niðurstöður sem á því byggja eru ómarktækar.

Eingöngu Python-staðalsafnið; engin uppsetning.

`provenance.json` geymir fyrir hverja skrá: slóðina sem hún kom af, stærð í
bætum, SHA-256 og breytingartíma. Slóðir eru skráðar með `~` fyrir heimamöppu
— repo-ið er opið og full slóð bætir engu við.

Sé þörf á að endurskrifa skrána (t.d. eftir að P0.3 bætir við safni):

```bash
python3 src/python/vidmid/provenance.py skrifa
```

---

## 4. Viðmiðstölurnar — `vidmid.json` og `vidmid.md`

```bash
python3 src/python/vidmid/tolur.py skrifa      # byggir viðmiðið upp á nýtt
python3 src/python/vidmid/tolur.py stadfesta   # ber það við síðurnar
```

| Skrá | Hvað hún er |
|---|---|
| [`vidmid.json`](vidmid.json) | Vélleshæft viðmið: **1.391 tala** úr 28 síðum, þar af **445 efnislegar niðurstöður**. Hver tala með síðu, byggingarlotu, kaflakeðju, töfluröð/dálki, einingu og samhengi. |
| [`vidmid.md`](vidmid.md) | Sama efni fyrir manneskju: umfang, staðfestar tölur, ósamræmi, og vísir í hópaskrárnar. |
| [`vidmid/`](vidmid/) | Ein skrá á hverja síðu **nýju** síðunnar (sjá [`../endurbygging.md`](../endurbygging.md), kafla 3), svo hver síðuagent fái sitt viðmið í einni skrá. |

Tala sem er ekki niðurstaða — auðkenni (`0405`), issue-tilvísun (`#14`),
ISO-dagsetning, CSS-gildi, tala inni í kóðalistun — er **skráð áfram** með
`visst: false`. Próf sníða hana frá með einni síu; ekkert er þaggað.

### Það sem HTML-lestur nær ekki

Tvær síður birta **engar tölur í HTML-inu**. Þær reikna þær í JavaScript í
vafra lesandans:

| Síða | Viðmiðið er |
|---|---|
| `friends/phoebe-statistics.html` | Sjö skrár í `vefur/friends/phoebe-stats/` sem Observable Plot les |
| `tokens/index.html` | CSV sem Quarto bakaði inn í `<script type="text/plain">` |

Þetta er ástæða þess að sex af staðfestu tölunum — línur á persónu,
sviðsfyrirsagnir og sviðsleiðbeiningar — finnast hvergi í HTML-textanum.
**Fyrir kjarnasíðu rannsóknarinnar er gagnaskráin viðmiðið, ekki síðan.**

---

## 5. Reglur um þessa möppu

1. **Ekkert hér er handbreytt.** Hvorki skrárnar né `provenance.json`
   (CLAUDE.md, regla 10).
2. **Ekkert hér er endurbyggt.** Viðmið sem er endurbyggt er ekki viðmið.
3. **Handritin sjálf koma aldrei hingað** — aðeins tölur um þau (issue #3).
4. Bætist safn við: afritaðu óbreytt, keyrðu `skrifa`, og skráðu safnið í
   töfluna í kafla 1.
5. `vidmid.json`, `vidmid.md` og `vidmid/` eru **afleiður** — þær eru
   skrifaðar af `tolur.py`, aldrei handbreyttar (regla 10).
