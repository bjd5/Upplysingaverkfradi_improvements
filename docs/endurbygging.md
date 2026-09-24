# Endurbygging — frá Quarto-bók yfir í static vefsíðu með SQL-grunni

Þetta skjal er **leiðarvísir fyrir agenta** sem vinna í þessu repo. Það lýsir
hvaðan verkefnið kemur, hvaða gögn mega ekki tapast, hvað er ógert og í hvaða
röð það er gert. Reglurnar sjálfar eru í [CLAUDE.md](../CLAUDE.md); þetta skjal
segir *hvað* á að gera, CLAUDE.md segir *hvernig*.

**Upprunarepo:** `Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe` (lokað)
**Þetta repo:** `bjd5/Upplysingaverkfradi_improvements` (**opið**)
**Dagsetning greiningar:** 2026-09-24

---

## 1. Hvaðan við komum

Gamla verkefnið er Quarto-bók (`site/*.qmd` → `docs/` → GitHub Pages) með 26
síðum, 211 commit og 12 Python-skriftum. Kóðinn sjálfur er vandaður: íslensk
docstring á hverri skriftu, eingöngu staðalsafnið í greiningunum, 11
prófunarskrár (2.366 línur) og CI sem stöðvast ef afleidd úttök verða ekki til.

Það sem gengur **ekki** upp gagnvart nýju reglunum:

| Krafa (CLAUDE.md) | Staðan í gamla verkefninu |
|---|---|
| Static HTML/CSS/JS í `web/` | Quarto-bók; Bootstrap, jQuery og popper fylgja með |
| SQL-grunnur í miðjunni | **Enginn gagnagrunnur til** — CSV og Markdown-bútar |
| `src/python/{sofnun,vinnsla,gagnagrunnur,utflutningur}` | 12 flatar skriftur í `src/` |
| `src/sql/{schema,migrations,queries}` | Ekkert |
| JSON í `web/gogn/` | Markdown-bútar í `site/_generated/` sem Quarto límir inn |
| Engin skrá yfir ~300 línur | `phoebe_analysis.py` 1.199, `phoebe_central_perk.py` 877, `vedurstofa_stodvar.py` 637, `earthquakes.py` 557, `phoebe-statistics.qmd` 1.000 |
| Ekkert inline CSS/JS | Quarto býr til hvort tveggja sjálfkrafa |

Þetta er ekki lagfæring á Quarto-síðu heldur **ný framsetning ofan á sömu
gögn**. Greiningarkóðinn og prófin flytjast yfir; birtingarlagið er skrifað upp
á nýtt.

---

## 2. Gögnin — það sem má alls ekki tapast

Þetta er mikilvægasta krafa verkefnisins: **tölurnar á nýju síðunni eiga að vera
þær sömu og á þeirri gömlu.** Það er ekki sjálfgefið, því aðeins hluti gagnanna
er í raun geymdur í gamla repo-inu.

| # | Gagnasafn | Uppruni | Staða í gamla repo-inu | Í git? | Áhætta |
|---|---|---|---|---|---|
| 1 | Jarðskjálftar — 334 atburðir, Reykjanes 1.11.2023–1.1.2024 | `api.vedur.is/quakes/events` | `data/raw/vedur-quakes/events.json` + provenance | ✅ | Lítil |
| 2 | Hagstofan — brautskráning af háskólastigi (json-stat2) | `px.hagstofa.is` `SKO04208b.px` | `data/raw/hagstofan/` (4 skrár + provenance) | ✅ | Lítil |
| 3 | Veðurstöðvar | `api.vedur.is/weather/stations` | **Hvergi vistað** — sótt í hverri CI-byggingu | ❌ | **Há** |
| 4 | mbl.is forsíða (regex-æfing) | `mbl.is` | `data/raw/mbl/*.html`, útilokað í `.gitignore` | ❌ | **Há** |
| 5 | TMDB — Phoebe/Friends | `api.themoviedb.org` (krefst lykils) | `data/processed/tmdb/`, útilokað | ❌ | **Há** |
| 6 | Friends-handrit — 227 HTML-skrár, 236 þættir, 61.161 lína | Tvö submodule frá einstaklingum | `data/fangj-friends`, `data/external/delvinso-friends` | Pinnuð SHA | Miðlungs + **höfundaréttur** |

**Þrjú gagnasöfn (3, 4, 5) eru sótt á ný í hverri byggingu og eru hvergi
geymd.** Veðurstofusíðan birtir því aðrar tölur í dag en í gær, og mbl.is-síðan
byggir á skrá sem er aðeins til á diski þess sem sótti hana. Um leið og gamla
repo-inu er lokað eða þjónustan breytist eru þau gögn farin.

**Þess vegna er fyrsta verkið — á undan öllu öðru — að frysta öll sex
gagnasöfnin í `data/raw/` með provenance og SHA-256** (issue í fasa 0). Ekkert
annað verk hefst fyrr en það er í höfn.

### Höfundaréttur — þetta repo er opið

