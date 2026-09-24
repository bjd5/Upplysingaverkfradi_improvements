# Verkpakkar fyrir agenta

Niðurbrot endurbyggingarinnar í pakka sem **einn agent klárar í einni lotu**.
Hver pakki = eitt issue = ein grein = eitt PR.

Samhengið er í [`endurbygging.md`](endurbygging.md); reglurnar í
[`../CLAUDE.md`](../CLAUDE.md). Þetta skjal segir hver gerir hvað, í hvaða röð.

---

## 1. Hvernig þetta er notað

1. Veldu pakka sem er **ekki blokkaður** (sjá töfluna í kafla 3).
2. Afritaðu **hausinn** (kafli 2) + prompt pakkans inn í nýja Claude Code-lotu.
3. Einn agent = einn pakki. Ekki gefa sama agent tvo pakka í röð — ný lota í staðinn.

**Um `--persona-scribe`:** íslenska (`is`) er **ekki** í tungumálalista
persónunnar (`en, es, fr, de, ja, zh, pt, it, ru, ko`). Notið
`--persona-scribe=en` og treystið á reglu 7 í CLAUDE.md um að efni sé á
íslensku — hausinn ítrekar það.

---

## 2. Hausinn — fer fremst í hvert einasta prompt

```text
Þú vinnur í repo-inu bjd5/Upplysingaverkfradi_improvements.

Lestu ÁÐUR en þú býrð til skrá:
  - CLAUDE.md          (bindandi regluverk — regla 1 ræður staðsetningu skráa)
  - docs/endurbygging.md  (samhengið: hvaðan verkefnið kemur og hvað má ekki tapast)

Fastar reglur fyrir þessa lotu:
  - Þú vinnur AÐEINS að því issue sem nefnt er hér að neðan. Finnir þú annað
    sem þarf að laga: skráðu það sem athugasemd í issue-ið, ekki lagaðu það.
  - Vinnið á grein, aldrei beint á main. Greinarheiti: <svið>/<stutt-lýsing>.
  - Commit-skilaboð á forminu `svið: hvað var gert` (regla 7).
  - Efni sem notandi les er á ÍSLENSKU. Kóðaheiti á ensku (regla 1.2 og 9.7).
  - Engir nýir pakkar, framework eða CDN-tenglar án þess að spyrja (regla 10).
    Sjálfgefið er Python-staðalsafnið og hreint HTML/CSS/JS.
  - Aldrei handbreyta data/raw/ né web/gogn/ (regla 10).
  - Engin skrá yfir ~300 línur (regla 6).
  - Villur eru aldrei þaggaðar (regla 6).
  - Ljúktu á að telja upp hvaða liði úr gátlista reglu 9 þú staðfestir og hverja
    ekki — og af hverju ekki.
```

---

## 3. Pakkarnir

`✅` = lokið · `🟢` = má hefja núna · `⏸` = blokkað · `👤` = Björn, ekki agent

Staðan er lesin úr greinum repo-sins **24.9.2026**. Lokin verk bíða samruna við
`main` — greinin sem geymir verkið fylgir í stöðudálkinum. Blokkunardálkurinn
telur aðeins það sem **enn** er ólokið.

### Bylgja 0 — björgun og grunnur

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P0.1** Bjarga gögnum af disknum | #30 | `--persona-devops` | ✅ `gagnabjorgun/frysta-vidmid` | — |
| **P0.2** Lesa viðmiðstölur úr byggðu síðunni | #30 | `--persona-analyzer` | ✅ `vidmid/lesa-tolur` | — |
| **P0.3** Frysta hrágögn + `.gitignore` | #2 | `--persona-devops` | ✅ `gagnabjorgun/frysta-hragogn` | — |
| **P0.4** Heimildir og aðferðafræði | #4 | `--persona-scribe=en` | ✅ `skjolun/heimildir-adferdafraedi` | — |
| **P0.5** Höfundaréttarákvörðun | #3 | 👤 | 🟢 | — |
| **P0.6** Myndritaákvörðun | #17 | 👤 | 🟢 | — |

TMDB náðist ekki að frysta í P0.3 — `TMDB_TOKEN` er hvergi til. Það er skráð í
`data/raw/frysting.json` og stöðvar ekkert annað verk.

**P0.5 og P0.6 eru nú á gagnrýnu leiðinni:** P0.5 blokkar P1.6, P2.5 og P2.6;
P0.6 blokkar P3.3 og þar með allar myndritasíður.

### Bylgja 1 — gagnalag

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P1.1** Migration-keyrari og tengilag | #5 | `--persona-backend` | ✅ `gagnagrunnur/migration-keyrari` | — |
| **P1.2** Skjálftavaktin: schema + hleðsla | #6 | `--persona-backend` | 🟢 | — |
| **P1.3** Hagstofan: schema + hleðsla | #7 | `--persona-backend` | 🟢 | — |
| **P1.4** Veðurstöðvar: schema + hleðsla | #8 | `--persona-backend` | 🟢 | — |
| **P1.5** mbl.is: schema + hleðsla | #9 | `--persona-backend` | 🟢 | — |
| **P1.6** Friends: schema + hleðsla | #10 | `--persona-backend` | ⏸ | P0.5 |
| **P1.7** Fyrirspurnir | #11 | `--persona-backend` | ⏸ | P1.2–P1.6 |

