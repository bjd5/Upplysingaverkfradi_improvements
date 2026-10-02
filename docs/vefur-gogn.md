# Gagnalag vefsins — frá `web/gogn/` á síðuna

Afurð **P3.2** (issue #19). Skjalið lýsir sameiginlega JS-laginu sem allar
gagnasíður (#20–#24) nota til að sækja og birta gögn úr `web/gogn/`, og
mynstrinu sem þær eiga að fylgja. Reglurnar sjálfar eru í
[`../CLAUDE.md`](../CLAUDE.md).

---

## 0. Sniðið sem lagið les

Útflutningurinn (`src/python/utflutningur/json_skrif.py`) skrifar hverja skrá í
`web/gogn/` á föstu sniði, og `gogn.js` hafnar öllu öðru:

```json
{
  "uppfaert": "2026-09-10T11:46:23+00:00",
  "heimild":  "Veðurstofa Íslands — api.vedur.is/quakes/events (CC BY 4.0)",
  "gogn":     [ {"dagur": "2023-11-01", "fjoldi": 1, …}, … ],
  "lysigogn": { "samantekt": {"atburdir": 334, …}, "manudir": [ … ], … }
}
```

| Reitur | Krafa | Hvað |
|---|---|---|
| `uppfaert` | skylda | ISO 8601 með tímabelti |
| `heimild` | skylda | óauður texti |
| `gogn` | skylda | **alltaf listi af röðum** (hlutum) — aðalgögn skrárinnar |
| `lysigogn` | valfrjálst (ekki í `yfirlit.json`) | hlutur: það sem síðan þarf til að lesa gögnin — samantektir, afmörkun, fyrirspurn |
| annað | **bannað** | skránni er hafnað með sýnilegri villu, eins og útflutningurinn gerir |

Hvað er í `gogn` og `lysigogn` hverrar skrár sést best í skránni sjálfri.

---

## 1. Skrárnar

| Skrá | Hlutverk | Á hvaða síðum |
|---|---|---|
| `web/assets/js/gogn.js` | Sækir, staðfestir og sníður. **Eina skráin sem kallar í `fetch`.** | Öllum gagnasíðum |
| `web/assets/js/gagnahluti.js` | Birtir hleðslu-, villu- og upprunastöðu út frá `data-gogn`-hooks; byggir töflur | Öllum gagnasíðum |
| `web/assets/js/stada-gagna.js` | Forsíðan: „Gögn uppfærð …“ úr `yfirlit.json` | `index.html` |
| `web/assets/js/<síða>.js` | Síðusértækir teiknarar (valkvætt) | Einni síðu |
| `web/assets/css/components/gagnahluti.css` | Útlit hleðslu, villu, varaleiðar og gagnataflna | Öllum gagnasíðum |
| `web/assets/css/components/stada-gagna.css` | „Gögn uppfærð … · Heimild: …“ (líka villuástand) | Öllum gagnasíðum |

Röðin skiptir máli og `defer` heldur henni:

```html
<link rel="stylesheet" href="../assets/css/components/stada-gagna.css">
<link rel="stylesheet" href="../assets/css/components/gagnahluti.css">
<script src="../assets/js/valmynd.js" defer></script>
<script src="../assets/js/gogn.js" defer></script>
<script src="../assets/js/gagnahluti.js" defer></script>
<script src="../assets/js/skjalftavaktin.js" defer></script>  <!-- valkvætt -->
```

Slóðin á gagnaskrárnar er reiknuð **frá `gogn.js` sjálfri**
(`assets/js/` → `../../gogn/`), ekki frá síðunni. Síða nefnir því aðeins
skráarheitið (`skjalftar.json`) og sama markup virkar í `index.html` og
`sidur/*.html`. Engin slóð fer út fyrir `web/` (regla 1.1).

---

## 2. Mynstrið: gagnahluti í HTML

Flestar síður þurfa **engan eigin JS**. Tölur eru merktar beint í HTML:

```html
<section class="gagnahluti" data-gogn="skjalftar.json"
         data-gogn-teiknari="skjalftar-manudir"
         aria-labelledby="urtak-titill">
  <h3 id="urtak-titill">Úrtakið í tölum</h3>
  <noscript>
    <p class="gogn-stada">Tölurnar hér eru settar inn með JavaScript. Án
    þess má lesa þær beint úr <a href="../gogn/skjalftar.json">gagnaskránni</a>.</p>
  </noscript>
  <div data-gogn-efni hidden>
    <dl class="stadreyndir">
      <div>
        <dt>Atburðir</dt>
        <dd data-gogn-reitur="lysigogn.samantekt.atburdir"></dd>
      </div>
    </dl>
  </div>
</section>
```

| Hook | Skylda | Merking |
|---|---|---|
| `data-gogn="skra.json"` | já | Gagnahluti. Skráarheiti í `web/gogn/`, án möppu. |
| `data-gogn-efni` + `hidden` | já, ef reitir | Það sem birtist þegar gögnin eru komin. Falið án JS og við villu — aldrei auðir reitir. |
| `data-gogn-reitur="lysigogn.a.b"` | nei | `textContent` fær gildið á slóðinni. Slóðavenjan er í kafla 2.1. Verður að vera tala eða strengur. |
| `data-gogn-teiknari="nafn"` | nei | Teiknari sem síðuskrá skráði (kafli 3). |
| `data-gogn-uppruni` | nei | Hvar „Gögn uppfærð … · Heimild: …“ á að standa. Vanti hann bætist `<p class="stada-gagna">` við neðst í hlutanum. |
| `<noscript>` | já | Varaleið án JavaScript (regla 3.4) — kafli 5. |

### 2.1 Slóðavenjan í `data-gogn-reitur`

Slóðin er lesin **frá rót skjalsins** og **byrjar alltaf á `lysigogn.` eða
`gogn.`**. Rótin er skrifuð út svo sá sem les HTML-ið sjái strax hvaðan talan
kemur. Punktur skilur að þrep og tala er sæti í lista (talið frá 0):

| Slóð | Gildi í `skjalftar.json` |
|---|---|
| `lysigogn.samantekt.atburdir` | `334` |
| `lysigogn.samantekt.dypt_km.midgildi` | `4.67` → „4,67“ |
| `lysigogn.manudir.0.atburdir` | `330` |
| `gogn.2.fjoldi` | `24` (þriðja röðin) |
| `samantekt.atburdir` | **villa** — rótina vantar |
| `uppfaert`, `heimild` | **villa** — upprunalínan birtir þau sjálfkrafa |

Stakar tölur (heildir, miðgildi, fjöldi) eru nær alltaf í `lysigogn`. Raðirnar
í `gogn` eru fyrir töflur og myndrit (kafli 3); `gogn.<n>.` í reit er aðeins
fyrir tilvik þar sem röðin er föst. Slóð sem vísar á hlut, lista, `null` eða
ekkert gefur sýnilega villu í hlutanum, og `tests/test_vefur_gogn.py` fellur á
sama tilviki áður en það kemst á vefinn.

### 2.2 Ástand

Ástandið sem `gagnahluti.js` setur á hlutann: `data-gogn-stada="hledst"`
(með `aria-busy="true"` og „Sæki gögn …“ í `role="status"`), svo `"tilbuid"`
eða `"villa"`.

---

## 3. Teiknarar — þegar reitir duga ekki

Töflur og annað sem byggist á listum — raðirnar í `doc.gogn` eða listi í
`doc.lysigogn` — fer í síðuskrá (`web/assets/js/<síða>.js`)
sem skráir teiknara. Hann keyrir **eftir** að reitirnir eru fylltir og **áður**
en efnið birtist:

```js
window.DataSection.registerRenderer("skjalftar-manudir", function (doc, section) {
  // doc = {uppfaert, heimild, gogn: [raðir], lysigogn}, þegar staðfest
  const table = window.DataSection.buildTable({
    caption: "Atburðir eftir mánuðum",
    columns: [
      { heading: "Mánuður", key: "manudur" },
      { heading: "Atburðir", key: "atburdir", numeric: true }
    ],
    rows: doc.lysigogn.manudir        // eða doc.gogn fyrir aðalraðirnar
  });
  section.querySelector("[data-gogn-efni]").appendChild(table);
});
```

Kasti teiknarinn villu birtist hún í hlutanum eins og aðrar villur, og efnið
helst falið.

**Tafla sem þarf að virka án JavaScript** (t.d. gagnatafla myndrits, ákvörðun
#17) á **ekki** að byggjast svona — hún verður að vera í HTML-inu sjálfu. Sjá
[`myndrit.md`](myndrit.md) kafla 7.

---

## 4. JS-viðmótið

`window.SiteData` (`gogn.js`):

| Fall | Skilar |
|---|---|
| `load("skra.json")` | `Promise<{uppfaert, heimild, gogn, lysigogn}>`. Hver skrá sótt einu sinni á síðu. Hafnar alltaf með `DataError` með íslenskum skilaboðum. |
| `fieldAt(doc, "lysigogn.a.b")` | Tala eða strengur eftir slóðavenju reitanna (kafli 2.1); annars `DataError` |
| `valueAt(hlutur, "a.0.b")` | Gildið á punktaslóð í hvaða hlut eða röð sem er, eða `undefined` |
| `formatNumber(4.67)` | `"4,67"` — sjá kafla 6 |
| `formatDate("2026-09-10T…")` | `"10. september 2026"` |
| `formatMonth("2023-11")` | `"nóvember 2023"` |
| `fileUrl("skra.json")` | Full slóð skrárinnar |
| `DataError` | Villuklasi; `message` má sýna lesanda |

`window.DataSection` (`gagnahluti.js`):

| Fall | Hlutverk |
|---|---|
| `registerRenderer(nafn, fn)` | Skráir teiknara: `fn(doc, section)` |
| `buildTable({caption, columns, rows})` (`columns[].key` er punktaslóð innan raðar) | `<div class="tafla-umgjord"><table class="gagnatafla">…` með `createElement` |
| `fillStatus(el, iso, texti)` | Fyllir `.stada-gagna`: „Gögn uppfærð … · texti“ |
| `fillStatusError(el, villa)` | Sama eining í villuástandi: „Villa: …“ |

**Aldrei `innerHTML`** með gögnum — gagnaskrá má ekki verða innspýtingarleið.
Prófin falla ef `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
`document.write` eða `eval` kemur fyrir í `web/assets/js/`.

---

## 5. Án JavaScript (regla 3.4)

Síðan er læsileg og rötunarhæf án JS: haus, valmynd, brauðmylsna, allur
fastur texti og tenglar standa. Það sem hverfur eru **aðeins** tölurnar sem
JS fyllir inn, og þá:

- er `data-gogn-efni` falið með `hidden`, svo lesandinn sér ekki auða reiti
  eða hálfa töflu;
- segir `<noscript>` hvað vantar og **tengir beint á gagnaskrána**, sem er
  rekjanleg og læsileg í vafra.

Forsíðan hefur sjálfgefinn texta í `data-stada-gagna`-reitnum sem skriftan
skiptir út.

---

## 6. Tölur og dagsetningar

**Tölurnar eru þegar námundaðar í JSON** (útflutningurinn, `src/python/utflutningur/`)
og JS **námundar aldrei aftur**. `formatNumber` breytir aðeins sniði, í sama
sniði og `utflutningur/islenskt_snid.py`:

| JSON | Á síðunni |
|---|---|
| `61161` | `61.161` (punktur milli þúsunda) |
| `4.67` | `4,67` (tugabrotskomma) |
| `3.0` | `3` (JSON gerir engan greinarmun) |
| `"43 einstakar fréttir"` | óbreytt — strengir eru þegar sniðnir |

`lysigogn.aukastafir` segir með hve mörgum aukastöfum útflutningurinn námundaði
— það er **hámark**, ekki birtingarsnið. JS fyllir ekki upp með núllum: `334` í
skrá með `aukastafir: 2` er „334“, ekki „334,00“.

Þurfi tala að birtast með föstum fjölda aukastafa (t.d. `3,0`) á
útflutningurinn að skrifa hana sem streng.

Dagsetningar fara í gegnum `Intl.DateTimeFormat("is-IS")` með tímabelti
`Atlantic/Reykjavik`. Styðji vafrinn ekki íslensku fellur Intl hljóðlaust á
ensku; lagið greinir það og notar þá eigin mánaðaheiti. ISO-strengur fer
aldrei beint á skjáinn.

---

## 7. Villur (regla 6)

Allar villur sjást **á síðunni**, á íslensku, í hlutanum sem þær varða — og
líka í console fyrir þróun. Þær eru aldrei þaggaðar og síðan brotnar ekki:

| Tilvik | Skilaboð |
|---|---|
| Netvilla | „Ekki náðist samband til að sækja „skjalftar.json“.“ |
| 404 / annar kóði | „Gagnaskráin „…“ fannst ekki (villa 404).“ / „fékkst ekki (villa 500).“ |
| Ekki gilt JSON | „Gagnaskráin „…“ er gölluð.“ |
| Skyldureit vantar | „Í gagnaskrána „…“ vantar reitinn „heimild“.“ |
| `gogn` ekki listi af röðum | „Gögnin í „…“ eru ekki listi af röðum.“ |
| `lysigogn` ekki hlutur | „Lýsigögnin í „…“ eru á röngu sniði.“ |
| Óþekktur reitur | „Óþekktur reitur „…“ í „…“.“ |
| Reitur vísar ekki á tölu/texta | „Gildið „lysigogn.samantekt.x“ er ekki tala eða texti í gagnaskránni.“ |
| Slóð án rótar | „Slóðin „samantekt.x“ verður að byrja á „lysigogn.“ eða „gogn.“.“ |
| Teiknari ekki skráður | „Enginn teiknari er skráður undir „…“.“ |

Villuboxið (`.gogn-villa`, `role="alert"`) byrjar á „Ekki tókst að birta
gögnin í þessum hluta.“ og endar á tengli á gagnaskrána. Rauði kanturinn er
viðbót; textinn ber merkinguna (regla 3.3).

---

## 8. Staðfesting

`tests/test_vefur_gogn.py` (staðalsafnið eitt) staðfestir: aðeins `gogn.js`
kallar í `fetch`; ekkert `innerHTML`/`eval`; lagið hleðst á undan notendum
sínum; hver `data-gogn`-skrá er til og á sniði reglu 5.4 (`gogn` listi af
röðum, `lysigogn` hlutur, engir aðrir reitir); hver `data-gogn-reitur` byrjar á
`lysigogn.` eða `gogn.` og vísar á tölu eða streng í skránni; hver gagnahluti hefur
`<noscript>` og falið efni; hver hook, teiknari og CSS-klasi sem JS notar er
til; og JS-skrárnar eru undir 300 línum og 60 KB samanlagt.

**Á undan birtingu** (`.github/workflows/pages.yml`, við hvert push á `main`)
keyrir `scripts/stadfesta-vef.sh`: hver skrá í `web/gogn/` stenst sama snið og
útflutningurinn skrifar (`json_skrif.sem_baeti`), engin útflutt skrá vantar og
hver gagnaskrá sem síða vísar í er til. Annars er ekkert birt.

`UndirslodTest` (`tests/test_vefur.py`) keyrir líka á undan birtingu: engin slóð
í HTML, CSS eða JS byrjar á `/` né fer út fyrir `web/`, svo síðan virkar undir
`bjd5.github.io/Upplysingaverkfradi_improvements/`.

Vafraprófin (Chromium, Playwright) eru handkeyrð og ekki í `unittest`-safninu.
Þau staðfestu 29.9.2026, á nýja sniðinu: engin villa í console, gögnin
birtast, níu villutilvik birtast á síðunni (þ.m.t. `gogn` ekki listi),
tafla úr 61 `gogn`-röð fær íslenskt snið, síðan virkar án JS, og 320 px í báðum þemum
án lárétts skruns.

---

## 9. Phoebe-síðurnar: súlur úr JS og töflur í HTML (issue #24)

`phoebe-tolfraedi.html` og `phoebe-central-perk.html` sameina tvö mynstur:

- **Myndritið** er teiknað af `web/assets/js/phoebe-myndrit.js` með
  `createElementNS` inn í `[data-myndrit]`, í stíl `components/stolparit.css`
  (litir úr `--myndrit-*`). Það er viðbót: súlurnar byrja í núlli og viðmiðslína
  er strikuð og nefnd með orðum. matplotlib er ekki notað hér — SVG úr Python
  (`myndrit.md`) bíður þess að pakkinn sé settur upp.
- **Taflan** við hvert myndrit er í HTML-inu sjálfu og virkar án JS. Hver tala
  er rekjanleg: `data-reitur` (lykill), næsta `data-rod` ofar (röðin, t.d.
  `gogn[thattarod=1,persona=Phoebe]`) og næsta `data-skra` ofar (gagnaskráin).
  `tests/test_vefur_phoebe.py` ber textann saman við gagnaskrána á íslensku
  sniði og fellur ef tala í HTML víkur frá henni.

`data-gogn-reitur` nær aðeins inn í `gogn`, ekki `lysigogn`. Tölur sem búa í
`lysigogn` fara því í töflur með `data-rod`, og teiknarinn les þær beint úr
skjalinu.
