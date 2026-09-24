# Verkefnisreglur — Upplýsingaverkfræði (rannsóknarverkefni)

Þetta skjal er **bindandi regluverk** fyrir þetta repo. Allir — bæði ég (Björn) og
gervigreindaraðstoð (Claude Code) — fara eftir því. Ef regla og vani stangast á,
gildir reglan. Ef regla reynist röng: breytum reglunni fyrst, kóðanum svo.

## 0. Verkefnið í einni málsgrein

Rannsóknarverkefni sem sækir gögn frá **vefþjónustum (API)**, geymir þau í
**SQL-gagnagrunni**, vinnur úr þeim og birtir niðurstöðurnar á **static vefsíðu
(HTML/CSS/JS)** á **íslensku**. Vefsíðan á að vera fagleg, sjónrænt sterk og
auðveld í notkun.

**Gagnaflæðið er einstefna og má aldrei rjúfa:**

```
Vefþjónusta (API)  →  Python (sækja)  →  data/raw/  →  Python (vinna)
                                                           ↓
                                                        SQL-grunnur
                                                           ↓
                                             Python (flytja út JSON)
                                                           ↓
                                             web/gogn/*.json  →  vefsíðan
```

Vefsíðan talar **aldrei** beint við gagnagrunn eða API. Hún les eingöngu
tilbúnar JSON-skrár úr `web/gogn/`. Þetta er það sem gerir síðuna static,
hraða og örugga.

---

## 1. Möppuskipan — gullna reglan

> **Eitt tungumál = ein mappa. Enginn kóði í rót verkefnisins.**

```
.
├── CLAUDE.md                  # þetta skjal (reglurnar)
├── README.md                  # hvað verkefnið er + hvernig á að keyra það
├── .gitignore
│
├── web/                       # ← STATIC VEFSÍÐAN (það sem birtist á netinu)
│   ├── index.html             # forsíða
│   ├── sidur/                 # allar aðrar HTML-síður
│   ├── assets/
│   │   ├── css/               # ALLT CSS hér — ekkert annars staðar
│   │   │   ├── tokens.css     # litir, letur, bil (design tokens)
│   │   │   ├── base.css       # reset + grunnstílar
│   │   │   ├── layout.css     # grind, haus, fótur
│   │   │   └── components/    # einn stíll per eining
│   │   ├── js/                # ALLT JavaScript hér — ekkert annars staðar
│   │   ├── img/
│   │   └── fonts/
│   └── gogn/                  # JSON sem Python flytur út (sjá reglu 5.4)
│
├── src/                       # ← ALLUR ANNAR KÓÐI, AÐSKILINN EFTIR MÁLI
│   ├── python/                # gagnasöfnun, úrvinnsla, útflutningur
│   │   ├── sofnun/            # kall í vefþjónustur
│   │   ├── vinnsla/           # hreinsun og umbreyting
│   │   ├── gagnagrunnur/      # tenging og fyrirspurnir
│   │   ├── utflutningur/      # JSON út í web/gogn/
│   │   └── vidmid/            # provenance og staðfesting á frosna viðmiðinu
│   ├── sql/
│   │   ├── schema/            # töfluskilgreiningar
│   │   ├── migrations/        # númeraðar breytingar: 001_..., 002_...
│   │   ├── queries/           # endurnýtanlegar fyrirspurnir
│   │   └── seeds/             # prófunargögn
│   ├── cpp/                   # C++ (src/ + include/ + CMakeLists.txt)
│   └── java/                  # Java (staðlað pakkatré)
│
├── data/                      # GÖGN — ekki kóði, að mestu utan git
│   ├── raw/                   # óbreytt svör frá API (aldrei breytt handvirkt)
│   ├── processed/             # hreinsuð gögn
│   └── db/                    # gagnagrunnsskráin sjálf (ALDREI í git)
│
├── docs/                      # rannsóknarskjölun, heimildir, aðferðafræði
│   └── vidmid/                # frosið afrit af gamla verkefninu (sjá README þar)
├── tests/                     # prófanir, speglar src/ uppbygginguna
├── scripts/                   # keyrsluskipanir (sækja, byggja, birta)
└── config/                    # stillingar (ALDREI leyndarmál)
```

