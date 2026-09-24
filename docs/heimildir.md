# Heimildaskrá

Sérhver tala sem birtist á vefsíðunni á sér rekjanlega leið aftur í hrágögn
(regla 8). Þessi skrá er fyrri helmingur þeirrar leiðar: **hvaðan kom gagnið?**
Seinni helmingurinn — *hvernig var það afmarkað og unnið?* — er í
[`adferdafraedi.md`](adferdafraedi.md).

Ekkert hér er skrifað eftir minni. Hver færsla á sér stoð í `provenance.json`
safnsins í [`../data/raw/`](../data/raw/) eða í frosna viðmiðinu í
[`vidmid/`](vidmid/), og tilvísunin fylgir færslunni. Það sem ekki er hægt að
styðja er merkt **óstaðfest** í kafla 5 — ekki giskað á.

Staðfesta má að gögnin séu ósnert hvenær sem er:

```bash
python3 src/python/sofnun/frysta.py stadfesta     # hrágögnin
python3 src/python/vidmid/provenance.py stadfesta  # viðmiðið
```

---

## 1. Vefþjónustur

| Gagnasafn | Þjónusta | Sótt (UTC) | Leyfi | Auðkenning |
|---|---|---|---|---|
| Jarðskjálftar | Veðurstofa Íslands — Quakes API | 2026-09-10T11:46:23Z | **CC BY 4.0** | engin |
| Hagstofan | Hagstofa Íslands — PxWeb API | 2026-09-10T09:02:26Z | óstaðfest | engin |
| Veðurstöðvar | Veðurstofa Íslands — Weather API | 2026-09-24T11:22:18Z | **CC BY 4.0** | engin |
| mbl.is | mbl.is (vefsíða, ekki API) | 2026-09-16T12:08:51Z | ekkert gefið | engin |
| TMDB | The Movie Database API v3 | **ekki sótt** | — | Bearer-lykill |

### 1.1 Jarðskjálftar — Veðurstofa Íslands

| Atriði | Gildi |
|---|---|
| Endapunktur | `https://api.vedur.is/quakes/events` |
| Skjölun | `https://api.vedur.is/quakes/openapi.json` |
| Aðferð | `GET`, haus `x-vi-api-version: 2026-08-06` |
| Sótt (UTC) | 2026-09-10T11:46:23Z |
| Athugunartímabil | 2023-11-01T00:00:00+00:00 → 2024-01-01T00:00:00+00:00 (upphaf meðtalið, endir undanskilinn) |
| Síur | `polygon` (lengd −23 til −21,5; breidd 63,7 til 64,1), `size_min=3`, `size_max=7`, `depth_min=0`, `depth_max=50`, `type=earthquake`, `evaluation_mode=manual`, `system=sil` |
| Svarstærð | 93.233 bæti, 334 atburðir |
| SHA-256 | `a535359ea84346426d5ce7fccf4ce8e5158b712e4fc66378dae4b291f771fa9a` |
| Leyfi | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Heimild þessarar færslu | [`../data/raw/vedur-quakes/provenance.json`](../data/raw/vedur-quakes/provenance.json) |

**Tilvísunarskylda.** CC BY 4.0 krefst þess að vísað sé til Veðurstofu Íslands
alls staðar þar sem þessi gögn birtast — líka á vefsíðunni sjálfri, ekki bara hér.

Þjónustan er opin og krefst hvorki innskráningar né API-lykils. Hausinn
`x-vi-api-version` velur útgáfu þjónustunnar; hann er opinbert útgáfunúmer en
ekki leyndarmál (frosna viðmiðið, `vidmid/vefur/capstone/earthquakes.html`).

### 1.2 Hagstofan — brautskráning af háskólastigi

