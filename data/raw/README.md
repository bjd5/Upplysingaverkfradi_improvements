# Hrágögn — frosin svör frá vefþjónustum

Þessi mappa er **byrjunin á gagnaflæðinu** (CLAUDE.md, kafli 0). Hér liggja svör
vefþjónustanna eins og þau komu, og öll tala sem endar á vefsíðunni á sér leið
aftur hingað.

Þrjár reglur gilda um allt sem er hér:

1. **Ekkert er handbreytt** — hvorki gögnin né `provenance.json` (reglur 4 og 10).
2. **Ekkert er sótt tvisvar að óþörfu.** Athugaðu þessa möppu áður en þú sækir
   (regla 4). Skriftan `frysta.py` gerir það sjálf og sækir ekki yfir eintak
   sem er þegar til.
3. **Hvert safn ber provenance**: þjónusta, slóð, aðferð, allar breytur,
   söfnunartími, User-Agent, SHA-256 og svarstærð.

Grunnurinn í `data/db/` er **afleiða** af þessari möppu og er ekki í git. Það á
að vera hægt að endurbyggja hann héðan án nets — það er prófið á reglu 5.

---

## 1. Söfnin

| Safn | Skrár | Stærð | Þjónusta | Aðferð |
|---|---:|---:|---|---|
| [`vedur-quakes/`](vedur-quakes/) | 2 | 94,7 kB | `api.vedur.is/quakes/events` | afrit úr upprunaverkefninu |
| [`hagstofan/`](hagstofan/) | 4 | 4,6 kB | `px.hagstofa.is` (`SKO04208b.px`) | afrit úr upprunaverkefninu |
| [`vedurstodvar/`](vedurstodvar/) | 2 | 153,6 kB | `api.vedur.is/weather/stations` | **ný söfnun** 2026-09-24 |
| [`mbl/`](mbl/) | 2 | 367,7 kB | `www.mbl.is/frettir/` | afrit — eina eintakið sem til er |
| **Samtals** | **10** | **620,6 kB** | | |

### Hvaða skrifta les hvert safn

| Safn | Hleðsla í grunninn | Birtist á síðu |
|---|---|---|
| `vedur-quakes/` | `src/python/vinnsla/` — P1.2, issue #6 | `web/sidur/skjalftavaktin.html` |
| `hagstofan/` | `src/python/vinnsla/` — P1.3, issue #7 | `web/sidur/hagstofan.html` |
| `vedurstodvar/` | `src/python/vinnsla/` — P1.4, issue #8 | `web/sidur/vedurstodvar.html` |
| `mbl/` | `src/python/vinnsla/` — P1.5, issue #9 | `web/sidur/mbl-regex.html` |

Safnið `vedurstodvar/` er auk þess lesið af
[`src/python/vinnsla/vedurstodvar_samanburdur.py`](../../src/python/vinnsla/vedurstodvar_samanburdur.py),
sem ber það við frosna viðmiðið.

---

## 2. Af hverju söfnin komu þrjár ólíkar leiðir

**`vedur-quakes/` og `hagstofan/`** voru vistuð með provenance í
upprunaverkefninu og komust í git þar. Þau voru afrituð hingað óbreytt
(`shutil.copy2`, breytingartímar varðveittir) og hver skrá sannreynd gegn þeirri
SHA-256 sem upprunaverkefnið skráði þegar það sótti gögnin. Að summurnar stemmi
sannar tvennt í einu: afritið er ósnert **og** frumgagnið hafði ekki breyst
síðan það var sótt.

**`vedurstodvar/`** átti sér ekkert eintak. Gamla verkefnið sótti stöðvalistann
upp á nýtt í hverri byggingu og vistaði svarið aldrei, svo gamla
veðurstöðvasíðan gat sýnt aðrar tölur í dag en í gær. Hér var **eitt** eintak
sótt og fryst. Það er **ný söfnun**, ekki afrit, og tölur sem víkja frá gömlu
síðunni eru breyting á stöðvaskránni en ekki villa — samanburðurinn er í
[`docs/vedurstodvar-samanburdur.md`](../../docs/vedurstodvar-samanburdur.md).

