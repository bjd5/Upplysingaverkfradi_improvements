# Viðmiðstölur gamla verkefnisins

Hver tala sem byggða gamla síðan birtir, vélleshæf í [`vidmid.json`](vidmid.json) og læsileg hér. Þetta er svarið við spurningunni sem viðmiðið er til fyrir: **sýnir nýja síðan sömu tölur?** (sjá [`README.md`](README.md) og [`../endurbygging.md`](../endurbygging.md), kafla 2).

Afleidd skrá. Uppfært 2026-09-24T11:39:24Z af `src/python/vidmid/tolur.py`; **ekki handbreytt** (regla 10).

## 1. Umfang

| Mæling | Fjöldi |
|---|---:|
| Síður lesnar | 28 |
| Síður með tölu í HTML | 26 |
| Tölur alls | 1391 |
| **Efnislegar niðurstöður** | **445** |
| Tölur sem eru ekki niðurstöður | 946 |

Efnisleg niðurstaða = tala í fyrirsögn, málsgrein, lista, töflu eða úttaki. Tölur inni í kóðalistun, auðkenni (`0405`), issue-tilvísanir (`#14`), ISO-dagsetningar og CSS-gildi eru skráðar áfram í `vidmid.json` en hafa `visst: false` — betra að hafa of mikið en að missa tölu.

**Eftir flokki:** tafla 246, malsgrein 168, listi 19, fyrirsogn 12

**Eftir tegund:** heiltala 316, desimal 62, hlutfall 30, thusund 25, bil 9, hlutfallstala 3

## 2. Síður án efnislegrar tölu

| Síða | Ástæða |
|---|---|
| `friends/uppahalds-video.html` | engin tala í HTML-textanum |
| `lotur/git-ai-reproducible/git.html` | aðeins tölur úr kóða, auðkenni eða dagsetningar |
| `reflections/ottar.html` | aðeins tölur úr kóða, auðkenni eða dagsetningar |
| `reflections/sveinn.html` | engin tala í HTML-textanum |
| `tokens/index.html` | tölurnar reiknaðar í vafra — sjá kafla 4 |

## 3. Staðfestar tölur

Tölurnar sem verklýsing P0.2 telur upp. `Í HTML` segir hvort talan stendur sem texti í byggðu síðunni; `Úr gagnaskrá` hvort hún stemmir við `friends/phoebe-stats/_meta.json`.

| Heiti | Gildi | Eining | Í HTML | Úr gagnaskrá | Stemmir |
|---|---:|---|:-:|---:|:-:|
| jarðskjálftar | 334 | atburðir | ✅ | — | ✅ |
| dagar í glugganum | 61 | dagar | ✅ | — | ✅ |
| handritsskrár | 227 | skrár | ✅ | 227 | ✅ |
| þættir | 236 | þættir | ✅ | 236 | ✅ |
| textablokkir alls | 70553 | textablokkir | ✅ | 70553 | ✅ |
| tilsvör | 61161 | tilsvör | ✅ | 61161 | ✅ |
| sviðsfyrirsagnir | 4055 | sviðsfyrirsagnir | — | 4055 | ✅ |
| sviðsleiðbeiningar | 3259 | sviðsleiðbeiningar | — | 3259 | ✅ |
| óflokkað | 2078 | textablokkir | ✅ | 2078 | ✅ |
| óflokkað hlutfall | 2.95 | % | ✅ | 2.95 | ✅ |
| línur Phoebe | 7483 | línur | — | 7483 | ✅ |
| línur Rachel | 9259 | línur | — | 9259 | ✅ |
| línur Ross | 9058 | línur | — | 9058 | ✅ |
| línur Chandler | 8446 | línur | — | 8446 | ✅ |
| línur Monica | 8395 | línur | — | 8395 | ✅ |
| línur Joey | 8183 | línur | — | 8183 | ✅ |

## 4. Síður sem reikna tölurnar í vafra

Tvær síður birta engar tölur í HTML-inu; þær reikna þær í JavaScript þegar lesandinn opnar síðuna. **Fyrir þær er gagnaskráin viðmiðið, ekki HTML-ið.** Þetta er ástæða þess að sex staðfestar tölur í kafla 3 hafa `—` í `Í HTML`.

### `friends/phoebe-statistics.html`

Myndrit og töflur eru byggð með Observable Plot í vafranum úr þessum sjö skrám. Tölurnar sem lesandinn sér standa hvergi í HTML-inu; þar er aðeins OJS-kóðinn sem reiknar þær.

Gagnaskrár:

- `friends/phoebe-stats/_meta.json`
- `friends/phoebe-stats/phoebe-extra-stats.json`
- `friends/phoebe-stats/phoebe-top-talkers.json`
- `friends/phoebe-stats/phoebe-screentime-by-season.json`
- `friends/phoebe-stats/phoebe-mentions-by-season.json`
- `friends/phoebe-stats/phoebe-per-episode.csv`
- `friends/phoebe-stats/phoebe-distinctive-words.csv`

### `tokens/index.html`

Teljararnir eru summaðir í JavaScript úr CSV sem Quarto bakaði inn í skjalið á byggingartíma. Engin tala á síðunni stendur í HTML-textanum.

Gagnaskrár:

- `<script type="text/plain" id="tk-gogn"> (innbakað CSV)`

## 5. Ósamræmi milli síðna

Viðmiðið er samsett úr þremur Quarto-byggingum á tveimur dögum og fjórar síður koma úr grein sem rataði aldrei á `main` (sjá [`README.md`](README.md), kafla 2). Ósamræmi er því vænt — og sjálfstæð niðurstaða. Hvert atriði er sannreynt, ekki ætlað.

### Fjöldi skráa sem geyma tvöfalda þætti

**Alvarleiki:** 🔴 hátt

| Staður | Það sem hann segir |
|---|---|
| `friends/phoebe-statistics.html` | „níu skráanna geyma tvöfalda þætti“ |
| `friends/index.html` | „223 með stöku þáttanúmeri og sex sem ná yfir tvöfalda þætti eða sérefni“ |
| `phoebe-central-perk.html` | „Fjórar skrár sameina tvöfalda þætti“ |

**Niðurstaða.** Þrjár tölur — 9, 6 og 4 — um sama hlutinn. Aðeins 9 stemmir: `_meta.json` telur níu skrár í `double_episode_files`, og 227 + 9 = 236. `friends/index.html` telur aðeins skrárnar sem hafa bandstrik í nafni (0212-0213, 0615-0616, 0923-0924, 1017-1018) auk tveggja sérefnisskráa; `phoebe-central-perk.html` aðeins bandstriksskrárnar fjórar. Fimm skrár (0423, 0523, 0624, 0723, 0823) geyma tvöfalda þætti þótt nafnið sýni aðeins eitt þáttanúmer.

**Sannreynt með.** `len(conventions.double_episode_files) == 9` og `transcript_files_used + 9 == aired_episodes_covered` í `_meta.json`

**Fyrir endurbygginguna.** Reikningur `friends/index.html` gengur ekki upp: 223 stakar + 4 tvöfaldar skrár gefa 231 þátt, ekki 236. Nýja síðan á að nota 218 stakar + 9 tvöfaldar = 236 og aðeins eina orðanotkun.

### Orðið „lína“ merkir þrennt

**Alvarleiki:** 🔴 hátt

| Staður | Það sem hann segir |
|---|---|
| `friends/phoebe-statistics.html` | 61 161 er „tilsvör“ af 70 553 textablokkum |
| `lotur/regex/index.html` | „Þátta 61.161 línur úr 70.553 textablokkum“ |
| `friends/index.html` | „delvinso gefur upp 236 þætti og um 69.500 línur“ |

**Niðurstaða.** Sama tala (61 161) heitir „tilsvör“ á einni síðu og „línur“ á annarri, og á þriðju síðu er „línur“ 69.500 — tala delvinso sem telur líka sviðslýsingar, leikaraskrá og höfundatexta. `friends/index.html` skýrir sína tölu sjálf, svo það frávik er skjalfest; hin tvö orðanotin standa óskýrð hlið við hlið.

**Sannreynt með.** 61161 finnst með `eining='línur'` á `lotur/regex/index.html` og sem „tilsvör“ á `friends/phoebe-statistics.html`; 69500 aðeins á `friends/index.html`

**Fyrir endurbygginguna.** Nýja síðan þarf eitt orð á hvert hugtak: tilsvör (61 161), textablokkir (70 553), og tala delvinso sé kölluð það sem hún er.

### phoebe-top-talkers.json er í tveimur röðum

**Alvarleiki:** 🟠 miðlungs

| Staður | Það sem hann segir |
|---|---|
| `docs/vidmid/vefur/friends/phoebe-stats/phoebe-top-talkers.json` | non_friend_characters[1]=frank, [2]=david, [16]=man, [17]=grandmother |
| `docs/vidmid/phoebe-stats/phoebe-top-talkers.json` | non_friend_characters[1]=david, [2]=frank, [16]=grandmother, [17]=man |

**Niðurstaða.** Gildin eru eins; röðin er ekki. `frank` og `david` eru bæði með `adjacent_turns=174`, `man` og `grandmother` bæði með 32. Röðunin í gömlu greiningunni brýtur jafntefli án fasts viðmiðs, svo tvær keyrslur á sömu gögnum skila ólíkri röð. Myndritið í byggðu síðunni sýnir því aðra röð en nýjasta úrvinnslan.