| Atriði | Gildi |
|---|---|
| Endapunktur | `https://px.hagstofa.is/pxis/api/v1/is/Samfelag/skolamal/4_haskolastig/1_hsProf/SKO04208b.px` |
| Aðferðir | `GET` (lýsigögn) og `POST` (fyrirspurn), `Content-Type: application/json; charset=utf-8` |
| Sótt (UTC) | 2026-09-10T09:02:26Z |
| Tafla | „Brautskráningarhlutfall og árgangsbrotthvarf í þriggja ára bakkalárnámi eftir námssviði 2014-2023“ |
| Uppruni taflunnar | Nemendaskrá og prófaskrá Hagstofu Íslands (reiturinn `source` í svarinu) |
| Svarsnið | json-stat2 |
| Fyrirspurnin sjálf | [`../data/raw/hagstofan/query.json`](../data/raw/hagstofan/query.json) — vistuð óbreytt |
| Leyfi | **óstaðfest** — sjá kafla 5 |
| Heimild þessarar færslu | [`../data/raw/hagstofan/provenance.json`](../data/raw/hagstofan/provenance.json) |

Safnið geymir fjórar skrár: lýsigögnin (`metadata.json`), fyrirspurnina
(`query.json`), svarið (`response.json`) og provenance. Að fyrirspurnin sjálf
sé varðveitt skiptir máli: PxWeb-svar án fyrirspurnarinnar er ekki
endurskapanlegt, því sama slóð skilar hverju sem er eftir því hvað var beðið um.

### 1.3 Veðurstöðvar — Veðurstofa Íslands

| Atriði | Gildi |
|---|---|
| Endapunktur | `https://api.vedur.is/weather/stations` |
| Skjölun | `https://api.vedur.is/weather/openapi.json` |
| Aðferð | `GET`, engar færibreytur (ósíað svar) |
| Sótt (UTC) | 2026-09-24T11:22:18Z |
| Svarstærð | 152.165 bæti, 778 stöðvar |
| SHA-256 | `d8404ec4a7dc84ba57adf6a03674e4ca0417d8bb79a1cbd44586ab9faf7e27f4` |
| Leyfi | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — skráð í `info.license` í openapi-lýsingu þjónustunnar, staðfest við söfnun |
| Heimild þessarar færslu | [`../data/raw/vedurstodvar/provenance.json`](../data/raw/vedurstodvar/provenance.json) |

**Þetta er ný söfnun, ekki afrit.** Gamla verkefnið vistaði stöðvalistann aldrei
og sótti hann upp á nýtt í hverri byggingu. Eintakið hér er því fyrsta frosna
eintakið sem til er og tölur þess eru bornar saman við gömlu síðuna í
[`vedurstodvar-samanburdur.md`](vedurstodvar-samanburdur.md).

Hnit VR-II (Hjarðarhagi 6, 107 Reykjavík) — 64,1386922, −21,9556406 — voru flett
upp í **Nominatim (OpenStreetMap)** 2026-09-03 í upprunaverkefninu og eru
endurnotuð óbreytt. Leyfi þeirrar uppflettingar er **óstaðfest** (kafli 5).

### 1.4 mbl.is — fréttaforsíða fyrir regex-æfingu

| Atriði | Gildi |
|---|---|
| Slóð | `https://www.mbl.is/frettir/` (**ekki** forsíða mbl.is) |
| Aðferð | `GET` á vefsíðu; þetta er ekki vefþjónusta og ekkert API |
| Sótt (UTC) | 2026-09-16T12:08:51Z |
| HTTP-staða | 200, `text/html; charset=UTF-8`, 367.351 bæti |
| MD5 | `c2c83bddb8ed41357b7b1b8ab51a6457` |
| Leyfi | ekkert gefið — efnið er höfundarréttarvarið fréttaefni |
| Heimild þessarar færslu | [`../data/raw/mbl/mbl-20260916T120851Z.json`](../data/raw/mbl/mbl-20260916T120851Z.json) og [`vidmid/provenance.json`](vidmid/provenance.json) |