Gamla repo-ið er lokað; þetta er **opið**. `fangj/friends` er safn afritaðra
handrita úr sjónvarpsþáttum og hefur **ekkert leyfi**. Handritin mega því ekki
fara óbreytt inn í þetta repo. Talnaniðurstöðurnar (línufjöldi á persónu,
senufjöldi, hlutföll) eru staðreyndir um textann en ekki textinn sjálfur og mega
fara inn. Sjá ákvörðunarissue í fasa 0.

---

## 3. Umfang nýju síðunnar

Ákveðið 2026-09-24: **rannsóknarefnið eingöngu.** Lotusíður námskeiðsins,
ígrundanir teymisins og tokenmælaborðið flytjast ekki yfir — þau eru áfram í
námskeiðsrepo-inu.

Síður nýju vefsíðunnar:

| Slóð | Efni | Gagnasafn |
|---|---|---|
| `web/index.html` | Forsíða: hvað verkefnið er, helstu niðurstöður | — |
| `web/sidur/skjalftavaktin.html` | Þemaverkefnið: jarðskjálftavirkni á Reykjanesi | 1 |
| `web/sidur/hagstofan.html` | Brautskráning af háskólastigi | 2 |
| `web/sidur/vedurstodvar.html` | Veðurstöðvar Veðurstofunnar | 3 |
| `web/sidur/mbl-regex.html` | Reglulegar segðir á fréttaforsíðu | 4 |
| `web/sidur/phoebe-tolfraedi.html` | Plass, nærvera og tengsl Phoebe | 6 |
| `web/sidur/phoebe-central-perk.html` | Söngur Phoebe í Central Perk | 6 |
| `web/sidur/phoebe-tmdb.html` | Hlutverkið í gagnagrunni TMDB | 5 |
| `web/sidur/adferdafraedi.html` | Aðferð, heimildir og takmarkanir | — |

---

## 4. Fasar og röð

Fasarnir eru raðir, ekki tillögur: hver fasi byggir á þeim á undan.

### Fasi 0 — Gagnabjörgun og grunnur
Frysta gögnin, leysa höfundaréttarspurninguna, skrá heimildir. **Ekkert annað
verk hefst fyrr en þessi fasi er búinn** — öll síðari verk vinna með gögnin sem
hér eru fryst.

### Fasi 1 — Gagnalag (SQL)
Migration-keyrari, svo eitt schema + hleðsla á hvert gagnasafn. Þessi fimm verk
eru **óháð innbyrðis** og má vinna samhliða þegar keyrarinn er til.

### Fasi 2 — Python-pípan
Söfnun, vinnsla, útflutningur — flutt úr gömlu skriftunum og klofið niður í
skrár undir 300 línum. Endar á prófunarverki sem staðfestir að tölurnar séu
óbreyttar.

### Fasi 3 — Vefsíðan
Beinagrind og sjónrænt kerfi fyrst, svo ein síða í einu. Síðuverkin eru óháð
innbyrðis.

### Fasi 4 — Gæði og útgáfa
Aðgengi, frammistaða, birting, skjölun.

---

## 5. Reglur fyrir agenta sem vinna í þessu repo

1. **Lestu [CLAUDE.md](../CLAUDE.md) áður en þú býrð til skrá.** Regla 1 ræður
   staðsetningu, regla 2 aðskilnaði HTML/CSS/JS.
2. **Ein issue = ein grein = eitt PR.** `main` á alltaf að vera nothæf.
3. **Aldrei breyta `data/raw/` né `web/gogn/` í höndunum.** Hvort tveggja er
   afleiða eða frumgagn sem skriftur eiga að skrifa (reglur 4, 5.4 og 10).
4. **Tölurnar eiga að standast samanburð við gamla verkefnið.** Breytist tala er
   það villa þar til annað er sannað — skráðu samanburðinn í PR-inu.
5. **Engir nýir pakkar, framework eða CDN-tenglar án þess að spyrja** (regla 10).
   Sjálfgefið er Python-staðalsafnið og hreint HTML/CSS/JS.
6. **Ljúktu með gátlista reglu 9** og segðu hvaða liði þú staðfestir og hverja
   ekki.

---

## 6. Áhættuskrá

| Áhætta | Afleiðing | Mótvægi |
|---|---|---|
| Gögn 3, 4 og 5 eru hvergi geymd | Tölur á síðunni óendurskapanlegar | Fasi 0 — frysting með SHA-256 |
| Friends-handritin eru höfundarréttarvarin og repo-ið opið | Endurbirting óleyfðs efnis | Ákvörðunarissue í fasa 0; aðeins talnaniðurstöður í git |
| Submodule-repo einstaklinga hverfa | Greiningin verður ekki endurkeyrð | Frysta afleiddu tölurnar, ekki treysta á submodule í byggingu |
| Myndrit án framework | Matplotlib-myndir gömlu síðunnar eiga sér ekki beina samsvörun | Ákvörðunarissue í fasa 3 áður en síðuverk hefjast |
| TMDB krefst lykils og repo-ið er opið | Lykill lekur | `.env` utan git, `config/.env.example` eitt í trénu (regla 4) |
| Endurbygging tekur lengri tíma en áætlað | Gamla síðan er eina birtingin | Gamla repo-ið stendur óhreyft; þetta er hliðstæð vinna |