### 1.1 Reglur um staðsetningu

- Ný skrá fer **alltaf** í möppu sem passar við tungumál hennar og hlutverk.
  Er enginn augljós staður? Þá vantar möppu — búðu hana til og skráðu hana hér.
- **Ekkert** í rót nema skjölun og stillingaskrár verkefnisins í heild.
- `web/` á að vera **sjálfstætt birtanleg**: afritaðu möppuna á vefþjón og
  síðan virkar. Engar tilvísanir út fyrir `web/`.
- Mappa fær `.gitkeep` ef hún þarf að vera til en er tóm.

### 1.2 Skráaheiti

- Möppu- og skráaheiti: **ASCII, lágstafir, bandstrik**. Engin `þ á ð ö í`,
  engin bil. `gagnasofnun-2026.html`, ekki `Gagnasöfnun 2026.html`.
- Íslenskir stafir eiga heima í **efni** síðunnar, ekki í slóðum.
- Nafnavenjur per mál:
  | Mál | Skrár | Föll / breytur | Klasar |
  |---|---|---|---|
  | Python | `snake_case.py` | `snake_case` | `PascalCase` |
  | JavaScript | `kebab-case.js` | `camelCase` | `PascalCase` |
  | CSS | `kebab-case.css` | `--kebab-case` | `.kebab-case` |
  | SQL | `001_kebab_case.sql` | `snake_case` | `snake_case` töflur |
  | C++ | `snake_case.cpp/.h` | `snake_case` | `PascalCase` |
  | Java | `PascalCase.java` | `camelCase` | `PascalCase` |
- Kóðaheiti (breytur, föll, töflur) eru á **ensku**. Efni og skjölun á **íslensku**.

---

## 2. Aðskilnaður HTML / CSS / JS — engar undantekningar

Þetta er kjarnakrafa verkefnisins og er ekki samningsatriði.

- ❌ Ekkert `<style>` inni í HTML. ✅ `<link rel="stylesheet">`.
- ❌ Ekkert `style="..."` attribute. ✅ CSS-klasi.
- ❌ Ekkert `<script>` með kóða inni í HTML. ✅ `<script src="..." defer>`.
- ❌ Ekkert `onclick="..."` / `onchange="..."`. ✅ `addEventListener` í .js-skrá.
- HTML lýsir **byggingu**, CSS lýsir **útliti**, JS lýsir **hegðun**. Ekkert af
  þessu fer yfir í hitt.
- Ein eining (t.d. kortaspjald) = `components/kort.css` + `js/kort.js`.

---

## 3. Vefsíðan — fagleg, falleg, auðrötuð

### 3.1 Sjónrænt kerfi (design tokens)
- **Öll** gildi fyrir liti, letur, bil og skugga eru skilgreind sem CSS-breytur
  í `tokens.css`. Enginn harðkóðaður litur eða px-tala annars staðar.
- Litapalletta: 1 aðallitur, 1 áherslulitur, hlutlaus grátónaskali (5–7 þrep).
  Ekki fleiri. Agi í litum er það sem lætur síðu líta út fyrir að vera fagleg.
- Letur: **hámark 2 leturfjölskyldur** (ein fyrir fyrirsagnir, ein fyrir texta).
  Stærðarskali með föstum þrepum — engar handahófskenndar stærðir.
- Bil: skali byggður á 4px eða 8px grunneiningu. Öll bil eru margfeldi af honum.
- Dökkt þema með `prefers-color-scheme` — leyst með því að endurskilgreina
  tokens, ekki með því að skrifa nýja stíla.