Eintakið er notað sem **textasýni fyrir reglulegar segðir**, ekki til
endurbirtingar á efni mbl.is. Engin frétt, fyrirsögn né mynd af síðunni fer inn
á nýju vefsíðuna; aðeins talningar úr HTML-byggingunni.

> **Athugið — eintakið er ekki það sama og gamla síðan birti.** Tölurnar á gömlu
> mbl-síðunni eru reiknaðar úr eintaki frá **2026-09-07**, sem hvergi er til.
> Sjá [`adferdafraedi.md`](adferdafraedi.md), kafla 1.4 og 6.

### 1.5 TMDB — ekki sótt

| Atriði | Gildi |
|---|---|
| Þjónusta | The Movie Database (TMDB) API v3 |
| Skjölun | `https://developer.themoviedb.org/reference/tv-series-details` |
| Endapunktar | `GET /3/tv/1668?language=en-US` og `GET /3/tv/1668/aggregate_credits?language=en-US` (`1668` = Friends) |
| Auðkenning | `Authorization: Bearer <token>` á hverri beiðni — ókeypis reikningur |
| Staða | **ekkert eintak til.** `TMDB_TOKEN` er hvorki í umhverfi né `.env` |
| Heimild þessarar færslu | [`../data/raw/frysting.json`](../data/raw/frysting.json) (`ofryst`) og `vidmid/vefur/friends/phoebe-tribute.html` |

Safnið átti að staðfesta hver leikur Phoebe og í hversu mörgum þáttum. Hvorki
svörin né samantektin lifðu af: `vidmid/generated/phoebe-tmdb-summary.md`
inniheldur textann *„TMDB-samantekt vantar — staðbundin tímamæling án lykils“*,
svo **ekkert viðmið er til fyrir þetta safn** og engin tala úr því má birtast
fyrr en það er sótt á ný.

---

## 2. Gögn sem eru ekki frá vefþjónustu

### 2.1 Friends-handritin

| Atriði | Gildi |
|---|---|
| Safn sem var greint | `delvinso/friends` — `data/external/delvinso-friends/season/*.html` |
| Upphaflegur uppruni | `fangj.github.io/friends` (delvinso-safnið er afleiða af því) |
| Umfang | 227 handritsskrár = 236 sýndir þættir (níu skrár geyma tvo þætti) |
| Undanskildar skrár | `0423uncut.html`, `07outtakes.html` |
| Greint | 2026-09-17T09:47:09Z af `src/phoebe_analysis.py` í upprunaverkefninu |
| Leyfi | **ekkert** — `fangj/friends` er safn afritaðra handrita án leyfis |
| Heimild þessarar færslu | [`vidmid/phoebe-stats/_meta.json`](vidmid/phoebe-stats/_meta.json) og [`vidmid/phoebe-stats/README.md`](vidmid/phoebe-stats/README.md) |

**Handritin sjálf eru ekki í þessu repo og fara ekki inn í það.** Þetta repo er
opið og handritin eru höfundarréttarvarin. Það sem er varðveitt eru
**talnaniðurstöður um textann** — línufjöldi, senufjöldi, tíðnitöflur — sem eru
staðreyndir um textann en ekki textinn sjálfur. Endanleg ákvörðun er í issue #3;
þangað til gildir þessi afmörkun.

Handritin eru **afrit aðdáenda**, ekki opinber handrit þáttanna. Það hefur
afleiðingar fyrir túlkun og er rakið í [`adferdafraedi.md`](adferdafraedi.md),
kafla 6.

### 2.2 Frosna viðmiðið — gamla vefsíðan

| Atriði | Gildi |
|---|---|
| Hvað | Byggð Quarto-síða upprunaverkefnisins, 28 HTML-síður |
| Upprunarepo | `Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe` (lokað) |
| Byggingarlotur | þrjár: `5510cab`, `9cf667d` og `fdf1261` (2026-09-16 til 2026-09-17) |
| Heimild þessarar færslu | [`vidmid/README.md`](vidmid/README.md) og [`vidmid/provenance.json`](vidmid/provenance.json) |

