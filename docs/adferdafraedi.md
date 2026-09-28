# Aðferðafræði

Hvernig var hvert gagnasafn afmarkað, og af hverju? Skráð jafnóðum (regla 8).
Hvaðan gögnin komu er í [`heimildir.md`](heimildir.md).

Hver fullyrðing á sér stoð í `provenance.json` safnsins eða í
[`vidmid/`](vidmid/). Þar sem rökstuðning vantar stendur það berum orðum.

---

## 1. Afmörkun gagnasafnanna

### 1.1 Jarðskjálftar — Reykjanes, nóvember–desember 2023

**Rannsóknarspurningin (í mótun):** *eru bein tengsl milli kvikusöfnunar og
jarðskjálftavirkni?* Þessi gögn lýsa aðeins skjálftavirkninni. Sjálfstæða
tímaröð um kvikusöfnun vantar, svo engin fylgni er reiknuð.

**Af hverju Reykjanes.** Reiturinn (lengd −23 til −21,5, breidd 63,7 til 64,1)
nær yfir landrisið við Svartsengi og kvikuganginn við Sundhnúk og Grindavík.

**Af hverju 1.11.2023–1.1.2024.** Glugginn er valinn utan um vel skjalfesta
atburðarás:

| Dagsetning | Atburður |
|---|---|
| 8. nóvember 2023 | Veðurstofan lýsir landrisi og líkanmati á kvikusöfnun út frá GNSS- og InSAR-mælingum |
| 10. nóvember 2023 | Stór kvikugangur myndast við Sundhnúk og Grindavík samhliða mikilli jarðskjálftavirkni og aflögun. **Ekki gaus þann dag** |
| 18. desember 2023 | Fyrsta gos hrinunnar við Sundhnúkagíga hefst |

Glugginn nær yfir daga **fyrir, á meðan og eftir** báða atburði: tveir heilir
mánuðir, 1.11.2023 00:00 UTC til 1.1.2024 00:00 UTC, **upphaf meðtalið, endir
ekki** — 61 UTC-dagur.

**Af hverju þessar síur.** `type=earthquake`, `evaluation_mode=manual` og
`system=sil`: aðeins **yfirfarnir** skjálftar úr SIL-kerfi Veðurstofunnar, því
sjálfvirkar greiningar eru oft endurskoðaðar. Stærð 3–7 og dýpt 0–50 km fylgdu
æfingunni; **rökstuðningurinn er hvergi skjalfestur** (kafli 7). Síurnar eru
líka **sannreyndar**: færsla utan markanna stöðvar keyrsluna.

**Stærðarkvarðinn verður að fylgja með.** `Mlw` og `Mw` mega ekki lenda í sama
miðgildi, og færsla án kvarða stöðvar keyrsluna. Hér er **aðeins `Mlw`**, eins
og Veðurstofan skráir hann — hvorki umreiknaður né merktur Richter.

**Það sem úrtakið inniheldur** (frosna viðmiðið, `vidmid/generated/earthquakes-results.md`):

| Mæling | Gildi |
|---|---|
| Atburðir | 334 yfirfarnir SIL-skjálftar |
| Dagar | 61 (2023-11-01 til 2023-12-31) |
| Dagar án atburðar sem stenst síurnar | 43 |
| Daglegur fjöldi | miðgildi 0, hámark 187 (10. nóvember) |
| Nóvember / desember | 330 / 4 atburðir |
| Dýpt | 0,07–11,26 km, miðgildi 4,67 km |
| Stærð (`Mlw`) | 3,00–4,98, miðgildi 3,47 |

Núll merkir **engan skráðan atburð sem stenst valdar síur**, ekki að enginn
skjálfti hafi orðið.

### 1.2 Hagstofan — innritunarárgangur 2017, staðan sex árum síðar

**Spurningin:** hversu stór hluti innritunarárgangsins 2017 lauk námi, og hvernig
ber verkfræði, framleiðsla og mannvirkjagerð saman við önnur námssvið?