**Sannreynt með.** Fletjuð lyklakort skránna tveggja: 479 lyklar í báðum, 16 ólíkir, allir innan þessara fjögurra sæta

**Fyrir endurbygginguna.** P2.7 verður að raða með föstu jafnteflisviðmiði (t.d. nafni) annars sýnir nýja síðan „aðra“ niðurstöðu sem er sama niðurstaðan. P2.8 á að bera saman mengi, ekki röð, nema röðin sé bundin.

### _meta.json er í tveimur eintökum frá tveimur keyrslum

**Alvarleiki:** ⚪ skráð

| Staður | Það sem hann segir |
|---|---|
| `docs/vidmid/vefur/friends/phoebe-stats/_meta.json` | generated_utc = 2026-09-16T14:56:00Z |
| `docs/vidmid/phoebe-stats/_meta.json` | generated_utc = 2026-09-17T09:47:09Z |

**Niðurstaða.** Eintökin eru eins að öðru leyti en tímastimplinum — allar tölur stemma. Viðvörunin í `README.md` (kafli 2) um að síðan gæti víkið frá `_meta.json` á því ekki við um þessar tölur.

**Sannreynt með.** diff á skránum gefur aðeins línuna `generated_utc`

**Fyrir endurbygginguna.** Staðfestu tölurnar í kafla 3 má nota án þess að velja milli eintaka.

### Talan 236 var eitt sinn birt sem skráafjöldi

**Alvarleiki:** ⚪ skráð

| Staður | Það sem hann segir |
|---|---|
| `lotur/git-ai-reproducible/agents.html` | „Fyrsta útgáfa forsíðunnar sagði … að þættirnir væru 236 … skrárnar eru 229, ekki 236“ |
| `reflections/bjorn.html` | „Talan 236 og orðið „replikka“ stóðu bæði á síðunni eftir mína rýni“ |
| `friends/phoebe-statistics.html` | „227 skrár sem ná yfir 236 sýnda þætti“ |

**Niðurstaða.** 236 er réttur fjöldi sýndra þátta en var einhvern tíma birtur sem fjöldi handritsskráa. Gamla verkefnið skjalfestir sína eigin leiðréttingu á tveimur síðum.

**Sannreynt með.** 236 finnst á fjórum síðum; tvær þeirra lýsa því sem villu

**Fyrir endurbygginguna.** Nýja síðan má ekki nota 236 sem skráafjölda. Skrár = 227, þættir = 236.

## 6. Sama tala á fleiri en einni síðu

Verklýsingin krefst þess að báðir staðir séu skráðir. Hér eru aðeins tölur sem birtast á tveimur síðum eða fleiri; fullur listi með samhengi er í `vidmid.json` undir `samrit`.