P0.3 og P1.1 eru bæði komin, svo **P1.2–P1.5 mega fara af stað núna og
samtímis** — þau snerta sitt hvora migration og sitt hvora töflu. P1.6 bíður
höfundaréttarákvörðunarinnar (P0.5), ekki gagnanna.

### Bylgja 2 — Python-pípan

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P2.1** HTTP-lag | #12 | `--persona-backend` | ✅ `sofnun/http-lag` | — |
| **P2.2** Söfnunarskriftur fluttar | #13 | `--persona-backend` | 🟢 | — |
| **P2.3** Kljúfa `earthquakes.py` (557 l.) | #14 | `--persona-refactorer` | ⏸ | P2.2 |
| **P2.4** Kljúfa `vedurstofa_stodvar.py` (637 l.) | #14 | `--persona-refactorer` | ⏸ | P2.2 |
| **P2.5** Kljúfa `phoebe_analysis.py` (1.199 l.) | #14 | `--persona-refactorer` | ⏸ | P2.2, P0.5 |
| **P2.6** Kljúfa `phoebe_central_perk.py` (877 l.) | #14 | `--persona-refactorer` | ⏸ | P2.2, P0.5 |
| **P2.7** Útflutningur í `web/gogn/` | #15 | `--persona-backend` | ⏸ | P1.7, P2.3–P2.6 |
| **P2.8** Próf og samanburður við viðmið | #16 | `--persona-qa` | ⏸ | P2.7 |

#14 er klofið í fjóra pakka af ásettu ráði — 3.270 línur eru ekki ein lota.
P2.3–P2.6 eru óháð innbyrðis. Viðmiðið sem P2.8 ber saman við er tilbúið
(P0.2): 445 tölur í `docs/vidmid/vidmid.json`.

### Bylgja 3 — vefsíðan

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P3.1** Beinagrind og sjónrænt kerfi | #18 | `--persona-frontend` | 🟢 | — |
| **P3.2** JS-gagnahleðsla | #19 | `--persona-frontend` | ⏸ | P3.1, P2.7 |
| **P3.3** Myndritalag | #17 | `--persona-frontend` | ⏸ | P0.6, P3.1 |
| **P3.4** Síða: Skjálftavaktin | #20 | `--persona-frontend` | ⏸ | P3.2, P3.3 |
| **P3.5** Síða: Hagstofan | #21 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.6** Síða: Veðurstöðvar | #22 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.7** Síða: mbl.is regex | #23 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.8** Síða: Phoebe-tölfræði | #24 | `--persona-frontend` | ⏸ | P3.2, P3.3 |
| **P3.9** Síða: Central Perk | #24 | `--persona-frontend` | ⏸ | P3.2, P3.3 |
| **P3.10** Síða: TMDB | #24 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.11** Síða: aðferðafræði | #25 | `--persona-scribe=en` | ⏸ | P3.1 |

#24 er klofið í þrjár síður. P3.4–P3.11 eru óháð innbyrðis. **P3.1 er eini
pakki bylgju 3 sem má hefja núna** og hann opnar alla hina — hann er því
næstur á eftir P1.2–P1.5 í forgangi.

### Bylgja 4 — gæði og útgáfa

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P4.1** Aðgengisúttekt | #26 | `--persona-frontend` | ⏸ | P3.4–P3.11 |
| **P4.2** Frammistöðuúttekt | #27 | `--persona-performance` | ⏸ | P3.4–P3.11 |
| **P4.3** Leyndarmálaúttekt | #28 | `--persona-security` | ⏸ | P3.4–P3.11 |
| **P4.4** Birting á Pages | #28 | `--persona-devops` | ⏸ | P4.1–P4.3 |
| **P4.5** README og verklok | #29 | `--persona-scribe=en` | ⏸ | P4.4 |

### Hvað er hægt að setja í gang núna

Sex pakkar eru lausir: **P1.2, P1.3, P1.4, P1.5** (hver sína migration),
**P2.2** (söfnunarskriftur yfir á HTTP-lagið úr P2.1) og **P3.1**
(vefbeinagrindin, engin gögn nauðsynleg). Þeir snerta engar sömu skrár og mega
því allir fara samtímis — ein vinnumappa á hvern (kafli 10).

Tvær ákvarðanir Björns (**P0.5**, **P0.6**) eru það sem heldur mestu eftir.

---

## 4. Prompt: P0.1 — bjarga gögnum af disknum

**Persóna:** `--persona-devops` · **Issue:** #30 · ✅ **Lokið** — `gagnabjorgun/frysta-vidmid`

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #30 — bjarga gögnum sem eru aðeins til á þessari vél.

Fjórar möppur liggja utan git og eiga sér hvergi afrit. Þær eru gitignored í
upprunaverkefninu að yfirlögðu ráði, svo þær hverfa með vélinni. Afritaðu þær
inn í þetta repo ÁÐUR en nokkuð annað er gert:

1. mbl.is-eintakið — EINA eintakið sem til er:
   ~/Desktop/Skóla forritun/upplysingver/data/raw/mbl/mbl-20260916T120851Z.html
   ~/Desktop/Skóla forritun/upplysingver/data/raw/mbl/mbl-20260916T120851Z.json
   → data/raw/mbl/
   Athugið: slóðin sem var sótt er https://www.mbl.is/frettir/ (ekki forsíðan).

2. Byggða gamla síðan — 28 HTML-skrár, 4,3 MB, byggð 2026-09-17:
   ~/PycharmProjects/idn302g-2026-team-friends-thesveinn/docs/
   → docs/vidmid/vefur/
   Þetta er eina heildarskráin yfir hverja tölu sem gamla síðan birtir.

3. Afleidd úttök greininganna:
   ~/PycharmProjects/idn302g-2026-team-friends-thesveinn/site/_generated/  (19 skrár)
   → docs/vidmid/generated/
   vedurstofa-*.md þar eru EINA ummerkið um veðurstöðvagögnin sem varð til —
   hráa API-svarið var aldrei vistað.

4. Friends-tölfræðin fullreiknuð:
   ~/PycharmProjects/idn302g-2026-team-friends-thesveinn/data/processed/phoebe-stats/
   → docs/vidmid/phoebe-stats/

Kröfur:
- Afritaðu ÓBREYTT. Engin hreinsun, engin endurröðun, engin nafnabreyting.
- Skrifaðu docs/vidmid/provenance.json: fyrir hverja skrá slóðin sem hún kom
  af, stærð, SHA-256 og afritunartími. Þetta er sönnunin fyrir að viðmiðið sé
  ósnert.
- Byggða síðan er frá commit 2865ed6 í upprunarepo-inu. origin/main þar er
  kominn í fb15d2a — 16 commit lengra. Skráðu ÞAÐ skýrt í provenance og í
  docs/vidmid/README.md: viðmiðið er 2865ed6, ekki núverandi main.
