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
| 5 | Höfundaréttur Friends-handritanna | **frágengið** 27.9.2026 — aðeins talnaniðurstöður (P0.5, issue #3) |
| 6 | Vinnsla og greining Central Perk-hlutans | **skjalfest í viðmiðinu**, ekki endurtekin hér — P2.6 flytur hana yfir |