| Gildi | Eining | Síður |
|---:|---|---|
| 2 | — | `capstone/earthquakes.html`, `friends/index.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/regex/index.html`, `lotur/regex/mbl.html`, `lotur/vefthjonustur/hagstofan.html`, `lotur/vefthjonustur/vedurstofan.html`, `phoebe-central-perk.html`, `project-management.html`, `team.html` |
| 1 | — | `capstone/earthquakes.html`, `friends/index.html`, `friends/phoebe-statistics.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/regex/mbl.html`, `lotur/vefthjonustur/hagstofan.html`, `lotur/vefthjonustur/vedurstofan.html`, `phoebe-central-perk.html`, `project-management.html`, `team.html` |
| 3.0 | — | `capstone/earthquakes.html`, `friends/phoebe-tribute.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/logic-sets/index.html`, `lotur/regex/mbl.html`, `lotur/vefthjonustur/hagstofan.html`, `lotur/vefthjonustur/vedurstofan.html`, `project-management.html`, `team.html` |
| 6 | — | `friends/phoebe-statistics.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/sql-advanced/index.html`, `lotur/storytelling/index.html`, `lotur/vefthjonustur/hagstofan.html`, `lotur/vefthjonustur/vedurstofan.html`, `project-management.html`, `team.html` |
| 4 | — | `capstone/earthquakes.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/regex/mbl.html`, `lotur/sql-basics/index.html`, `lotur/vefthjonustur/hagstofan.html`, `lotur/vefthjonustur/vedurstofan.html`, `project-management.html`, `team.html` |
| 5 | — | `friends/phoebe-statistics.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/regex/mbl.html`, `lotur/sql-advanced/index.html`, `lotur/vefthjonustur/hagstofan.html`, `project-management.html`, `team.html` |
| 236 | — | `friends/index.html`, `friends/phoebe-statistics.html`, `lotur/git-ai-reproducible/agents.html`, `reflections/bjorn.html` |
| 229 | — | `friends/index.html`, `friends/phoebe-statistics.html`, `lotur/git-ai-reproducible/agents.html`, `lotur/git-ai-reproducible/index.html` |
| 100 | % | `lotur/vefthjonustur/hagstofan.html`, `tokens/bjorn.html`, `tokens/ottar.html`, `tokens/sveinn.html` |
| 7 | — | `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/vefthjonustur/hagstofan.html`, `project-management.html`, `team.html` |
| 8601 | — | `tokens/bjorn.html`, `tokens/ottar.html`, `tokens/sveinn.html` |
| 200 | — | `lotur/regex/mbl.html`, `lotur/vefthjonustur/vedurstofan.html`, `phoebe-central-perk.html` |
| 61 | dagar | `capstone/earthquakes.html`, `lotur/sql-advanced/index.html`, `team.html` |
| 24 | — | `capstone/earthquakes.html`, `friends/index.html`, `phoebe-central-perk.html` |
| 15 | skrár | `friends/index.html`, `lotur/git-ai-reproducible/agents.html`, `lotur/git-ai-reproducible/index.html` |
| 9 | — | `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/vefthjonustur/hagstofan.html`, `lotur/vefthjonustur/vedurstofan.html` |
| 0.0 | — | `capstone/earthquakes.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/vefthjonustur/hagstofan.html` |
| 70553 | textablokkir | `friends/phoebe-statistics.html`, `lotur/regex/index.html` |
| 1017 | — | `friends/index.html`, `phoebe-central-perk.html` |
| 229 | skrár | `friends/index.html`, `phoebe-central-perk.html` |
| 64.1 | — | `capstone/earthquakes.html`, `team.html` |
| 63.7 | — | `capstone/earthquakes.html`, `team.html` |
| 61 | — | `index.html`, `lotur/sql-basics/index.html` |
| 50 | — | `lotur/regex/mbl.html`, `lotur/vefthjonustur/vedurstofan.html` |
| 43 | — | `capstone/earthquakes.html`, `lotur/regex/mbl.html` |
| 33 | — | `phoebe-central-perk.html`, `project-management.html` |
| 21 | — | `lotur/regex/mbl.html`, `lotur/vefthjonustur/vedurstofan.html` |
| 18 | — | `friends/index.html`, `lotur/git-ai-reproducible/reproducible-reports.html` |
| 17 | — | `lotur/regex/mbl.html`, `lotur/vefthjonustur/hagstofan.html` |
| 10 | — | `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/vefthjonustur/hagstofan.html` |

*4 fleiri í `vidmid.json`.*

## 7. Viðmið eftir síðum nýju síðunnar

Ein skrá á hverja síðu sem á að byggja (sjá [`../endurbygging.md`](../endurbygging.md), kafla 3).

| Síða nýju síðunnar | Viðmið | Tölur | Úr gömlu síðunum |
|---|---|---:|---|
| Skjálftavaktin — jarðskjálftar á Reykjanesi | [`vidmid/skjalftavaktin.md`](vidmid/skjalftavaktin.md) | 90 | `capstone/earthquakes.html` |
| Hagstofan — brautskráning af háskólastigi | [`vidmid/hagstofan.md`](vidmid/hagstofan.md) | 84 | `lotur/vefthjonustur/hagstofan.html` |
| Veðurstöðvar Veðurstofunnar | [`vidmid/vedurstodvar.md`](vidmid/vedurstodvar.md) | 41 | `lotur/vefthjonustur/vedurstofan.html` |
| mbl.is — reglulegar segðir á fréttaforsíðu | [`vidmid/mbl-regex.md`](vidmid/mbl-regex.md) | 60 | `lotur/regex/index.html`, `lotur/regex/mbl.html` |
| Phoebe — plass, nærvera og tengsl | [`vidmid/phoebe-tolfraedi.md`](vidmid/phoebe-tolfraedi.md) | 46 | `friends/index.html`, `friends/phoebe-statistics.html`, `friends/phoebe-tribute.html` |
| Phoebe — söngurinn í Central Perk | [`vidmid/phoebe-central-perk.md`](vidmid/phoebe-central-perk.md) | 30 | `phoebe-central-perk.html` |
| Síður utan umfangs nýju síðunnar | [`vidmid/utan-umfangs.md`](vidmid/utan-umfangs.md) | 94 | `index.html`, `lotur/git-ai-reproducible/agents.html`, `lotur/git-ai-reproducible/index.html`, `lotur/git-ai-reproducible/reproducible-reports.html`, `lotur/logic-sets/index.html`, `lotur/sql-advanced/index.html`, `lotur/sql-basics/index.html`, `lotur/storytelling/index.html`, `project-management.html`, `reflections/bjorn.html`, `team.html`, `tokens/bjorn.html`, `tokens/ottar.html`, `tokens/sveinn.html` |