Viðmiðið er heimild um **hvað gamla síðan birti**, ekki um hvað er rétt. Það er
ekki innbyrðis samstæð bygging: fjórar kjarnasíður eru byggðar úr commiti sem
rataði aldrei á `main`. Ósamræmi milli síðna er því vænt og skráð sérstaklega.

---

## 3. Rit og greinar

Tvær frumheimildir eru **nefndar** í frosna viðmiðinu. Þær eru skráðar hér
nákvæmlega eins og viðmiðið nefnir þær — hvorki meira né minna. Hvorug hefur
verið sótt og lesin í þessu verkefni, svo fullar ritfangaupplýsingar vantar
(kafli 5).

| Tilvísun eins og viðmiðið nefnir hana | Ár | Notuð fyrir | Hvar hún er nefnd |
|---|---|---|---|
| Veðurstofa Íslands, skýrsla **VÍ 2009-013**, kafli 4.3 | 2009 | Umfjöllun um stærðarkvarðann `Mlw` — af hverju hann er hvorki umreiknaður né merktur Richter | `vidmid/vefur/capstone/earthquakes.html` |
| **Monroe, Colaresi & Quinn** | 2008 | Aðferðin að baki z-gildum úr log-odds hlutfalli með Dirichlet-prior (einkennandi orð Phoebe) | `vidmid/phoebe-stats/README.md` |

Titlar, tímarit og slóðir eru **ekki** skráð hér vegna þess að viðmiðið gefur þau
ekki. Þau verða að koma úr heimildunum sjálfum þegar þær eru sóttar.

---

## 4. Verkfæri og forsendur

| Atriði | Gildi | Heimild |
|---|---|---|
| Hnit VR-II | 64,1386922, −21,9556406 | Nominatim (OpenStreetMap), flett upp 2026-09-03 |
| Jarðarradíus í fjarlægðarreikningi | 6371,0088 km | `src/python/vinnsla/vedurstodvar_samanburdur.py` |
| Python | eingöngu staðalsafnið — engir pakkar, engin framework (regla 10) | `CLAUDE.md` |

---

## 5. Óstaðfest — það sem vantar enn

Þetta eru **opnar spurningar**, ekki fullyrðingar. Engin þeirra má verða að
staðhæfingu á vefsíðunni fyrr en hún er staðfest.

| # | Spurning | Af hverju hún er opin | Hver á að leysa |
|---|---|---|---|
| 1 | Hvaða leyfi gildir um Hagstofugögnin? | `provenance.json` safnsins skráir ekkert leyfi og skilmálar Hagstofunnar voru ekki lesnir í upprunaverkefninu | P1.3 / P4.3 |
| 2 | Hvaða leyfi gildir um Nominatim-uppflettinguna? | Hnitin voru flett upp en leyfi ekki skráð | P1.4 |
| 3 | Af hverju stærð 3–7 og dýpt 0–50 km? | Mörkin eru í kóðanum og í hverri lýsingu, en **rökstuðningur þeirra er hvergi skráður** | Björn (issue #2) |
| 4 | Af hverju aðeins `evaluation_mode=manual`? | Skjalfest er *hvað* sían útilokar (sjálfvirkar greiningar), ekki *af hverju* það val var tekið | Björn (issue #2) |
| 5 | Skilmálar mbl.is fyrir vistun og greiningu eintaks | Engin skilmálalesning er skráð í provenance | P4.3 |
| 6 | Frumheimildirnar í kafla 3 | Hvorug hefur verið sótt; þær eru teknar upp úr viðmiðinu | P0.4 framhald |
| 7 | Uppfærslutími Hagstofusvarsins | Svarið gefur `updated = 9999-12-31T23:59:59Z`, sem er ekki nothæf dagsetning | P1.3 |