### 3.2 Rötun (navigation)
- Sama haus og fótur á **öllum** síðum, á sama stað, í sömu röð.
- Hámark **3 smellir** í hvaða efni sem er frá forsíðu.
- Núverandi síða er alltaf sjónrænt merkt í valmynd.
- Brauðmylsna (breadcrumbs) á öllum undirsíðum.
- Hver síða svarar strax þremur spurningum í efsta hluta: *Hvar er ég? Hvað er
  hér? Hvert get ég farið næst?*

### 3.3 Aðgengi (skylda, ekki valkvætt)
- `<html lang="is">` á öllum síðum.
- Merkingarbært HTML: `<header> <nav> <main> <article> <footer>`, ein `<h1>`
  per síðu, fyrirsagnir í réttri röð án stökka.
- Litaandstæða minnst **4.5:1** fyrir texta (WCAG 2.1 AA).
- Allt nothæft með lyklaborði; sjáanleg `:focus` umgjörð — aldrei `outline: none`
  án þess að setja eitthvað betra í staðinn.
- Allar myndir með `alt`-texta á íslensku. Skrautmyndir fá `alt=""`.
- Litur einn og sér má aldrei vera eina merkingarberan (bættu við tákni/texta).

### 3.4 Frammistaða (þak sem má ekki fara yfir)
- Fyrsta hleðsla síðu: **< 500 KB** samtals.
- Myndir: WebP, `width`/`height` sett, `loading="lazy"` neðan við fold.
- **Engin JS-framework** og engin ónauðsynleg CDN-tengsl. Vanilla JS.
- Öll `<script>` með `defer`.
- Síðan verður að vera læsileg og rötunarhæf þótt JavaScript sé slökkt.

### 3.5 Skjáaðlögun
- Mobile-first: grunnstíll fyrir síma, `min-width` media queries upp á við.
- Virkar frá 320px upp úr. Ekkert lárétt skrun.
- Smellifletir minnst 44×44px.

---

## 4. Gagnasöfnun frá vefþjónustum

- **Engir lyklar í kóða.** API-lyklar koma úr umhverfisbreytum (`.env`, sem er
  í `.gitignore`). `config/` geymir aðeins dæmi: `.env.example`.
- Hvert svar frá API er vistað óbreytt í `data/raw/` með tímastimpli áður en
  nokkuð er unnið úr því. Hrágögnum er **aldrei** breytt eftir á.
- Hver gagnasöfnun skráir: **hvaða þjónusta, hvaða slóð, hvenær sótt, hvaða
  breytur**. Þetta fer í `docs/` og er forsenda þess að rannsóknin sé endurtekjanleg.
- Virðum þjónustuna: hraðatakmörkun (delay milli kalla), `User-Agent` sem
  auðkennir verkefnið, endurtilraunir með vaxandi bið, og skilmálar þjónustunnar
  lesnir áður en sótt er.
- Sækjum aldrei sömu gögn tvisvar að óþörfu — athugum `data/raw/` fyrst.
- Öll netköll í `try/except` með skiljanlegri villu. Aldrei þögul villa.

---

## 5. Gagnagrunnur (SQL)

- **Fyrirspurnir með breytum, aldrei strengjasamsetning.** Þetta er öryggisregla:
  `cur.execute("... WHERE id = ?", (id,))` — aldrei f-strengur inn í SQL.
- Öll uppbygging grunnsins verður til úr `src/sql/migrations/`, númeruðum í röð.
  Grunnurinn er aldrei breytt handvirkt í GUI-tóli.
- Migration er **aldrei** breytt eftir að hún hefur verið keyrð — ný migration í staðinn.
- Gagnagrunnsskráin sjálf (`data/db/`) fer **aldrei** í git. Hún er afleiðing,
  ekki frumgagn — það á að vera hægt að endurbyggja hana frá `raw` + migrations.