**Af hverju innritunarár 2017.** Taflan býður aðeins `2014` og `2017`; valinn
er sá nýrri. Tveir punktar aðgreina ekki þróun frá tilviljun, svo engin
breyting milli árganga er reiknuð.

**Af hverju tímapunkturinn `n+3`.** Kóðinn `n+3` lítur út fyrir að merkja þrjú ár,
en `valueTexts` í lýsigögnunum segir **„Sex árum eftir innritun“**. Niðurstöðurnar
mæla því stöðuna sex árum eftir innritun 2017 — ekki hvort nemendur luku
þriggja ára námi á þremur árum. Auðveldasta villan í þessari töflu.

**Hvað var valið.** `Nemendur` = `5` (brautskráðir alls), `6` (brottfallnir),
`7` (enn í námi); `Námssvið` = `Alls`, `05`, `06`, `07`; `Kyn` = `Alls`, `1`, `2`;
`Fjöldi/Hlutfall` = `1`. Svarið er því **36 prósentugildi** (1 × 1 × 3 × 1 × 4 × 3).

Stöðuflokkarnir þrír eru sami innritunarhópur við sama viðmiðunartíma, svo þeir
leggjast saman í 100% — námundun getur gefið 99,9% eða 100,1%. `Fjöldi/Hlutfall = 1`
merkir **prósentur en ekki fjölda nemenda**; án fjöldans er hvorki hægt að meta
óvissu né tölfræðilega marktækni.

### 1.3 Veðurstöðvar — ein stöð fyrir VR-II

**Spurningin:** forrit á að sýna veðrið í VR-II (Hjarðarhaga 6) og þarf að lesa
eina veðurstöð. Hvaða stöð, og dugar hún?

**Af hverju ein ósíuð beiðni.** Gamla skriftan sendi fimm beiðnir; fjórar með
síum (`active`, `polygon`, `station_id`) sem velja allar úr ósíaða svarinu. Það
er því **yfirmengi** hinna og eitt nægir (regla 4).

**Afmörkun stöðvavalsins.** Kassinn sem er sendur sem `polygon` er 5 km út frá
VR-II. Lengdargráða styttist í cos(breidd), svo kassinn er ekki ferningur í
gráðum. Stöð telst **virk** ef reiturinn `ending` er tómur; ártal þýðir að hún
hætti mælingum það ár, hversu nálæg sem hún er.

Af 778 stöðvum eru **343 virkar** — listinn nær yfir allar stöðvar sem
Veðurstofan þekkir, líka aflagðar. Nálægð er ekki samfelld tímaröð: næsta
virka stöð við VR-II hóf mælingar 2022.

Samanburður þessa eintaks við gömlu síðuna er í
[`vedurstodvar-samanburdur.md`](vedurstodvar-samanburdur.md).

### 1.4 mbl.is — eitt eintak, fimm spurningar

**Spurningin:** hvað má lesa úr kyrrstæðu HTML-svari með reglulegum segðum einum
saman?

**`/frettir/`, ekki forsíðan.** Sótt var af `https://www.mbl.is/frettir/`
(skjalfest í provenance). Fjöldi frétta þar er annar en á forsíðunni.

**Fimm spurningar æfingarinnar**, með svörunum eins og gamla síðan birti þau:
einstakar fréttir **42**, hitastig í Reykjavík **11 °C**, gengi Bandaríkjadals
**121,05 ISK**, sýnileg orð **2.127**, skilgreindir auglýsingareitir **50**.

> **Þessi fimm svör eru úr öðru eintaki en því sem er fryst hér.** Gamla síðan
> reiknaði þau úr `mbl-20260907T103959Z.html` (sótt 2026-09-07 kl. 10:39:59 UTC,
> 370.113 bæti, MD5 `02002470ff0c0622b78a47e89f0044a0`). Eintakið sem P0.1
> bjargaði er **seinna eintakið**, `mbl-20260916T120851Z.html` (2026-09-16,
> 367.351 bæti, MD5 `c2c83bddb8ed41357b7b1b8ab51a6457`). Fyrra eintakið er hvergi
> til. Fréttaforsíða breytist oft á dag, svo tölurnar fimm **munu ekki** koma
> eins út úr frosna eintakinu — og það er ekki villa. Sjá kafla 6.