- Opnaðu undanþágur í .gitignore svo docs/vidmid/ og data/raw/mbl/ komist í
  git. data/raw/* er útilokað í dag.
- docs/vidmid/README.md: hvað hver mappa er, hvaðan hún kom, af hverju hún er
  fryst og hvaða spurningu hún svarar (= „sýnir nýja síðan sömu tölur?").

Ekki gera:
- Ekki keyra greiningarskriftur. Ekki endurbyggja neitt. Þetta er afritun.
- Ekki snerta upprunarepo-in — lesa, ekki skrifa.
- Ekki afrita Friends-HANDRITIN sjálf (submodule-in). Aðeins tölurnar.
  Höfundarétturinn er óútkljáður í issue #3.

Lokið: segðu heildarstærð þess sem fór í git, og staðfestu að sha256 hverrar
skráar stemmi við provenance.
```

---

## 5. Prompt: P0.2 — lesa viðmiðstölur úr byggðu síðunni

**Persóna:** `--persona-analyzer` · **Issue:** #30 · ✅ **Lokið** — `vidmid/lesa-tolur`

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #30, seinni hluti — búa til vélleshæft viðmið úr byggðu gömlu
síðunni sem P0.1 afritaði í docs/vidmid/vefur/ (28 HTML-skrár).

Af hverju: krafa verkefnisins er að nýja síðan sýni SÖMU tölur og sú gamla.
Í dag eru þær tölur aðeins til sem texti inni í 28 HTML-skrám. Próf geta ekki
borið sig saman við HTML.

Verkið:
- Lestu hverja síðu í docs/vidmid/vefur/ og dragðu út hverja tölu sem er
  efnisleg niðurstaða (ekki blaðsíðutöl, ekki dagsetningar í fæti).
- Skrifaðu docs/vidmid/vidmid.json: fyrir hverja tölu — hvaða síða, hvaða
  samhengi (fyrirsögn eða málsgrein), gildið sjálft, og eining ef við á.
- Skrifaðu docs/vidmid/vidmid.md: sama efni í töflu sem manneskja les.

Tölur sem ÞEGAR eru staðfestar og verða að koma fram (úr
docs/vidmid/phoebe-stats/_meta.json og provenance-skránum):
  jarðskjálftar: 334 atburðir, 61 dagur
  handritsskrár: 227, þættir: 236
  textablokkir alls: 70.553, tilsvör: 61.161
  sviðsfyrirsagnir: 4.055, sviðsleiðbeiningar: 3.259
  óflokkað: 2.078 (2,95%)
  línur á persónu: Phoebe 7.483 · Rachel 9.259 · Ross 9.058 ·
                   Chandler 8.446 · Monica 8.395 · Joey 8.183

Aðferð:
- Notaðu Python-staðalsafnið (html.parser). Ekki bæta við bs4 eða lxml.
- Sértu í vafa um hvort tala sé niðurstaða eða skraut: taktu hana með og
  merktu hana „óvisst". Betra að hafa of mikið en að missa tölu.
- Ef sama tala birtist á fleiri en einni síðu: skráðu báða staði. Ósamræmi
  MILLI síðna í gamla verkefninu er sjálfstæð niðurstaða — skráðu það
  sérstaklega í issue-ið.

Lokið: hversu margar tölur fundust, hvaða síður reyndust tölulausar, og hvort
þú fannst ósamræmi milli síðna.
```

---

## 6. Prompt: P0.3 — frysta hrágögn og opna .gitignore

**Persóna:** `--persona-devops` · **Issue:** #2 · ✅ **Lokið** — `gagnabjorgun/frysta-hragogn`

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #2 — frysta hrágögnin svo allt sé endurskapanlegt án nets.

P0.1 bjargaði mbl-eintakinu. Þrjú söfn eru eftir:

1. Jarðskjálftar og Hagstofan — afritaðu ÓBREYTT úr
   ~/PycharmProjects/idn302g-2026-team-friends-thesveinn/data/raw/
   (vedur-quakes/ og hagstofan/, báðar með provenance.json) → data/raw/

2. Veðurstöðvar — EKKERT eintak er til; hráa svarið var aldrei vistað.
   Sæktu EITT eintak af https://api.vedur.is/weather/stations og vistaðu
   óbreytt í data/raw/vedurstodvar/ með provenance.
   Skráðu SKÝRT að þetta sé NÝ söfnun og að tölurnar víki því frá gömlu
   síðunni — sem sótti gögnin upp á nýtt í hverri byggingu og var því aldrei
   stöðug. Berðu saman við docs/vidmid/generated/vedurstofa-*.md og skráðu
   muninn.

3. TMDB — ekkert eintak á disknum (aðeins README eftir).
   Þarf TMDB_TOKEN úr .env. Sé lykillinn ekki til: SLEPPTU þessu, skráðu í
   issue-ið að það vanti, og haltu áfram. Ekki stöðva allt verkið á því.
   docs/vidmid/generated/phoebe-tmdb-summary.md geymir samantektina þótt
   skyndiminnið sé horfið.

Kröfur (regla 4):
- Svarið vistað óbreytt ÁÐUR en nokkuð er unnið úr því.
- provenance.json fyrir hvert safn: þjónusta, slóð, aðferð, allar breytur,
  fetched_at_utc, User-Agent sem auðkennir verkefnið, SHA-256, svarstærð,
  leyfi ef þekkt. Sniðið í data/raw/vedur-quakes/provenance.json er fyrirmyndin.
- User-Agent má EKKI innihalda persónulegt netfang — repo-ið er opið.
- Lykill fer aldrei í úttak, logg né git.
- Opnaðu undanþágur í .gitignore fyrir hvert safn.
- data/raw/README.md: söfnin, stærð þeirra, hvaða skrifta les hvert.

Lokið: heildarstærð frosinna gagna, staðfesting á að sha256 stemmi alls
staðar, og listi yfir það sem ekki tókst að frysta og af hverju.
```

---

## 7. Prompt: P1.1 — migration-keyrari og tengilag

**Persóna:** `--persona-backend` · **Issue:** #5 · ✅ **Lokið** — `gagnagrunnur/migration-keyrari`

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #5 — migration-keyrari og tengilag. Þetta er grunnurinn sem fimm
önnur verk (#6–#10) bíða eftir, svo það þarf að vera traust.

Þú þarft ENGIN gögn fyrir þetta verk — aðeins src/sql/migrations/001_gagnasofnun.sql
sem þegar er í trénu. Vinnið samhliða gagnabjörguninni.

Smíðið:
- src/python/gagnagrunnur/keyrari.py
    Les src/sql/migrations/*.sql í númeraröð, keyrir þær sem eftir eru og
    skráir hverja í töfluna schema_migrations: númer, heiti, SHA-256 af
    innihaldi, tímastimpill.
    STÖÐVAST með skýrri villu ef SHA-256 á ÞEGAR KEYRÐRI migration hefur
    breyst — það þýðir að einhver breytti sögu og grunnurinn er ekki lengur
    endurbyggjanlegur (regla 5).
- src/python/gagnagrunnur/tenging.py
    Opnar data/db/rannsokn.sqlite, kveikir á PRAGMA foreign_keys = ON,
    skilar context manager sem gerir commit/rollback rétt.
- scripts/endurbyggja-grunn.sh
    Eyðir grunninum og byggir hann frá grunni úr data/raw/ + migrations.
    Þetta er PRÓFIÐ á reglu 5: grunnurinn er afleiða, ekki frumgagn.
- Tengið hlada() í src/python/main.py við keyrarann (í stað NotImplementedError).

Öryggisregla sem ekki er samningsatriði (regla 5):
  Allar fyrirspurnir með breytum: cur.execute(sql, (gildi,))
  ALDREI f-strengur eða + inn í SQL. Þetta gildir líka um töflunöfn sem koma
  að utan — þar er hvítlisti, ekki strengjasamsetning.

Próf í tests/ fyrir:
  - sama migration keyrð tvisvar breytir engu
  - breytt migration sem þegar var keyrð stöðvar keyrslu
  - breytufyrirspurn kemst óskemmd í gegn
  - endurbyggja-grunn.sh skilar sama grunni tvisvar í röð

Eingöngu Python-staðalsafnið (sqlite3). Engir nýir pakkar.

Lokið: staðfestu að endurbyggja-grunn.sh gefi sama grunn tvisvar, og að
data/db/ sé enn utan git.
```

---

## 8. Prompt: P1.2–P1.6 — schema og hleðsla (fimm pakkar)

**Persóna:** `--persona-backend` · **Issues:** #6–#10 · 🟢 **P1.2–P1.5 mega hefjast** · P1.6 bíður P0.5

Sama form á öllum fimm; skiptið aðeins út efnishlutanum. **Fimm agentar mega
vinna þessa samtímis** — þeir snerta sitt hvora migration og sitt hvora töflu.

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #<N> — schema og hleðsla fyrir <gagnasafn>.

Migration-keyrarinn úr #5 er til; notaðu hann, ekki þinn eigin.
Hrágögnin eru fryst í data/raw/<mappa>/ — lestu þau, breyttu þeim aldrei.
Viðmiðstölurnar eru í docs/vidmid/ — niðurstaðan þín verður borin saman
við þær í #16.

Smíðið:
- src/sql/migrations/<NÚMER>_<HEITI>.sql — notaðu NÁKVÆMLEGA númerið og heitið
  sem pakkanum þínum er úthlutað í töflunni hér að neðan. Skráin ber athugasemd
  um hvaðan gögnin koma og hvaða leyfi gildir (regla 5).
- Hleðslu í src/python/vinnsla/ sem SANNREYNIR hverja færslu áður en hún fer
  inn. Frávik STÖÐVA keyrsluna — færsla má aldrei hverfa hljóðlega (regla 6).
- Próf sem staðfesta fjöldatölurnar hér að neðan.

<EFNISHLUTI — sjá issue-ið sjálft fyrir töflur, dálka og sannreyningar>

Lokið: fjöldatölur úr grunninum bornar saman við væntu gildin í issue-inu,
og staðfesting á að engin fyrirspurn noti strengjasamsetningu.
```

Úthlutuð migration-númer og væntu gildin sem hver pakki á að hitta:

| Pakki | Issue | Gagnasafn | Migration | Verður að standast |
|---|---|---|---|---|
| P1.2 | #6 | Jarðskjálftar | `002_jardskjalftar.sql` | 334 atburðir · 61 dagur · enginn `magnitude_type` `NULL` |
| P1.3 | #7 | Hagstofan | `003_hagstofan.sql` | fjöldi gilda = margfeldi víddastærða |
| P1.4 | #8 | Veðurstöðvar | `004_vedurstodvar.sql` | fjöldi stöðva = fjöldi í frosna svarinu |
| P1.5 | #9 | mbl.is | `005_mbl-regex.sql` | öll fimm svör æfingarinnar fást úr SQL |
| P1.6 | #10 | Friends | `006_friends.sql` | 227 skrár · 236 þættir · 61.161 lína · 2,95% óflokkað |

Númerin eru frátekin fyrir fram því pakkarnir fimm eru unnir samtímis. Taki
tveir agentar sama númerið stöðvar keyrarinn úr #5 keyrsluna með villunni
„Tvær migrations bera númerið 00N — númer verða að vera einkvæm". Enginn
endurnúmerar pakka annars, og `001_gagnasofnun.sql` stendur óhreyfð: migration
sem hefur verið keyrð er aldrei breytt (regla 5).

---

## 9. Bylgjur 2–4

Prompt fyrir þessa pakka eru **ekki skrifuð enn, af ásettu ráði**: bylgja 3
veltur á myndritaákvörðuninni (#17) og bylgja 2 á höfundaréttarákvörðuninni
(#3). Prompt skrifað núna yrði rangt um leið og ákvörðun fellur.

Þegar P0.5 og P0.6 eru afgreidd fást prompt fyrir næstu bylgju á sama sniði.

Það sem gildir þó þegar: **hver pakki í töflunni í kafla 3 er ein lota fyrir
einn agent.** Þess vegna er #14 klofið í fjóra (3.270 línur) og #24 í þrjá.

---

## 10. Samhliða agentar — ein mappa á hvern

**Ekki keyra tvo agenta í sömu vinnumöppu.** Git geymir eina `HEAD`, eitt
index og eitt vinnutré á hverja möppu. Tveir agentar í sömu möppu deila þeim
öllum: sá seinni sér breytingar þess fyrri sem sínar eigin og sópar þeim inn
í sitt commit. Þá verður eitt PR úr tveimur verkum og reglan „eitt commit =
ein rökrétt breyting" (regla 7) er rofin án þess að nokkur taki eftir því.

Lausnin er `git worktree`: ein mappa á hvern agent, öll með sömu sögu.

```sh
# Úr rót verkefnisins, einu sinni fyrir hvern pakka:
git worktree add ../uv-P0.2 -b vidmid/lesa-tolur      main
git worktree add ../uv-P0.3 -b gagnabjorgun/frysta-hragogn main
git worktree add ../uv-P2.1 -b sofnun/http-lag         main
git worktree add ../uv-P3.1 -b vefur/beinagrind        main
```

Hver agent fær **eina** þessara mappa og fer aldrei út fyrir hana. Þegar PR er
samþykkt:

```sh
git worktree remove ../uv-P0.2
```

Bætið þessu aftast í hausinn (kafli 2) þegar fleiri en einn agent er að störfum:

```text
  - Þú vinnur EINGÖNGU í möppunni sem þér var úthlutað. Ekki `git checkout`
    yfir á aðra grein, ekki `git add -A` (það sópar upp verkum annarra
    agenta), og ekki snerta skrár utan þíns pakka.
  - Staðfestu með `git status` ÁÐUR en þú committar að ekkert sé í
    staging sem tilheyrir ekki þínu verki.
```

---

## 11. Prompt: P0.4 — heimildir og aðferðafræði

**Persóna:** `--persona-scribe=en` · **Issue:** #4 · ✅ **Lokið** — `skjolun/heimildir-adferdafraedi`

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #4 — skrá heimildir, aðferðafræði og takmarkanir.

Regla 8 krefst þess að sérhver tala á vefsíðunni eigi sér rekjanlega leið
aftur í hrágögn, og að aðferðafræði sé skráð jafnóðum en ekki í lokin. Þetta
verk leggur grunninn ÁÐUR en nokkur tala er birt.

Gögnin eru fryst í data/raw/ með provenance.json fyrir hvert safn (#2, #30).
Lestu þær skrár — ekki giska á breytur eða dagsetningar.

docs/heimildir.md — ein færsla á hvert gagnasafn:
  þjónusta, full slóð, sóknardagsetning, leyfi, tengill í skjölun
  þjónustunnar. Jarðskjálftagögnin eru CC BY 4.0 og það VERÐUR að koma fram.

docs/adferdafraedi.md — hvernig hvert safn var afmarkað og AF HVERJU:
  - Jarðskjálftar: af hverju Reykjanes, af hverju 1.11.2023–1.1.2024,
    af hverju stærð 3–7 og dýpt 0–50 km, af hverju aðeins yfirfarnir
    SIL-atburðir.
  - Hagstofan: af hverju innritunarár 2017 og tímapunkturinn n+3.
  - Friends: af hverju delvinso en ekki fangj (brotin HTML-bygging í
    þáttum 0911 og 0915 var löguð þar), og hvaða tvær skrár eru
    undanskildar (0423uncut.html, 07outtakes.html).

Takmarkanakafli — þetta er skylduefni, ekki viðbót (regla 8 segir að
takmarkanir séu birtar á síðunni, ekki faldar). Hann fer óbreyttur inn á
web/sidur/adferdafraedi.html í P3.11, svo orðaðu hann fyrir LESANDA en ekki
fyrir kennara:
  - Úrtakið nær yfir 61 dag í kringum þekkta atburðahrinu. Hlaupandi
    meðaltal reiknað úr hrinu gerir nánast hvern dag „yfir meðallagi" —
    rólegt viðmiðunartímabil vantar.
  - Stærðarkvarðar (Mlw, Mw) mega ekki blandast í sama miðgildi.
  - Engin fylgni sem reiknuð er í verkefninu er orsakasamband.
  - Veðurstöðvarnar og mbl-eintakið eru frosin, ekki lifandi staða.
  - Handritin eru afrit aðdáenda, ekki opinber handrit — innsláttarvillur
    og ósamræmi í nafnritun eru til staðar.

Tengdu hvert gagnasafn við þá skriftu sem les það og þá síðu sem birtir það,
svo leiðin frá tölu að hrágagni sé rekjanleg í BÁÐAR áttir.

Ekki skrifa neina fullyrðingu sem þú hefur ekki heimild fyrir í
data/raw/*/provenance.json eða docs/vidmid/. Sértu í vafa: skrifaðu
„óstaðfest" og skráðu spurninguna í issue-ið.

