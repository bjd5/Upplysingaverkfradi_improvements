# Aðferðafræði

Skráð jafnóðum meðan unnið er, ekki eftir á (regla 8). Þetta skjal svarar einni
spurningu fyrir hvert gagnasafn: **hvernig var það afmarkað og af hverju
einmitt þannig?** Hvaðan gögnin komu er í [`heimildir.md`](heimildir.md).

Hver fullyrðing hér á sér stoð í `provenance.json` safnsins eða í frosna
viðmiðinu í [`vidmid/`](vidmid/), og tilvísunin fylgir. Þar sem rökstuðningur er
**hvergi skráður** stendur það berum orðum — betra er að skrá eyðu en að fylla
hana með ágiskun.

---

## 1. Afmörkun gagnasafnanna

### 1.1 Jarðskjálftar — Reykjanes, nóvember–desember 2023

**Rannsóknarspurningin er í mótun:** *eru bein tengsl milli kvikusöfnunar og
jarðskjálftavirkni?* Gamla síðan svaraði henni ekki og þessi gögn svara henni
ekki heldur. Þau byggja fyrri helming svarsins — jarðskjálftavirknina. Seinni
helminginn, sjálfstæða tímaröð um kvikusöfnun, vantar enn, og án hans er engin
fylgni reiknuð og engin ályktun dregin.

**Af hverju Reykjanes.** Reiturinn sem var sendur með beiðninni — lengdargráða
−23 til −21,5, breiddargráða 63,7 til 64,1 — afmarkar Reykjanesskagann, þar sem
atburðarásin sem spurningin snýst um átti sér stað: landris við Svartsengi og
kvikugangurinn við Sundhnúk og Grindavík.

**Af hverju 1.11.2023–1.1.2024.** Glugginn er valinn utan um vel skjalfesta
atburðarás:

| Dagsetning | Atburður |
|---|---|
| 8. nóvember 2023 | Veðurstofan lýsir landrisi og líkanmati á kvikusöfnun út frá GNSS- og InSAR-mælingum |
| 10. nóvember 2023 | Stór kvikugangur myndast við Sundhnúk og Grindavík samhliða mikilli jarðskjálftavirkni og aflögun. **Ekki gaus þann dag** |
| 18. desember 2023 | Fyrsta gos hrinunnar við Sundhnúkagíga hefst |

Glugginn nær því yfir daga **fyrir, á meðan og eftir** báða atburði. Tveir heilir
almanaksmánuðir gefa skýr og endurkeyranleg mörk: frá 1. nóvember 2023 kl. 00:00
UTC til 1. janúar 2024 kl. 00:00 UTC, **upphaf meðtalið og endir undanskilinn** —
61 UTC-dagur fyrir daglegan samanburð.

**Af hverju þessar síur.** Beiðnin bað um `type=earthquake`,
`evaluation_mode=manual` og `system=sil`: aðeins **yfirfarna** jarðskjálfta úr
SIL-mælakerfi Veðurstofunnar. Sjálfvirkar greiningar eru því undanskildar, og
það skiptir máli vegna þess að eldri skjálftafærslur geta verið endurskoðaðar —
yfirfarnar færslur eru þær sem standa. Stærðarmörkin 3–7 og dýptarmörkin
0–50 km fylgdu æfingunni; **rökstuðningur þeirra er hvergi skjalfestur** og er
skráður sem opin spurning (kafli 7).

Síurnar eru ekki aðeins sendar heldur líka **sannreyndar**: hver færsla er lesin
yfir og frávik stöðva keyrsluna. Svar sem inniheldur færslu utan markanna er
ekki það úrtak sem beðið var um.

**Stærðarkvarðinn verður að fylgja með.** `Mlw` og `Mw` eru ekki sama talan og
mega ekki lenda í sama miðgildi; vanti kvarðann er ekki hægt að álykta hann, svo
færsla án hans stöðvar keyrsluna. Í þessu eintaki er **aðeins `Mlw`**, varðveittur
eins og Veðurstofan skráir hann — hvorki umreiknaður né merktur Richter.

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

**Af hverju innritunarár 2017.** Lýsigögn töflunnar bjóða aðeins tvö innritunarár:
`2014` og `2017`. Fyrirspurnin velur það síðara — nýjasta árganginn sem taflan
nær yfir. Hún velur **ekki** bæði: tveir punktar sýna mun milli tveggja árganga
en aðgreina ekki varanlega þróun frá tilviljun, breyttri samsetningu hópa eða
breytingum á námsumhverfi. Þessi fyrirspurn reiknar því enga breytingu milli
árganga.

