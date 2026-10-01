# Aðgengi vefsíðunnar

Úttekt á öllum tólf síðum `web/` gegn WCAG 2.1 AA (issue #26). Skjalið segir
hvernig aðgengi er tryggt og hvernig mælingin er endurtekin. Reglurnar eru í
[`../CLAUDE.md`](../CLAUDE.md) (3.3, 3.5, 9), uppbyggingin í
[`vefur-beinagrind.md`](vefur-beinagrind.md).

---

## 1. Hvernig hlutirnir eru

| Atriði | Hvernig |
|---|---|
| Tungumál | `<html lang="is">` á öllum síðum |
| Kennileiti | `header`, `nav`, `main`, `article`, `footer`; ein `h1`, fyrirsagnir án stökka |
| Stökktengill | „Fara beint í efni“ er fyrsti tengill allra síðna og birtist við fókus |
| Fókus | Ein umgjörð í `base.css` (`:focus-visible`, 3 px, token `--fokus`). Kort á forsíðu teikna hana utan um allt kortið |
| Núverandi síða | `aria-current` plús fylltur flötur — aldrei litur einn og sér |
| Töflur | `<caption>` og `th scope="col"`; töflur úr JavaScript koma úr `buildTable` sem setur hvort tveggja |
| Myndir | Engar `<img>` eru á síðunum; engin myndrit eru birt enn. Myndrit úr Python fá gagnatöflu (sjá [`myndrit.md`](myndrit.md)) |
| Snertifletir | `--smellisvaedi` er 44 px; tenglar í valmynd, brauðmylsnu og kortum fylla það |
| Mjór skjár | Ekkert lárétt skrun á 320 px; töflur skruna innan `.tafla-umgjord` |
| Án JavaScript | Allt meginmál og öll valmynd er í HTML; gagnahlutar hafa `<noscript>` með tengli á JSON-skrána |

---

## 2. Mæld textaandstæða

Mælt í Chromium á 320 px með `colorScheme` ljósu og dökku. Skriftan fór yfir
hvern textahnút á síðunni, tók **reiknaðan** textalit og bakgrunn (lög með
gagnsæi lögð saman) og reiknaði hlutfall samkvæmt WCAG. Taflan sýnir lægsta
gildið á hverri síðu; lágmark er 4,5:1 (3:1 fyrir stóran texta).

| Síða | Ljóst | Dökkt | Textahnútar | Niðurstaða |
|---|---|---|---|---|
| `index.html` | 5,50 | 6,29 | 86 | stenst |
| `sidur/skjalftavaktin.html` | 4,69 | 6,29 | 75 | stenst |
| `sidur/friends-gagnasagan.html` | 4,69 | 6,29 | 57 | stenst |
| `sidur/phoebe-tolfraedi.html` | 4,69 | 6,29 | 59 | stenst |
| `sidur/phoebe-central-perk.html` | 4,69 | 6,29 | 59 | stenst |
| `sidur/phoebe-tmdb.html` | 4,69 | 6,29 | 58 | stenst |
| `sidur/uppahalds-video.html` | 4,69 | 6,29 | 55 | stenst |
| `sidur/phoebe-tribute.html` | 4,69 | 6,29 | 55 | stenst |
| `sidur/hagstofan.html` | 4,69 | 6,29 | 58 | stenst |
| `sidur/vedurstodvar.html` | 4,69 | 6,29 | 56 | stenst |
| `sidur/mbl-regex.html` | 4,69 | 6,29 | 56 | stenst |
| `sidur/adferdafraedi.html` | 4,69 | 6,29 | 72 | stenst |

Lægsta ljósa gildið (4,69) er „Efni í vinnslu“ í biðstöðueiningunni; lægsta
dökka (6,29) er flokksmerkið í síðuhaus. Efnisleg gögn á síðunum eru enn
fá — tölurnar breytast þegar síðuverkin bæta við texta, svo prófin í kafla 4
gæta lykilparanna.

### Lykilpör úr `tokens.css`

Reiknað úr token-gildunum (prófað í `tests/test_vefur_adgengi.py`). Dálkar:
`--bak`, `--bak-upphaekkad`, `--bak-daufur`.

| Texti | Ljóst | Dökkt |
|---|---|---|
| `--texti` | 13,88 / 14,75 / 12,79 | 16,67 / 15,20 / 15,75 |
| `--texti-daufur` | 6,33 / 6,72 / 5,83 | 10,32 / 9,41 / 9,75 |
| `--tengill` | 6,21 / 6,60 / 5,72 | 8,96 / 8,17 / 8,46 |
| `--tengill-yfir` | 10,13 / 10,76 / 9,33 | 11,37 / 10,37 / 10,75 |
| `--ahersla-700` | 6,06 / 6,44 / 5,58 | 7,24 / 6,60 / 6,84 |
| `--texti-a-lit` á `--adal-500` | 6,60 | 6,60 |
| `--fokus` (umgjörð, lágmark 3:1) | 4,05 / 4,30 / 3,73 | 7,24 / 6,60 / 6,84 |

---

## 3. Niðurstaða úttektar

| Gátlisti | Niðurstaða |
|---|---|
| `lang`, ein `h1`, fyrirsagnir, kennileiti | Stenst á öllum 12 síðum |
| Textaandstæða í báðum þemum | Stenst, sjá kafla 2 |
| Litur ekki eina merkingin | Stenst (valmynd: `aria-current` + fylling + feitt letur; stöðumerki hafa texta) |
| Lyklaborð: fyrsta Tab, fókusumgjörð | Stenst. Fyrsta Tab fer á „Fara beint í efni“; allir fókusanlegir hlutir hafa umgjörð |
| Töflur | Stenst (ein tafla, á Skjálftavaktinni: `caption` + `scope="col"`) |
| Snertifletir 44 × 44 px | **Lagað:** brauðmylsnutengillinn „Þema“ var 39 px breiður; fær `min-width`. Aðrir stakir tenglar ≥ 44 × 44 |
| 320 px án lárétts skruns | Stenst á öllum 12 síðum í báðum þemum |
| Console án villu eða viðvörunar | **Lagað:** tvær villur á Skjálftavaktinni (sjá hér að neðan). Engin villa á neinni síðu eftir það |
| Án JavaScript | Stenst: meginmál og valmynd eru í HTML; Skjálftavaktin sýnir tengil á JSON-skrána |

Lagfæringarnar á Skjálftavaktinni: gagnahlutinn leitaði að `samantekt` inni í
`gogn` en útflutningurinn geymir hana í `lysigogn` (reitir byrja nú á
`lysigogn.`), og mánaðartaflan bjóst við mánaðaskrá en skráin geymir einn dag
per línu (teiknarinn tekur nú dagana saman í mánuði).

### Ekki staðfest

- Skjálesarar (NVDA, VoiceOver) voru ekki prófaðir; athugað var með
  merkingu HTML og fókusröð, ekki upplesinn texta.
- Aðeins Chromium. Firefox og Safari eru ótestuð.
- Myndrit eru ekki á síðunum enn, svo textaleg samsvörun þeirra er óprófuð
  á síðunum sjálfum (hún er skilgreind í `myndrit.md`).
- Snertiflötur inni í löngum texta (inline tenglar) er undanskilinn
  samkvæmt WCAG 2.5.8.

---

## 4. Hvernig mælingin er endurtekin

**Án vafra:** `python3 -m unittest discover -s tests`. Prófin
`tests/test_vefur.py` og `tests/test_vefur_adgengi.py` athuga `lang`, `h1`,
fyrirsagnaröð, `alt`, töflur, stökktengil, `outline: none` án staðgengils,
snertiflatatokenið og andstæðu allra lykilpara í báðum þemum.

**Í vafra (Playwright, Chromium):**

1. Þjóna `web/`: `python3 -m http.server 8765 --directory web`.
2. Fyrir hverja síðu og hvort `colorScheme` (`light`, `dark`) á 320 px
   breidd: lesa `getComputedStyle` á hverjum textahnút, leggja gagnsæ
   bakgrunnslög saman og reikna hlutfallið; bera saman við 4,5 (3 fyrir
   texta ≥ 24 px eða ≥ 18,66 px feitan).
3. Lesa `getBoundingClientRect` á öllum `a`, `button`, `input` og `summary`;
   skrá þá sem eru undir 44 px (inline tenglar í texta undanskildir).
4. Bera `scrollWidth` saman við `clientWidth`.
5. Ýta á Tab þar til hringurinn er búinn; fyrsti fókus á að vera stökktengillinn
   og `outline-style` (eða umlykjandi `:focus-within`) má ekki vera `none`.
6. Hlusta á `console` (`error`, `warning`), `pageerror` og svör ≥ 400.
7. Opna aftur með `javaScriptEnabled: false` og lesa `main`.

Skriftan er ekki geymd í repo-inu (regla 6); skrefin hér duga til að endurgera hana.