Tvær afmarkanir til viðbótar: „sýnilegt“ merkir texta sem stendur eftir í
kyrrstæða HTML-svarinu, og auglýsingareitirnir eru **tómir** í því — JavaScript
fyllir þá eftir á. Talningin telur skilgreinda reiti en ekki birtar auglýsingar.

### 1.5 Friends-handritin — 227 skrár, 236 þættir

**Af hverju `delvinso` en ekki `fangj`.** `delvinso` er afleiða af `fangj` þar
sem **brotin HTML-bygging í `0911` og `0915` er löguð**. Bæði söfn gefa sömu
tölur (Monica munar einni línu), svo niðurstöðurnar eru **ekki háðar valinu**.

**Tvær skrár eru undanskildar:** `0423uncut.html` og `07outtakes.html`
(tvítekning og aukaefni). Eftir standa **227 handritsskrár**, sem svara til **236
sýndra þátta** — níu skrár geyma tvo þætti hver.

**Skilgreiningar sem gilda alls staðar** (`vidmid/phoebe-stats/README.md`):

- **Lína** = ein `Nafn: texti` blokk.
- **Orð** = `[a-z][a-z'-]*` eftir að svigainnskot voru fjarlægð — `(hlær)` og
  `(til Joey)` eru sviðsleiðbeiningar en ekki töluð orð.
- **Sena** = talin upp á nýtt í hvert sinn sem lína byrjar á `[Scene: …]`.
- **Hóplínur eru undanskildar.** `All:` og `Monica and Phoebe:` eru ekki eignaðar
  einstaklingum.
- **Phoebe Sr., Ursula og Mrs Buffay teljast ekki Phoebe** — þær eru sérstakar
  persónur í gögnunum.

**Þáttunargæði:** 70.553 textablokkir, þar af 61.161 tilsvar, 4.055
sviðsfyrirsagnir og 3.259 sviðsleiðbeiningar. **2.078 blokkir (2,95%) eru
óflokkaðar** — nær eingöngu „Commercial Break“, „End“ og kreditlínur.

#### 1.5.1 Höfundaréttur — valkostur A

**Vandinn.** Upprunaverkefnið var í lokuðu repo-i; þetta repo er opið. Handritin
sem greiningin las eru **afrit aðdáenda** á höfundarréttarvörðum
sjónvarpshandritum. `fangj/friends` hefur **ekkert leyfi**, og MIT-leyfið á
`delvinso/friends` nær yfir kóðann þar en ekki endilega yfir handritatextann sem
hann vinnur með. Að greina slík handrit í lokuðu námsverkefni er venjubundið; að
endurbirta þau í opnu repo-i er annað mál. Um leið eru bæði söfnin á
einkarepo-um einstaklinga sem enginn í teyminu stýrir — hverfi þau er
greiningin ekki endurkeyranleg.