Lokið: hvaða söfn hafa fulla færslu og hvaða upplýsingar vantar enn.
```

---

## 12. Prompt: P2.1 — sameiginlegt HTTP-lag

**Persóna:** `--persona-backend` · **Issue:** #12 · ✅ **Lokið** — `sofnun/http-lag`

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #12 — eitt HTTP-lag fyrir alla gagnasöfnun.

Þú þarft ENGIN gögn og ekkert annað verk fyrir þetta. Vinnið samhliða öðrum.

Vandamálið: fjórar skriftur í upprunaverkefninu senda vefbeiðnir og hver
þeirra útfærir User-Agent, endurtilraunir og provenance-skráningu upp á eigin
spýtur. Regla 4 gerir sömu kröfur til þeirra allra, svo þær eiga heima á
einum stað.

src/python/sofnun/http.py skal sjá um:
  - User-Agent sem AUÐKENNIR verkefnið og inniheldur tengilið (regla 4).
    Tengiliðurinn kemur úr umhverfisbreytu, ekki harðkóðaður — repo-ið er
    opið og persónulegt netfang á ekki að fara í kóða.
  - Hraðatakmörkun: skilgreind lágmarksbið milli kalla á sömu þjónustu.
  - Endurtilraunir með vaxandi bið og þaki á fjölda tilrauna.
  - Allar beiðnir í try/except með skiljanlegri villu. Aldrei þögul villa
    (reglur 4 og 6).
  - Sjálfvirka provenance-ritun: þjónusta, slóð, aðferð, breytur,
    fetched_at_utc, User-Agent, SHA-256, svarstærð.
  - Skrifa svarið ÓBREYTT í data/raw/<þjónusta>/ með tímastimpli ÁÐUR en
    nokkuð er unnið úr því (regla 4).
  - Athuga data/raw/ fyrst og sleppa kalli ef sama gagn er þegar til —
    regla 4 bannar að sækja sömu gögn tvisvar að óþörfu.

Lyklar koma EINGÖNGU úr umhverfisbreytum eða .env, aldrei úr kóða, og fara
aldrei í úttak, logg eða villuskilaboð.

Eingöngu Python-staðalsafnið (urllib.request). Gömlu skriftunum tókst það og
engin ástæða er til að bæta við pakka.

Sniðið á provenance.json sem þegar er í data/raw/vedur-quakes/ er fyrirmyndin
— lestu það og skrifaðu samhæft, ekki nýtt snið.

Athugið: P0.3 sækir veðurstöðvarnar einu sinni með einfaldri beiðni. Það verk
er ekki að bíða eftir þessu lagi og þið eigið ekki að samræma ykkur — þetta
lag er fyrir #13 og áfram.

Próf: keyra án nets, með svörum úr prófgögnum. Prófið að endurtilraunir
stöðvist, að þögul villa sé ómöguleg og að lykill komist aldrei í provenance.

Lokið: staðfestu að `grep -ri "token\|api_key\|secret" src/` sýni engan lykil,
aðeins lestur úr umhverfi.
```

