# Beinagrind vefsíðunnar og sjónræna kerfið

Afurð verkpakka **P3.1** (issue #18). Þetta skjal lýsir uppbyggingunni sem
síðuverkin **P3.4–P3.11** byggja ofan á: hvaða þrettán síður eru til, hvernig
ratað er um þær, hvaða einingar eru tiltækar og hvað er þegar staðfest.

Reglurnar sjálfar eru í [`../CLAUDE.md`](../CLAUDE.md); hér er hvernig þeim er
mætt í `web/`.

---

## 1. Síðurnar þrettán, í þremur flokkum

Síðunum er skipt í **Þema**, **Friends** og **Viðauka** (ákveðið 2026-09-28,
sjá [`endurbygging.md`](endurbygging.md) kafla 3). Flokkarnir eru skráðir í
`THEMA`, `FRIENDS` og `VIDAUKI` efst í `tests/test_vefur.py`.

| Flokkur | Slóð | Fyrirsögn | Gagnasafn |
|---|---|---|---|
| — | `web/index.html` | Gögn úr vefþjónustum, greind og gerð skiljanleg | — |
| Þema | `web/sidur/skjalftavaktin.html` | Skjálftavaktin | 1 — Veðurstofan, jarðskjálftar |
| Friends 01 | `web/sidur/friends-gagnasagan.html` | Friends-gagnasagan *(biðstaða)* | 6 — handrit |
| Friends 02 | `web/sidur/phoebe-tolfraedi.html` | Plass, nærvera og tengsl Phoebe | 6 — handrit |
| Friends 03 | `web/sidur/phoebe-central-perk.html` | Söngur Phoebe í Central Perk | 6 — handrit |
| Friends 04 | `web/sidur/phoebe-tmdb.html` | Hlutverkið í gagnagrunni TMDB | 5 — TMDB |
| Friends 05 | `web/sidur/uppahalds-video.html` | Okkar uppáhalds myndbönd *(biðstaða)* | — |
| Friends 06 | `web/sidur/phoebe-tribute.html` | Til heiðurs Phoebe *(biðstaða)* | — |
| Viðauki A | `web/sidur/hagstofan.html` | Brautskráning af háskólastigi | 2 — Hagstofan |
| Viðauki B | `web/sidur/vedurstodvar.html` | Veðurstöðvar Veðurstofunnar | 3 — Veðurstofan, stöðvar |
| Viðauki C | `web/sidur/mbl-regex.html` | Reglulegar segðir á fréttasíðu | 4 — mbl.is |
| Viðauki D | `web/sidur/adferdafraedi.html` | Aðferðafræði | — |

Síðurnar `gogn.html`, `nidurstodur.html` og `um.html` úr fyrstu beinagrindinni
voru **felldar niður**: þær eru ekki í umfanginu sem var ákveðið í
[`endurbygging.md`](endurbygging.md) kafla 3. Efni þeirra á heima á
aðferðafræðisíðunni (heimildir, takmarkanir) og á forsíðunni (markmið).
Gamli tengillinn `um.html#heimildir` varð `adferdafraedi.html#heimildir`.

---

## 2. Rötun

### Aðalvalmyndin — einn liður per flokk, eins á öllum síðum

```
Forsíða · Þema · Friends · Viðauki
```

Hver flokksliður vísar á fyrstu síðu flokksins (`skjalftavaktin.html`,
`friends-gagnasagan.html`, `hagstofan.html`). Á öllum Friends- og
Viðaukasíðum er **undirvalmynd** efst sem heldur systursíðunum í einum smelli.
Þema hefur aðeins eina síðu og þarf því enga undirvalmynd.

Brauðmylsnan er þriggja þrepa: `Forsíða / <Flokkur> / <Síða>`. Flokksþrepið
vísar á samsvarandi kafla á forsíðunni (`index.html#thema`, `#friends`,
`#vidauki`) — þar eru öll spjöld flokksins.

Merking núverandi síðu er tvöföld — aldrei litur einn og sér (regla 3.3):

| Staða | Merking |
|---|---|
| Nákvæmlega þessi síða | `aria-current="page"` + fylltur flötur + feitt letur |
| Önnur síða í sama flokki | `aria-current="true"` + kantur undir |

### Smellaleiðin — mælt, ekki áætlað

`tests/test_vefur.py` gengur tenglagrafið frá forsíðunni og fellur ef eitthvað
fer yfir þrjá smelli. Mæld dýpt:

```
Forsíða                                    0 smellir
├── Þema
│   └── Skjálftavaktin                     1
├── Friends
│   ├── Friends-gagnasagan                 1
│   ├── Plass, nærvera og tengsl Phoebe    1
│   ├── Söngur Phoebe í Central Perk       1
│   ├── Hlutverkið í gagnagrunni TMDB      1
│   ├── Okkar uppáhalds myndbönd           1
│   └── Til heiðurs Phoebe                 1
└── Viðauki
    ├── Brautskráning af háskólastigi      1
    ├── Veðurstöðvar                       1
    ├── Reglulegar segðir                  1
    └── Aðferðafræði                       1

Mesta dýpt: 1 smellur (þak reglunnar: 3)
```

Allar síðurnar eru í einum smelli af því að kortarastið á forsíðunni og
fóturinn vísa beint á þær allar. Fóturinn hefur einn dálk per flokk og er eins
á öllum síðum, svo engin síða er meira en einn smellur frá hverri annarri.

### Þrjár spurningar efst á hverri síðu (regla 3.2)

| Spurning | Hvar henni er svarað |
|---|---|
| Hvar er ég? | Brauðmylsna, flokksmerki (`Viðauki A · Vefþjónustur`) og merkt valmynd |
| Hvað er hér? | `<h1>` og inngangsmálsgreinin, auk staðreyndadálksins „Um þessa síðu" |
| Hvert get ég farið næst? | Undirvalmynd (Friends, Viðauki), valmyndin sjálf og „Hvert get ég farið næst?" neðst — næsta síða í flokknum, fyrsta síða annars flokks og aðferðafræðin |

Staðreyndadálkurinn segir líka hreint út hver **staða síðunnar** er. Meðan
efnið vantar stendur þar „Beinagrind — greining í vinnslu", og efnishlutinn
sjálfur ber `bidstada`-einingu sem lofar engum tölum (regla 8).

---

## 3. Sjónræna kerfið

Öll gildi eru í `web/assets/css/tokens.css`. Prófin staðfesta að **engin
px-tala og enginn harðkóðaður litur** sé í neinni annarri CSS-skrá.

- **Litir:** einn aðallitur (blágrænt), einn áherslulitur (brennt appelsínugult),
  sjö þrepa grátónaskali og þrír merkingarlitir.
- **Letur:** tvær fjölskyldur — Georgia-stafli á fyrirsagnir, kerfisstafli á
  lesmál (auk einbreiðs stafla fyrir kóðabrot). Sjö föst stærðarþrep.
- **Bil:** 4px grunneining; öll bil eru margfeldi af henni (`--bil-1` … `--bil-24`).
- **Dökkt þema:** `prefers-color-scheme: dark` endurskilgreinir **eingöngu**
  tokens — engir nýir stílar. Prófin falla ef eitthvað annað en breyta er
  skilgreint þar.

### Tvær skráðar undantekningar

1. **Skjáþrep.** Media queries taka ekki við CSS-breytum. Þrepin þrjú (40rem,
   48rem, 64rem) eru því skráð sem athugasemd efst í `tokens.css` og notuð
   óbreytt annars staðar. Þau eru í `rem`, ekki `px`.
2. **44px smellifletir.** Regla 3.5 er uppfyllt fyrir öll **stjórntæki**:
   valmyndartengla, hnappa, brauðmylsnu, merkið í hausnum, fótartengla,
   undirvalmynd, kortatengla og „næstu skref". Hún gildir **ekki** um tengla
   inni í lesmáli — að teygja þá í 44px myndi rjúfa línubilið í textanum. Þetta
   er sama skil og WCAG dregur milli stjórntækja og texta í samfelldu máli.

### Birtuskil

Upprunalegu níu síðurnar voru mældar í báðum þemum: hvert einasta textaelement stenst
WCAG 2.1 AA (4.5:1, eða 3:1 fyrir stórt letur). Tvö gildi þurfti að laga í
dökka þemanu og bæði voru leyst í tokens — aðvörunarliturinn var of dökkur, og
merkt valmyndarsíða notaði bakgrunnslit sem texta. Fjórar síður bættust við
í flokkuninni 2026-09-28. Þær nota sömu einingar og tokens en hafa ekki
verið mældar sérstaklega.

---

## 4. Einingar

Ein eining = ein CSS-skrá í `web/assets/css/components/`.

| Eining | Skrá | Hlutverk |
|---|---|---|
| Brauðmylsna | `braudmylsna.css` | Slóð notanda, á öllum undirsíðum |
| Síðuhaus | `sidu-haus.css` | Flokkur, `<h1>`, inngangur og staðreyndadálkur |
| Undirvalmynd | `undirvalmynd.css` | Systursíður (Phoebe-síðurnar þrjár) |
| Biðstaða | `bidstada.css` | Heiðarlegur staðgengill fyrir efni sem vantar |
| Næstu skref | `naesta-skref.css` | Þrír tenglar neðst — engin síða er blindgata |
| Kort | `kort.css` | Efnisspjöld í rasti (forsíða) |
| Hetja | `hetja.css` | Kynningarsvæði forsíðu og hnappastílar |
| Staða gagna | `stada-gagna.css` | Uppfærsludagsetning úr `web/gogn/` |

Aðeins ein JavaScript-skrá er í notkun: `valmynd.js` (og `stada-gagna.js` á
forsíðunni). Báðar eru með `defer`.

---

## 5. Án JavaScript

Þetta er hörð krafa (regla 3.4), ekki markmið. Staðfest með því að afrita
`web/` og fjarlægja allar `<script>`-merkingar:

- Valmyndarhnappurinn **birtist ekki** — CSS felur hann sjálfgefið og
  `valmynd.js` kveikir á honum með `data-js="virkt"`.
- `aria-expanded` er **ekki** í HTML-inu; skriftan setur það. Án hennar er
  ekkert loforð gefið skjálesurum um hegðun sem er ekki til.
- Valmyndin stendur opin í eðlilegu flæði og vefst í línur undir merkinu.
- Hausinn er `position: relative` undir 64rem og `sticky` fyrir ofan. Ástæðan:
  án JavaScript er valmyndin öll sýnileg, og fastur haus tæki þá þriðjung af
  símaskjá.
- Ekkert efni hverfur og engin slóð brotnar.

---

## 6. Hvað P3.4–P3.11 gera

Hver síðuverkpakki fyllir **einn** `<article class="efni">` og skiptir
`bidstada`-einingunni út fyrir raunverulegt efni. Það sem á ekki að snerta:

- Hausinn og fótinn — þeir eru stafrétt eins á öllum síðunum og prófin
  falla ef það breytist. Þurfi valmyndin að breytast er það gert á öllum
  síðunum í einu.
- `tokens.css` — nema til að bæta við þrepi í skala sem er þegar til.
- Nýjar px-tölur eða litir í component-skrár: prófin stöðva það.

Það sem á að uppfæra: reiturinn **Staða síðunnar** í staðreyndadálknum, þegar
efnið er komið.

---

## 7. Staðfesting

```bash
python3 -m unittest discover -s tests      # vefprófin eru í tests/test_vefur.py
python3 -m http.server 8000 --directory web
```

`tests/test_vefur.py` staðfestir aðskilnað HTML/CSS/JS, `defer` á öllum
skriftum, `lang="is"`, eina `<h1>` á síðu, fyrirsagnir án stökka, merkingarbær
kennileiti, brauðmylsnu, stafréttan haus og fót, að allar slóðir séu til, að
engin síða sé munaðarlaus, þriggja smella þakið, og að engin px-tala eða litur
sé utan `tokens.css`.

Mæld þyngd fyrstu hleðslu: **29–32 KB** á síðu (þak reglu 3.4: 500 KB).