**Ákvörðunin.** Björn valdi **valkost A** 27.9.2026 (issue #3):

- **Handritin fara aldrei inn í þetta repo** — hvorki afrituð né vendoruð.
  `.gitignore` útilokar `data/external/` og `data/fangj-friends/`, þar sem
  upprunaverkefnið geymdi þau.
- **Afleiddu tölurnar fara í git**: `data/processed/phoebe-stats/` — línufjöldi,
  orðafjöldi, senufjöldi, hlutföll og tíðnitöflur á persónu. Þær eru
  staðreyndir *um* textann, ekki textinn.

**Rökin.** Tölurnar eru það sem síðan birtir. Með þeim í git birtir hún réttar
tölur án handritanna, og varðveisluáhættan er leyst fyrir niðurstöðurnar þótt
hún sé ekki leyst fyrir aðfangið. Sá sem hefur handritasöfnin getur endurkeyrt
greininguna; sá sem hefur þau ekki getur samt rakið hverja tölu að skránni sem
hún kemur úr.

**Af hverju ekki hinir kostirnir:**

| Kostur | Hvað hann hefði gefið | Af hverju ekki |
|---|---|---|
| **B.** Vendora handritin inn í `data/raw/friends/` | Fulla endurkeyrslu, óháða þriðja aðila | Endurbirtir höfundarréttarvarinn texta í opnu repo-i |
| **C.** Sleppa Friends-greiningunum | Einfaldasta leiðin, enginn höfundaréttarvandi | Þrjár af níu síðum hverfa og umtalsverð vinna glatast |

**Verðið sem A kostar.** Friends-tölurnar eru **ekki endurbyggjanlegar úr þessu
repo-i**. Það brýtur meginregluna um að unnin gögn séu afleiða (regla 5), og
undanþágan er rökstudd í
[`../data/processed/README.md`](../data/processed/README.md), kafla 1.2: fyrir
þetta repo eru tölurnar frumgagn. Skilyrðið sem heldur undanþágunni lögmætri er
að engin talnaskrá geymi samfellda setningu úr þáttunum — kafli 1.5.2.

**Tvennt er enn opið — Björn ákveður** (issue #3):

| | Spurning | Staða |
|---|---|---|
| (a) | Á að skrá handritasöfnin sem **submodule** í `.gitmodules` — svo endurkeyrsla sé ein skipun fyrir þann sem hefur aðgang — eða halda þeim alveg utan repo-sins? Submodule geymir aðeins slóð og commit-SHA, ekki textann. | **opið** — `.gitmodules` er óbreytt |
| (b) | Byggðu síðurnar í [`vidmid/vefur/`](vidmid/vefur/) geyma **átta orðréttar handritslínur** úr þætti `0101` (`friends/phoebe-statistics.html` og `search.json`), á `main` og í git-sögunni. Á að samþykkja þær sem tilvitnun, eða endurskrifa söguna? | **opið** — línurnar eru óbreyttar |

Spurning (b) ræður hvort skilyrði #3 — *ekkert höfundarréttarvarið efni í
git-sögu þessa repo-s* — telst uppfyllt. Þangað til er það **ekki** staðfest.

#### 1.5.2 Handritsleitin — þröskuldur og afmörkun

Fullyrðingin *„engin talnaskrá geymir samfellda setningu“* er ekki
traustsatriði heldur prófuð með
[`../src/python/vidmid/handritsleit.py`](../src/python/vidmid/handritsleit.py)
og [`../tests/test_handritsleit.py`](../tests/test_handritsleit.py):

```bash
python3 src/python/vidmid/handritsleit.py stadfesta
```

**Reglan fyrir hvert strengjagildi:**

1. **Hámark fimm orð** (`ORDATHAK_GAGNAREITS = 5` í `handritsreitir.py`).
2. **Ekkert setningamerki** — `.`, `!`, `?` eða `…` sem lokar orði eða er fylgt
   af hástafsorði. Tugabrot (`2.95`) eru undanskilin, annars teldist hver
   prósentutala setning.

**Af hverju fimm.** Fimm orð er mælt hámark þeirra gagnareita sem ekki eru
undanþegnir (`.units.share_pct` í `phoebe-screentime-by-season.json` og
`.question` í `phoebe-extra-stats.json`). Lengsti strengurinn í
`signature-phrases.csv` — reitnum sem er næst því að vera tilvitnun — er þrjú
orð. Meðaltilsvar í handritunum er **11,2 orð** hjá Phoebe og **10,7 orð** hjá
hinum fimm (`summary.json`), svo þakið er **undir hálfu meðaltilsvari**: brot úr
tilsvari fellir prófið, ekki aðeins heilt tilsvar.

**Undanþágur.** 18 reitir brjóta almennu regluna af lögmætri ástæðu —
aðferðarlýsingar verkefnisins sjálfs á íslensku og þáttatitlar. Þeir eru taldir
upp í `handritsreitir.py`, hver með ástæðu og **frystri SHA-256** af innihaldinu.
Undanþága getur því ekki orðið felustaður: breytist undanþeginn reitur, finnist
undanþága ekki í skránum, eða þurfi reitur hana ekki lengur, fellur prófið.

**Leitin prentar ekki innihald** brotlegs strengs, aðeins staðsetningu og
mælingar. Væri hann handritstexti myndi prentunin afrita hann í logga.

**Hún er prófuð þar sem hún á að bresta** (`agenta-verkefni.md`, kafli 6):
prófin keyra hana á heimatilbúnum gervisetningum og falla ef hún **finnur þær
ekki**.

**Afmörkun — það sem leitin nær til, og það sem hún nær ekki til.** Hún les
aðeins `.json`- og `.csv`-skrár á þessum stöðum, samtals **42 skrár**:

| Nær til | Nær **ekki** til |
|---|---|
| `data/processed/phoebe-stats/` | Byggðu HTML-síðurnar í `docs/vidmid/vefur/` |
| `docs/vidmid/phoebe-stats/` | `docs/vidmid/vefur/search.json` |
| `docs/vidmid/vefur/friends/phoebe-stats/` | Annað í repo-inu |
| `docs/vidmid/generated/phoebe-central-perk-summary.json` | |

Grænt próf þýðir því: **talnaskrárnar eru textalausar** — ekki að repo-ið sé
það. Vitað er að það er það ekki: `friends/phoebe-statistics.html` og
`search.json` geyma línurnar átta úr spurningu (b) hér að ofan. Prófið heitir
`test_skannadar_talnaskrar_geyma_enga_samfellda_setningu` til að nafnið lofi
ekki meiru en það prófar.

**Af hverju leitin er ekki víkkuð yfir `docs/vidmid/vefur/`:** hún myndi falla á
línunum átta, og það er ekki leitarinnar að ákveða hvort þær mega standa. Að
víkka hana og undanskilja línurnar væri að svara spurningu (b) hljóðlega; að
víkka hana án undanþágu væri að gera `main` rautt vegna ákvörðunar sem ekki
hefur verið tekin. Afmörkunin stendur þar til Björn hefur svarað (b).

### 1.6 TMDB — ekkert eintak

Safnið átti að staðfesta hver leikur Phoebe og í hve mörgum þáttum. Hvorki
svörin né samantektin lifðu af og `TMDB_TOKEN` vantar, svo **ekkert verður
skjalfest** umfram beiðnirnar sjálfar (`heimildir.md`, 1.5). Engin TMDB-tala
birtist fyrr en safnið er sótt á ný.

---

## 2. Hreinsun og sannreyning

**Færsla hverfur aldrei hljóðlega.** Frávik stöðva keyrsluna með skýringu
(regla 6).

| Þrep | Hvað er sannreynt |
|---|---|
| Söfnun | Svarið vistað **óbreytt** áður en nokkuð er unnið úr því; SHA-256 og provenance skráð |
| Frysting | SHA-256 hverrar skráar borið við provenance upprunans |
| Þáttun | Bygging, gildissvið, tímastimplar, einkvæm auðkenni, skráður stærðarkvarði |
| Talning | Dagar án atburðar fá **röð með núlli**, ekki enga röð |

Tímaröð án núlldaga sýnir ranga mynd af 43 dögum af 61 — þess vegna
`LEFT JOIN` á dagatöfluna (P1.7).

Hrágögnum er aldrei breytt. Afleiðurnar — grunnurinn, `web/gogn/` og skýrslubútar
— verða til úr `data/raw/` og reiknast eins í hverri keyrslu.

## 3. Geymsla

Gagnagrunnurinn er **afleiða**: honum má eyða og byggja hann aftur úr
`data/raw/` og `src/sql/migrations/` án nets. Þess vegna er hann utan git.
Migration er **aldrei breytt eftir keyrslu** (regla 5).
`001_gagnasofnun.sql` býr til `fetch_log`, sem skráir hverja söfnun: þjónustu,
endapunkt, breytur, tímastimpil, HTTP-stöðu, fjölda færslna og slóðina á óbreytta
svarið í `data/raw/`. Töflur hvers gagnasafns koma í P1.2–P1.6.

Allar fyrirspurnir eru með breytum (`cur.execute(sql, (gildi,))`), aldrei
strengjasamsetningu — líka töflunöfn sem koma að utan, þar sem hvítlisti er
notaður.

## 4. Greining

Greiningin er **lýsandi**. Ekkert í verkefninu mælir orsakasamband og engin
fylgni sem er reiknuð má lesast sem slík.

| Aðferð | Hvar | Forsenda sem liggur að baki |
|---|---|---|
| Dagleg talning með núlldögum | Skjálftavaktin | Dagur án atburðar er mæling, ekki gat |
| Miðgildi og bil **innan hvers stærðarkvarða** | Skjálftavaktin | `Mlw` og `Mw` eru ekki sama talan |
| Hlaupandi 7 daga meðaltal | Skjálftavaktin | Sléttun, ekki spá — sjá takmörkun í kafla 6 |
| Prósentur þriggja stöðuflokka | Hagstofan | Sami hópur, sami viðmiðunartími, leggjast í 100% |
| Fjarlægð eftir stórbaug (haversine) | Veðurstöðvar | Jarðarradíus 6371,0088 km |
| Talningar með reglulegum segðum | mbl.is | Aðeins kyrrstætt HTML; JavaScript er ekki keyrt |
| Hlutdeild, ræðuskipti og `interaction_lift` | Friends | Lift leiðréttir fyrir því að málglaðar persónur eiga fleiri samskipti við alla |
| z-gildi úr log-odds með Dirichlet-prior | Friends | Monroe, Colaresi & Quinn (2008); aðeins orð sem koma ≥ 40 sinnum fyrir |

### 4.1 Fyrirspurnirnar og námundun

Hver tala sem síðurnar byggja á kemur úr fyrirspurn í `src/sql/queries/` —
**ein skrá á hverja fyrirspurn**, með haus sem segir hvaða spurningu hún svarar,
hvaða síða notar hana og hvaða `?`-breytur hún tekur (#11). Python les þær með
einum lesara (`src/python/gagnagrunnur/fyrirspurnir.py`) eftir hvítlista; engin
fyrirspurn er geymd í Python-streng og engin er sett saman úr strengjum. Sama
fyrirspurn er notuð af hleðslunni til staðfestingar og af birtingunni, svo
hleðslan staðfestir nákvæmlega þá tölu sem fer á síðuna.

**Námundunarvenjan: SQL skilar óafrúnnuðu, birtingin námundar.** SQLite `ROUND`
námundar helming frá núlli; Python (`round`, og sniðið í
`utflutningur/islenskt_snid.py`) námundar helming að sléttri tölu. Nafntilvik
Phoebe á þátt í fyrstu þáttaröð eru nákvæmlega 99/24 = 4,125: SQL-námundun gæfi
4,13, en greiningin og gamla síðan sýndu 4,12. Þess vegna er námundað á einum
stað, í birtingu, með Python — og viðmiðið heldur. Tvær sýnir í
`006_friends.sql` námunda í SQL (`unclassified_pct`, `interaction_lift`); þeim er
ekki breytt (regla 5), en prófað er að þær gefi sömu tölu og Python-námundun.

**Hlaupandi 7 daga meðaltal** (`skjalftar-hlaupandi-medaltal.sql`) er ný afleidd
mæling: gamla síðan reiknaði það ekki og það á sér enga viðmiðstölu. Glugginn
endar á deginum (dagurinn og sex dagar á undan, ekki miðjaður), núll-dagar eru
taldir með, og fyrstu sex dagar tímabilsins hafa styttri glugga — fyrirspurnin
skilar `days_in_window` svo birtingin geti merkt þá.

## 5. Rekjanleiki — báðar áttir

Frá tölu að hrágagni og til baka.

| Gagnasafn | Hrágögn | Provenance | Hleðsla í grunn | Síða |
|---|---|---|---|---|
| Jarðskjálftar | `data/raw/vedur-quakes/` | safnsins eigin | P1.2 (#6) | `web/sidur/skjalftavaktin.html` |
| Hagstofan | `data/raw/hagstofan/` | safnsins eigin | P1.3 (#7) | `web/sidur/hagstofan.html` |
| Veðurstöðvar | `data/raw/vedurstodvar/` | safnsins eigin | P1.4 (#8) | `web/sidur/vedurstodvar.html` |
| mbl.is | `data/raw/mbl/` | `vidmid/provenance.json` | P1.5 (#9) | `web/sidur/mbl-regex.html` |
| Friends | *engin — aðeins talnaniðurstöður* | `vidmid/phoebe-stats/_meta.json` | P1.6 (#10) | `phoebe-tolfraedi.html`, `phoebe-central-perk.html` |
| TMDB | **vantar** | — | — | `web/sidur/phoebe-tmdb.html` |

Leiðin til baka: tala á síðu → JSON í `web/gogn/` (`src/python/utflutningur/`)
→ grunnurinn → `data/raw/`, þar sem `provenance.json` segir hvaða beiðni skilaði
gagninu og `frysting.json` staðfestir að það sé óbreytt. Hvaða skrifta les hvaða
safn er í [`../data/raw/README.md`](../data/raw/README.md).

---

## 6. Takmarkanir

Í [`takmarkanir.md`](takmarkanir.md) — skrifað fyrir lesanda vefsíðunnar og
fer óbreytt á aðferðafræðisíðuna (P3.11). Einn staður, ekki tveir.

---

## 7. Óstaðfest og ófrágengið

Full færsla telst vera þjónusta, slóð, sóknardagsetning, leyfi og tengill í
skjölun. Þrjú af sex gagnasöfnum standast það: **jarðskjálftarnir**,
**veðurstöðvarnar** og **Friends-handritin**. Hin þrjú vantar hvert sitt:
Hagstofan leyfi og skjölunartengil, mbl.is lesna skilmála, og TMDB allt nema
lýsinguna á beiðnunum sjálfum.

Opnar spurningar um heimildir og leyfi eru taldar upp í
[`heimildir.md`](heimildir.md), kafla 5. Hér eru þær sem snúa að aðferðinni:

| # | Atriði | Staða |
|---|---|---|
| 1 | Rökstuðningur fyrir stærð 3–7 og dýpt 0–50 km | **óstaðfest** — hvergi skjalfest, hvorki í kóða né á gömlu síðunni |
| 2 | Rökstuðningur fyrir `evaluation_mode=manual` | **að hluta** — skjalfest hvað sían útilokar, ekki af hverju valið var tekið |
| 3 | Fimm mbl-svörin úr frosna eintakinu | **ekki reiknuð** — P1.5 reiknar þau og skráir muninn við gömlu síðuna |
| 4 | Afmörkun TMDB-safnsins | **ófrágengið** — ekkert eintak til |
| 5 | Höfundaréttur Friends-handritanna | **ákveðið að hluta** — valkostur A (27.9.2026): tölurnar í git, handritin aldrei. Opið: (a) submodule í `.gitmodules` og (b) átta orðréttar línur í `vidmid/vefur/` — sjá kafla 1.5.1 |
| 6 | Vinnsla og greining Central Perk-hlutans | **skjalfest í viðmiðinu**, ekki endurtekin hér — P2.6 flytur hana yfir |