---

## 13. Prompt: P3.1 — beinagrind og sjónrænt kerfi

**Persóna:** `--persona-frontend` · **Issue:** #18 · 🟢 **Má hefja núna**

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #18 — sameiginleg beinagrind allra síðna og sjónræna kerfið.

Þú þarft ENGIN gögn fyrir þetta verk. Vinnið samhliða öðrum.

Beinagrindin er ÞEGAR TIL í web/ (tokens.css, base.css, layout.css,
components/, valmynd.js og fjórar HTML-síður). Verkið er að fullgera hana
fyrir NÍU síður og staðfesta að hún standist reglurnar. Ekki byrja upp á
nýtt — byggið á því sem er.

Síðurnar níu verða:
  index.html og undir sidur/: skjalftavaktin, hagstofan, vedurstodvar,
  mbl-regex, phoebe-tolfraedi, phoebe-central-perk, phoebe-tmdb,
  adferdafraedi.
Búið til beinagrind hverrar þeirra með réttum haus, fæti, brauðmylsnu og
tómum efnishluta sem síðuverkin (P3.4–P3.11) fylla.

Bygging (regla 2 — engar undantekningar):
  - Ekkert <style>, ekkert style="...", enginn kóði inni í <script>,
    ekkert onclick. Öll <script> með defer.
  - Sami haus og fótur á ÖLLUM síðum, á sama stað og í sömu röð.
  - Núverandi síða sjónrænt merkt OG með aria-current="page".
  - Brauðmylsna á öllum undirsíðum.
  - Hver síða svarar þremur spurningum efst: Hvar er ég? Hvað er hér?
    Hvert get ég farið næst?
  - Hámark 3 smellir í hvaða efni sem er frá forsíðu — teiknið leiðina upp
    og staðfestið hana.