Ein beiðni var send, ósíuð. Gamla skriftan sendi fimm — ósíaða og fjórar síaðar
— en síurnar (`active`, `polygon`, `station_id`) velja allar úr sama mengi, svo
ósíaða svarið er yfirmengi þeirra allra og hinar fjórar eru reiknaðar
staðbundið. Fjórar beiðnir sem engu bæta við eru álag á þjónustu sem gefur
gögnin frítt.

**`mbl/`** var fryst í P0.1 (issue #30) og er eina eintakið sem til er af
fréttaforsíðunni sem regex-æfingin byggir á. Provenance þess liggur með öðrum
björgunargögnum í [`docs/vidmid/provenance.json`](../../docs/vidmid/provenance.json)
og er staðfest með `python3 src/python/vidmid/provenance.py stadfesta`.

---

## 3. Það sem er EKKI fryst

| Safn | Hvað vantar | Staða |
|---|---|---|
| TMDB (`api.themoviedb.org`) | `TMDB_TOKEN` í `.env` | **ófryst** |

Ekkert eintak af TMDB-svörunum er á disknum; skyndiminnið í
`data/processed/tmdb/` var `gitignore`-að í upprunaverkefninu og er horfið. Það
sem eftir er af safninu er samantektin í
`docs/vidmid/generated/phoebe-tmdb-summary.md`, sem P0.1 bjargaði.

Lykillinn er ekki til í umhverfinu, svo ekkert var hægt að sækja. Þetta er skráð
í `ofryst` í [`frysting.json`](frysting.json) og stöðvar ekki önnur verk — en
síðan `web/sidur/phoebe-tmdb.html` (P3.10) getur ekki byggt á frosnu gagni fyrr
en safnið er fryst. Sjálf söfnunin á heima í sameiginlega HTTP-laginu (P2.1,
issue #12), þar sem lyklameðferð og hraðatakmörkun eru leyst á einum stað.

---

## 4. Að frysta og staðfesta

```bash
python3 src/python/sofnun/frysta.py allt         # afrit + veðurstöðvar + TMDB-skráning
python3 src/python/sofnun/frysta.py stadfesta    # reiknar SHA-256 upp á nýtt
```

`stadfesta` gerir athugasemd við breytta skrá, horfna skrá **og** skrá sem hefur
bæst við án þess að vera skráð, og skilar öðru en núlli ef nokkuð stemmir ekki.
Þá eru hrágögnin ekki lengur ósnert og niðurstöður sem byggja á þeim eru
ómarktækar.

[`frysting.json`](frysting.json) geymir fyrir hverja skrá: stærð, SHA-256, hvort
hún var sannreynd gegn provenance upprunaverkefnisins, og hvenær safnið var
fryst. Hún er **afleidd** og ekki handbreytt.

| Skrá | Svarar spurningunni |
|---|---|
| `<safn>/provenance.json` | Hvaðan komu gögnin og með hvaða breytum? |
| `frysting.json` | Hvenær komust þau hingað og eru þau enn ósnert? |

---

## 5. Leyfi

| Safn | Leyfi |
|---|---|
| `vedur-quakes/` | CC BY 4.0 — `https://creativecommons.org/licenses/by/4.0/` |
| `vedurstodvar/` | CC BY 4.0 — skráð í `info.license` í `api.vedur.is/weather/openapi.json` |
| `hagstofan/` | sjá skilmála Hagstofu Íslands; óskráð í provenance upprunaverkefnisins |
| `mbl/` | ekkert leyfi gefið — eintakið er notað til máltæknilegrar æfingar |

Fullar heimildafærslur fara í `docs/heimildir.md` (P0.4, issue #4). Vísa verður
til Veðurstofunnar hvar sem þessi gögn birtast; CC BY 4.0 krefst þess.
