# Endurbygging — frá Quarto-bók yfir í static vefsíðu með SQL-grunni

Leiðarvísir fyrir agenta: hvaðan verkefnið kemur, hvaða gögn mega ekki tapast
og í hvaða röð verkin eru unnin. [CLAUDE.md](../CLAUDE.md) segir *hvernig*;
þetta skjal segir *hvað*.

**Upprunarepo:** `Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe` (lokað) ·
**Þetta repo:** `bjd5/Upplysingaverkfradi_improvements` (**opið**) ·
**Greint:** 2026-09-24

---

## 1. Hvaðan við komum

Gamla verkefnið er Quarto-bók (`site/*.qmd` → GitHub Pages): 26 síður, 12
Python-skriftur og 11 prófunarskrár. Kóðinn er vandaður, en gengur ekki upp
gagnvart nýju reglunum:

| Krafa (CLAUDE.md) | Gamla verkefnið |
|---|---|
| Static HTML/CSS/JS í `web/` | Quarto með Bootstrap, jQuery og popper |
| SQL-grunnur í miðjunni | **Enginn gagnagrunnur** — CSV og Markdown-bútar |
| `src/python/{sofnun,vinnsla,…}` | 12 flatar skriftur í `src/` |
| JSON í `web/gogn/` | Markdown-bútar sem Quarto límir inn |
| Engin skrá yfir ~300 línur | `phoebe_analysis.py` 1.199, `phoebe_central_perk.py` 877, `vedurstofa_stodvar.py` 637, `earthquakes.py` 557 |
| Ekkert inline CSS/JS | Quarto býr til hvort tveggja |

Þetta er **ný framsetning ofan á sömu gögn**: greiningarkóðinn og prófin
flytjast yfir, birtingarlagið er skrifað upp á nýtt.

## 2. Gögnin — það sem má alls ekki tapast

**Tölurnar á nýju síðunni eiga að vera þær sömu og á þeirri gömlu.** Aðeins
hluti gagnanna var geymdur í gamla repo-inu:

| # | Gagnasafn | Uppruni | Í gamla repo-inu | Áhætta |
|---|---|---|---|---|
| 1 | Jarðskjálftar — 334 atburðir, Reykjanes 1.11.2023–1.1.2024 | `api.vedur.is/quakes/events` | `data/raw/vedur-quakes/` ✅ | Lítil |
| 2 | Hagstofan — brautskráning (json-stat2) | `px.hagstofa.is` `SKO04208b.px` | `data/raw/hagstofan/` ✅ | Lítil |
| 3 | Veðurstöðvar | `api.vedur.is/weather/stations` | **Hvergi** — sótt í hverri byggingu | **Há** |
| 4 | mbl.is fréttasíða | `mbl.is` | Aðeins á diski, `gitignore`-að | **Há** |
| 5 | TMDB — Phoebe/Friends | `api.themoviedb.org` (lykill) | `gitignore`-að | **Há** |
| 6 | Friends-handrit — 227 skrár, 236 þættir, 61.161 lína | Tvö submodule einstaklinga | Pinnuð SHA | Miðlungs + **höfundaréttur** |

Söfn 3–5 voru hvergi geymd. **Fyrsta verkið var því að frysta öll söfnin í
`data/raw/` með provenance og SHA-256** (fasi 0).

**Höfundaréttur:** þetta repo er opið. Handritin (`fangj/friends`, ekkert leyfi)
fara aldrei hingað; aðeins talnaniðurstöður um þau (ákvörðun P0.5).

## 3. Umfang nýju síðunnar

Ákveðið 2026-09-24: **rannsóknarefnið eingöngu.** Lotusíður námskeiðsins og
ígrundanir flytjast ekki. Tokenmælaborðið var fjarlægt alveg, líka úr frosna
viðmiðinu (2026-09-28).

**Breytt 2026-09-28:** efninu er skipt í **Þema**, **Friends** og **Viðauka**,
og þrjár Friends-biðsíður bætast við. Lotusíður án gagna flytjast áfram ekki.

| Flokkur | Slóð | Efni | Safn |
|---|---|---|---|
| — | `web/index.html` | Forsíða | — |
| Þema | `web/sidur/skjalftavaktin.html` | Jarðskjálftavirkni á Reykjanesi | 1 |
| Friends | `web/sidur/friends-gagnasagan.html` | Hvaðan handritin koma *(biðstaða)* | 6 |
| Friends | `web/sidur/phoebe-tolfraedi.html` | Plass, nærvera og tengsl Phoebe | 6 |
| Friends | `web/sidur/phoebe-central-perk.html` | Söngur Phoebe í Central Perk | 6 |
| Friends | `web/sidur/phoebe-tmdb.html` | Hlutverkið í TMDB *(biðstaða: lykil vantar)* | 5 |
| Friends | `web/sidur/uppahalds-video.html` | Uppáhaldsmyndbönd *(biðstaða)* | — |
| Friends | `web/sidur/phoebe-tribute.html` | Til heiðurs Phoebe *(biðstaða)* | — |
| Viðauki A | `web/sidur/hagstofan.html` | Brautskráning af háskólastigi | 2 |
| Viðauki B | `web/sidur/vedurstodvar.html` | Veðurstöðvar Veðurstofunnar | 3 |
| Viðauki C | `web/sidur/mbl-regex.html` | Reglulegar segðir á fréttasíðu | 4 |
| Viðauki D | `web/sidur/adferdafraedi.html` | Aðferð, heimildir, takmarkanir | — |