**Af hverju tímapunkturinn `n+3`.** Kóðinn `n+3` lítur út fyrir að merkja þrjú ár,
en `valueTexts` í lýsigögnunum segir **„Sex árum eftir innritun“**. Niðurstöðurnar
mæla því stöðuna sex árum eftir innritun 2017 — ekki hvort nemendur luku
þriggja ára námi á þremur árum. Þetta er auðveldasta villan að gera í þessari
töflu og er þess vegna skjalfest hér.

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

**Af hverju ein ósíuð beiðni.** Gamla skriftan sendi fimm beiðnir á sama
endapunkt: eina ósíaða og fjórar með síum (`active`, `polygon`, `station_id`).
Síurnar velja allar úr sama mengi, svo ósíaða svarið er **yfirmengi** þeirra
allra og hinar fjórar má reikna staðbundið úr því. Ein beiðni er því frystingin
og fjórar beiðnir til viðbótar væru álag á þjónustu sem gefur gögnin frítt
(regla 4).

**Afmörkun stöðvavalsins.** Kassinn sem er sendur sem `polygon` er 5 km út frá
VR-II. Lengdargráða styttist í cos(breidd), svo kassinn er ekki ferningur í
gráðum. Stöð telst **virk** ef reiturinn `ending` er tómur; ártal þýðir að hún
hætti mælingum það ár, hversu nálæg sem hún er.

Af 778 stöðvum í eintakinu eru **343 virkar** — listinn er skrá yfir allar stöðvar
sem Veðurstofan þekkir, virkar og aflagðar, en ekki yfir stöðvar í rekstri.
Nálægð og samfelld tímaröð eru tvö ólík skilyrði: næsta virka stöð við VR-II
hóf mælingar 2022 og á ekkert frá 1976.

Samanburður þessa eintaks við gömlu síðuna er í
[`vedurstodvar-samanburdur.md`](vedurstodvar-samanburdur.md).

### 1.4 mbl.is — eitt eintak, fimm spurningar

**Spurningin:** hvað má lesa úr kyrrstæðu HTML-svari með reglulegum segðum einum
saman?

**Af hverju `/frettir/` en ekki forsíðan.** Sótt var af `https://www.mbl.is/frettir/`
— fréttayfirlitið, ekki forsíða mbl.is. Það er skjalfest í provenance eintaksins
og skiptir máli fyrir talninguna: fjöldi frétta á yfirlitssíðu er annar en á
forsíðu.

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

**Af hverju `delvinso` en ekki `fangj`.** Söfnin tvö eru nánast eins — `delvinso`
er afleiða af `fangj.github.io/friends` — en í `delvinso` er búið að **laga brotna
HTML-byggingu í þáttum `0911` og `0915`**. Greiningin var keyrð á báðum söfnum til
samanburðar og gaf sömu tölur (Monica munaði einni línu), svo niðurstöðurnar eru
**ekki háðar valinu**; það er valið vegna þáttunargæða en ekki vegna talnanna.

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

### 1.6 TMDB — ekkert eintak

Safnið átti að staðfesta hver leikur Phoebe og í hversu mörgum þáttum, og var um
leið æfing í réttri meðferð aðgangslykils. Hvorki svörin né samantektin lifðu af
og `TMDB_TOKEN` er ekki til, svo **ekkert er hægt að skjalfesta um afmörkun þessa
safns** annað en það sem beiðnirnar sjálfar segja (sjá `heimildir.md`, kafla 1.5).
Engin tala úr TMDB má birtast á vefsíðunni fyrr en safnið er sótt á ný.

---

## 2. Hreinsun og sannreyning

**Grundvallarregla: færsla hverfur aldrei hljóðlega.** Frávik stöðva keyrsluna
með skýringu í stað þess að falla út úr talningu (regla 6). Þetta gildir í báðar
áttir — svar sem stenst ekki síurnar sem beðið var um er ekki það úrtak sem
beðið var um, og afrit sem stemmir ekki við SHA-256 er ekki afrit.