Sjónrænt kerfi (regla 3.1):
  - Staðfestið að ENGINN harðkóðaður litur eða px-tala sé utan tokens.css.
  - Hámark 2 leturfjölskyldur, stærðarskali með föstum þrepum.
  - Bilaskali á 4px eða 8px grunneiningu; öll bil margfeldi af honum.
  - Dökkt þema með prefers-color-scheme, leyst með því að ENDURSKILGREINA
    tokens — ekki með nýjum stílum.

Merkingarbært HTML (regla 3.3):
  - <html lang="is">, <header> <nav> <main> <article> <footer>,
    ein <h1> á síðu, fyrirsagnir í réttri röð án stökka.
  - Sjáanleg :focus umgjörð alls staðar. Aldrei outline: none án betri
    staðgengils.
  - „Fara beint í efni"-tengill fremst.

Skjáaðlögun (regla 3.5):
  - Mobile-first, min-width fyrirspurnir upp á við.
  - Virkar frá 320px, ekkert lárétt skrun.
  - Smellifletir minnst 44x44px.

Ein eining = ein CSS-skrá í components/ + ein JS-skrá ef hún þarf hegðun.

Prófið með SLÖKKT á JavaScript: valmyndin verður að vera rötunarhæf og efnið
læsilegt. Það er hörð krafa (regla 3.4), ekki markmið.