Myndbanda- og tribute-síðurnar mega aldrei hýsa myndbrot, myndir eða textabúta
úr þáttunum — repo-ið er opið (kafli 2).

Nýtt efni sem bætist við gamla verkefnið er flokkað daglega eftir þessu
umfangi ([`uppruni.md`](uppruni.md)).

## 4. Fasar

Hver fasi byggir á þeim á undan.

| Fasi | Efni | Staða |
|---|---|---|
| 0 | **Gagnabjörgun** — frysta gögnin, höfundaréttur, heimildir | lokið; TMDB ófryst (lykil vantar) |
| 1 | **Gagnalag (SQL)** — migration-keyrari, schema og hleðsla á hvert safn | lokið; sex söfn hlaðin |
| 2 | **Python-pípan** — söfnun, vinnsla, útflutningur, allt undir 300 línum | lokið; samanburður við viðmið í [`samanburdur.md`](samanburdur.md) |
| 3 | **Vefsíðan** — beinagrind og sjónrænt kerfi, svo ein síða í einu | lokið, nema þrjár biðsíður og TMDB |
| 4 | **Gæði og útgáfa** — [aðgengi](adgengi.md), [frammistaða](frammistada.md), birting, skjölun | lokið; birting bíður þess að Pages sé kveikt |

## 5. Reglur fyrir agenta

1. **Lestu [CLAUDE.md](../CLAUDE.md) fyrst.** Regla 1 ræður staðsetningu,
   regla 2 aðskilnaði HTML/CSS/JS.
2. **Ein issue = ein grein = eitt PR.** `main` er alltaf nothæf.
3. **Aldrei handbreyta `data/raw/` né `web/gogn/`** (reglur 4, 5.4, 10).
4. **Tölurnar standast samanburð við gamla verkefnið**; skráðu hann í PR-inu.
5. **Engir nýir pakkar, framework eða CDN án þess að spyrja** (regla 10).
6. **Ljúktu með gátlista reglu 9.**

## 6. Ákvarðanir

Stutt yfirlit; rökin eru í skjölunum sem vísað er í.

| Ákvörðun | Niðurstaða | Nánar |
|---|---|---|
| Höfundaréttur Friends-handritanna (#3) | **Valkostur A:** aðeins afleiddar tölur í repo-inu, handritin aldrei. Safnið er submodule sem er ekki sótt sjálfkrafa. | [`adferdafraedi.md`](adferdafraedi.md) 1.5.1 |
| Myndrit án framework (#17) | **Valkostur A:** matplotlib teiknar SVG við útflutning, eingöngu í `src/python/utflutningur/`; litir úr `tokens.css`. Notað fyrir Skjálftavaktina. | [`myndrit.md`](myndrit.md) kafli 1 |
| Myndrit Phoebe-síðnanna | Súlur teiknaðar af vanilla JS í stíl `--myndrit-*`, með gagnatöflu í HTML-inu sem virkar án JS. Frosnu SVG-myndirnar hafa hvítan bakgrunn og henta ekki í dökku þema. | [`vefur-gogn.md`](vefur-gogn.md) kafli 9 |
| Umfang síðunnar | Rannsóknarefnið eingöngu; lotusíður og tokenmælaborð fóru ekki yfir. | kafli 3 hér |
| mbl-eintakið | Nýtt eintak (16.9.2026); það gamla (7.9.2026) er glatað. | [`takmarkanir.md`](takmarkanir.md) |

## 7. Áhættuskrá

| Áhætta | Mótvægi |
|---|---|
| Söfn 3–5 hvergi geymd | Fasi 0 — frysting með SHA-256 |
| Handritin höfundarréttarvarin, repo-ið opið | Aðeins talnaniðurstöður í git (P0.5) |
| Submodule einstaklinga hverfa | Afleiddu tölurnar frystar |
| Myndrit án framework | matplotlib teiknar SVG við útflutning (P0.6) |
| TMDB-lykill lekur | `.env` utan git (regla 4) |
| Gamla verkefnið breytist áfram | Dagleg yfirferð ([`uppruni.md`](uppruni.md)) |