| Þrep | Hvað er sannreynt |
|---|---|
| Söfnun | Svarið vistað **óbreytt** áður en nokkuð er unnið úr því; SHA-256 og provenance skráð |
| Frysting | SHA-256 hverrar skráar borið við provenance upprunans |
| Þáttun | Bygging, gildissvið, tímastimplar, einkvæm auðkenni, skráður stærðarkvarði |
| Talning | Dagar án atburðar fá **röð með núlli**, ekki enga röð |

Síðasta atriðið er ekki formsatriði: tímaröð sem sleppir núlldögunum sýnir ranga
mynd af 43 dögum af 61 í jarðskjálftaúrtakinu. Þess vegna krefst P1.7
`LEFT JOIN` á dagatöfluna en ekki talningar á röðum í atburðatöflunni.

Hrágögnum er aldrei breytt eftir á. Það sem má breytast eru **afleiðurnar**:
gagnagrunnurinn, JSON-skrárnar í `web/gogn/` og skýrslubútar eins og
`vedurstodvar-samanburdur.md`, sem allar verða til úr `data/raw/` og eiga að
reiknast eins í hverri keyrslu.

## 3. Geymsla

Gagnagrunnurinn er **afleiða en ekki frumgagn**: það á að vera hægt að eyða honum
og byggja hann upp á nýtt úr `data/raw/` og `src/sql/migrations/` án nets. Þess
vegna er hann utan git.

Uppbyggingin verður aðeins til úr númeruðum migrations, sem er **aldrei breytt
eftir að þær hafa verið keyrðar** — ný migration í staðinn (regla 5).
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

## 5. Rekjanleiki — báðar áttir

Frá tölu að hrágagni og til baka. Síðurnar eru þær sem
[`endurbygging.md`](endurbygging.md) skilgreinir; þær verða til í bylgju 3.

| Gagnasafn | Hrágögn | Provenance | Hleðsla í grunn | Síða |
|---|---|---|---|---|
| Jarðskjálftar | `data/raw/vedur-quakes/` | safnsins eigin | P1.2 (#6) | `web/sidur/skjalftavaktin.html` |
| Hagstofan | `data/raw/hagstofan/` | safnsins eigin | P1.3 (#7) | `web/sidur/hagstofan.html` |
| Veðurstöðvar | `data/raw/vedurstodvar/` | safnsins eigin | P1.4 (#8) | `web/sidur/vedurstodvar.html` |
| mbl.is | `data/raw/mbl/` | `vidmid/provenance.json` | P1.5 (#9) | `web/sidur/mbl-regex.html` |
| Friends | *engin — aðeins talnaniðurstöður* | `vidmid/phoebe-stats/_meta.json` | P1.6 (#10) | `phoebe-tolfraedi.html`, `phoebe-central-perk.html` |
| TMDB | **vantar** | — | — | `web/sidur/phoebe-tmdb.html` |

Skriftur sem lesa hrágögnin **í dag** eru tvær:
`src/python/sofnun/frysta.py` staðfestir að öll söfnin séu ósnert, og
`src/python/vinnsla/vedurstodvar_samanburdur.py` les stöðvalistann og ber hann
við viðmiðið. Hleðsluskriftur hvers safns verða til í bylgju 1; hvaða skrifta á
að lesa hvaða safn er skráð í [`../data/raw/README.md`](../data/raw/README.md).

Leiðin til baka: hver tala á síðu kemur úr JSON-skrá í `web/gogn/`, sem
`src/python/utflutningur/` skrifar úr grunninum, sem er byggður úr `data/raw/`,
þar sem `provenance.json` segir hvaða beiðni skilaði gagninu og `frysting.json`
staðfestir að það sé óbreytt. Fjögur skref, öll í þessu repo-i.

---

## 6. Takmarkanir

Takmarkanirnar eru í sérstakri skrá: **[`takmarkanir.md`](takmarkanir.md)**.

Sá texti er skrifaður fyrir lesanda vefsíðunnar og fer **óbreyttur** inn á
`web/sidur/adferdafraedi.html` í P3.11 (issue #25). Hann á því einn stað en ekki
tvo — texti sem er afritaður milli skjala fer á skjön við sjálfan sig um leið og
annað eintakið er lagfært.

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
| 5 | Höfundaréttur Friends-handritanna | **ófrágengið** — issue #3 ræður hvort talnaniðurstöður standa óbreyttar |
| 6 | Vinnsla og greining Central Perk-hlutans | **skjalfest í viðmiðinu**, ekki endurtekin hér — P2.6 flytur hana yfir |