Lokið: staðfestu 320px, lyklaborðsrötun, JS-lausa hegðun og að console sé
villulaus á öllum níu síðunum.
```

---

## 14. Prompt: P1.7 — endurnýtanlegar fyrirspurnir

**Persóna:** `--persona-backend` · **Issue:** #11 · ⏸ **Blokkað af P1.2–P1.6**

```text
[HAUSINN úr kafla 2 hér]

Verk: issue #11 — safna fyrirspurnunum sem síðurnar byggja á í
src/sql/queries/.

Regla 5 segir að fyrirspurnir eigi að geymast, ekki bara svörin. Í dag lægju
þær faldar inni í Python-strengjum; hér verða þær lesanlegar, endurnýtanlegar
og prófanlegar.

Ein .sql-skrá á hverja fyrirspurn, með athugasemd efst: hvaða spurningu hún
svarar og hvaða síða notar hana.

Að minnsta kosti þessar:
  - Daglegur fjöldi jarðskjálfta yfir allt tímabilið, MEÐ dögum sem hafa
    núll (LEFT JOIN á earthquake_days). Fyrirspurn sem telur aðeins raðir í
    earthquakes sleppir þeim og sýnir ranga tímaröð.
  - Miðgildi og dreifing stærðar INNAN hvers stærðarkvarða
    (GROUP BY magnitude_type) — aldrei eitt meðaltal yfir alla.
  - Hlaupandi 7 daga meðaltal:
    AVG(...) OVER (ORDER BY utc_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
  - Röðun persóna eftir plássi: RANK() OVER (PARTITION BY season)
  - interaction_lift sem CTE í læsilegum þrepum, ekki einni langri fyrirspurn.

Python-lagið les þessar skrár í stað þess að geyma SQL í strengjum. Breytur
fara áfram inn sem breytur (regla 5): skráin geymir ?-staðgengla, ALDREI
innsett gildi.

Próf sem keyra hverja fyrirspurn á grunninum og staðfesta að hún skili röðum.

Lokið: staðfestu að engin SQL-strengjasamsetning sé eftir í Python-kóðanum og
að hver fyrirspurn beri athugasemd um hvaða spurningu hún svarar.
```

---

## 15. Staða P1.2–P1.5 — hálfnuð vinna sem bíður

Fjórir agentar unnu þessa pakka samtímis 2026-09-24 og **stöðvuðust allir á sömu
mínútu** þegar mánaðarþak reikningsins náðist (HTTP 429). Vinnan var vistuð og
ýtt upp, en **ekkert þeirra er tilbúið til sameiningar.**

| Grein | Issue | Migration | Einingar | Próf | Keyrt frá enda til enda |
|---|---|---|---|---|---|
| `sql/skjalftar-schema` | #6 | `002` ✅ | 4 | ✅ | ❌ |
| `sql/hagstofan-schema` | #7 | `003` ✅ | 2 | ❌ | ❌ |
| `sql/vedurstodvar-schema` | #8 | `004` ✅ | 3 + fyrirspurn | ❌ | ❌ |
| `sql/mbl-regex-schema` | #9 | `005` ✅ | 4 | ❌ | ❌ |

Staðfest um alla fjóra: allar `.py`-skrár þýðast, migration-númer eru rétt og
aðgreind, og engin eining rekst á nafn annarrar.

### Hvað vantar, grein fyrir grein

**Allar fjórar:** keyra `python3 -m unittest discover -s tests` og staðfesta að
öll próf repo-sins séu græn — ekki bara þau nýju. Keyra hleðsluna á frosnu
gögnunum og bera niðurstöðuna saman við `docs/vidmid/vidmid.json`.

- **#6 skjálftar** — lengst komin. Prófin eru skrifuð en ókeyrð. Staðfestið
  334 atburði og 61 dag.
- **#7 Hagstofan** — **`hagstofan_jsonstat.py` er 347 línur og brýtur reglu 6.**
  Kljúfið hana áður en lengra er haldið. Engin próf skrifuð. Staðfestið 36 gildi
  = margfeldi `size` = [1, 1, 3, 1, 4, 3].
- **#8 veðurstöðvar** — engin próf. Staðfestið 778 stöðvar og 343 með `NULL`
  lokaár. `src/sql/queries/vedurstodvar-siur.sql` varð til hér, á undan #11 —
  gætið þess að hún rekist ekki á það verk.
- **#9 mbl** — engin próf. Agentinn náði að staðfesta að **öll fimm mynstrin
  skila sömu niðurstöðu og viðmiðið** áður en hann stöðvaðist; sú staðfesting
  er ekki í prófi og þarf að endurgera.

### Að taka upp þráðinn

Sækið greinina, lesið commitið (það er merkt ÓKLÁRAÐ), og haldið áfram með
promptinu úr kafla 8 auk þess sem hér er talið. Ekki byrja upp á nýtt —
migration og einingar eru þegar skrifaðar.