- Hver tafla hefur frumlykil, skýr nöfn í fleirtölu (`measurements`), og
  athugasemd í schema um hvaðan gögnin koma.
- **5.4 Útflutningur í vefinn:** `src/python/utflutningur/` skrifar JSON í
  `web/gogn/`. Þessar JSON-skrár eru **afleiddar** — þeim er aldrei breytt
  handvirkt. Hver skrá inniheldur `{"uppfaert": "<ISO dagsetning>", "gogn": [...]}`
  svo síðan geti sýnt hvenær gögnin voru síðast uppfærð.

---

## 6. Kóðagæði (öll mál)

- Ein skrá = eitt hlutverk. Fer skrá yfir ~300 línur → hún er líklega að gera
  of margt.
- Föll gera eitt og heita eftir því sem þau gera.
- Engir töfratölur eða töfrastrengir — nefndir fastar efst í skrá eða í `config/`.
- Villur eru meðhöndlaðar eða látnar falla með skýringu. **Aldrei þaggaðar.**
- Athugasemdir útskýra **af hverju**, ekki hvað. Kóðinn sjálfur útskýrir hvað.
- Python: fylgjum PEP 8, gerðarmerkingar (type hints) á opinberum föllum,
  docstring á hverju falli sem aðrir kalla í.
- Kóði sem er ekki í notkun er eytt, ekki kommentaður út. Git man hann.

---

## 7. Git

- Aldrei committa: `.env`, innihald `data/db/`, stór hrágögn, `.idea/`, `__pycache__/`.
- Commit-skilaboð á forminu `svið: hvað var gert` — t.d.
  `vefur: bæti við brauðmylsnu á undirsíður`, `sql: migration 003 fyrir mælingar`.
- Eitt commit = ein rökrétt breyting. Ekki blanda saman uppröðun skráa og
  nýrri virkni í sama commit.
- Vinna á greinum, `main` á alltaf að vera í nothæfu ástandi.

---

## 8. Rannsóknarheiðarleiki

- Sérhver tala sem birtist á vefsíðunni á sér rekjanlega leið aftur í hrágögn.
- Allar heimildir skráðar í `docs/heimildir.md` með slóð og dagsetningu.
- Aðferðafræði skráð í `docs/` **jafnóðum**, ekki í lokin.
- Þekktar takmarkanir gagnanna eru birtar á síðunni, ekki faldar.

---

## 9. Verklok — hvenær er verk búið?

Verk telst ekki klárað fyrr en allt þetta stenst:

1. Skráin er á réttum stað samkvæmt reglu 1.
2. HTML/CSS/JS eru aðskilin samkvæmt reglu 2.
3. Síðan virkar í síma (320px) og á borðtölvu.
4. Lyklaborðsrötun og `alt`-textar í lagi.
5. Engin villa í console vafrans.
6. Engin leyndarmál í kóðanum.
7. Efni á íslensku, kóðaheiti á ensku.
8. Breytingin er committuð með lýsandi skilaboðum.

---

## 10. Reglur fyrir gervigreindaraðstoð (Claude Code)

- Lestu þetta skjal áður en þú býrð til skrá og fylgdu reglu 1 um staðsetningu.
- Búðu **ekki** til nýjar möppur í rót án þess að spyrja.
- Bættu **ekki** við pökkum, frameworkum eða CDN-tenglum án þess að spyrja —
  sjálfgefið er hreint HTML/CSS/JS og Python-staðalsafnið.
- Ekki skrifa inline stíla eða inline script "bara til að prófa".
- Ekki breyta gögnum í `data/raw/` né JSON í `web/gogn/` handvirkt.
- Ekki keyra eyðandi skipanir á gagnagrunn eða git-sögu án staðfestingar.
- Efni sem notandi les er á **íslensku**. Kóðaheiti á ensku.
- Þegar þú klárar: segðu hvaða reglur úr kafla 9 þú staðfestir og hverjar ekki.
