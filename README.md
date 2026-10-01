# Upplýsingaverkfræði — rannsóknarverkefni

Gögn sótt frá vefþjónustum, geymd í SQL-gagnagrunni og birt á static vefsíðu á
íslensku. Endurbygging á eldra Quarto-verkefni ([`docs/endurbygging.md`](docs/endurbygging.md)).

**Síðan:** <https://bjd5.github.io/Upplysingaverkfradi_improvements/> — birtist
þegar GitHub Pages hefur verið virkjað og workflow-ið `.github/workflows/pages.yml`
(#28) hefur keyrt.

**Reglurnar eru í [CLAUDE.md](CLAUDE.md).** Lestu þær áður en þú bætir við skrá.

## Spurningarnar

| Síða | Spurning |
|---|---|
| Skjálftavaktin (þema) | Eru bein tengsl milli kvikusöfnunar og jarðskjálftavirkni? *Í mótun:* gögnin lýsa aðeins skjálftunum á Reykjanesskaga, nóvember–desember 2023. |
| Phoebe — tölfræði | Hversu mikið pláss fær Phoebe Buffay í Friends — línur, senur og samtöl — miðað við hinar aðalpersónurnar fimm? |
| Phoebe — Central Perk | Hvenær syngur Phoebe í Central Perk og hvernig dreifast atriðin yfir þáttaraðirnar tíu? |
| Phoebe — TMDB | Hvernig er hlutverkið skráð í TMDB? *Bíður gagna (#75).* |
| Viðauki A — Hagstofan | Hve stór hluti innritunarárgangs 2017 í háskóla hafði lokið námi sex árum síðar, eftir námssviði og kyni? |
| Viðauki B — Veðurstöðvar | Hvaða veðurstöð á forrit fyrir VR-II (Hjarðarhaga 6) að lesa, og dugar hún? |
| Viðauki C — mbl.is | Hvað má lesa úr kyrrstæðu HTML-svari fréttasíðu með reglulegum segðum einum? |

Greiningin er lýsandi; engin tala mælir orsakasamband. Afmörkunin er í
[`docs/adferdafraedi.md`](docs/adferdafraedi.md), takmarkanirnar í
[`docs/takmarkanir.md`](docs/takmarkanir.md).

## Gagnasöfnin

| # | Safn | Heimild | Sótt (UTC) | Leyfi |
|---|---|---|---|---|
| 1 | Jarðskjálftar | Veðurstofa Íslands — `api.vedur.is/quakes/events` | 2026-09-10 | CC BY 4.0 |
| 2 | Brautskráning | Hagstofa Íslands — PxWeb, tafla `SKO04208b` | 2026-09-10 | óstaðfest |
| 3 | Veðurstöðvar | Veðurstofa Íslands — `api.vedur.is/weather/stations` | 2026-09-24 | CC BY 4.0 |
| 4 | Fréttasíða | mbl.is — `www.mbl.is/frettir/` (vefsíða, ekki API) | 2026-09-16 | ekkert gefið; skilmálar óstaðfestir |
| 5 | Friends-handrit | `delvinso/friends-tv-show-analysis` @ `a4641fe`, afleiða af `fangj/friends` | commit 2019-02-21 | kóðinn MIT, handritin án leyfis — hér eru aðeins afleiddar tölur |
| 6 | TMDB | The Movie Database API v3 | **ekki fryst** — `TMDB_TOKEN` vantar (#75) | óstaðfest |

Söfn 1–4 eru fryst óbreytt í `data/raw/`, Friends-tölurnar í `data/processed/`.
Slóðir, SHA-256 og opnar spurningar: [`docs/heimildir.md`](docs/heimildir.md).

## Keyrsla frá tómri vél

Þarf git, bash og **Python 3.12+** — enga pakka. Python 3.11 dugar ekki: grunnurinn
neitar að opnast og prófin falla með villum sem líta út eins og kóðavillur. Sé
`python3` eldri en 3.12 er `python3.12` notað beint og `PYTHON=python3.12` sett
fyrir skriftur og próf.

```bash
git clone https://github.com/bjd5/Upplysingaverkfradi_improvements.git
cd Upplysingaverkfradi_improvements

cp config/.env.example .env                    # stillingar, aldrei í git
python3.12 src/python/main.py --skref allt     # eða: safna | vinna | hlada | flytja-ut
```

- **`safna`** sendir ekkert netkall: öll söfn liggja þegar í `data/raw/`. TMDB er
  skráð óvirkt nema `TMDB_TOKEN` sé í umhverfinu eða `.env`.
- **`hlada`** byggir `data/db/rannsokn.sqlite` eingöngu úr `src/sql/migrations/`.
  Migration er aldrei breytt eftir keyrslu; keyrarinn stöðvast ef SHA-256 hennar
  breytist.
- **`flytja-ut`** skrifar `web/gogn/*.json`. Á hreinni klónun verða skrárnar
  bætaeins og `git status` sýnir enga breytingu.

Fleiri skipanir:

```bash
PYTHON=python3.12 scripts/endurbyggja-grunn.sh        # eyðir grunninum, byggir aftur, prentar fingrafar
PYTHON=python3.12 scripts/saekja-gogn.sh listi        # söfnin; `<safn> --thvinga` sækir nýtt eintak af netinu
python3.12 src/python/vidmid/provenance.py stadfesta  # frosnu gögnin óbreytt (SHA-256)
```

Tvær endurbyggingar í röð eiga að prenta sama fingrafar.

**Friends-handritin (valkvætt).** Þau eru git submodule og ekki sótt við
venjulegt `git clone`; þeirra þarf hvorki fyrir síðuna né prófin. Til að
endurreikna Friends-tölurnar:

```bash
git submodule update --init data/raw/friends-handrit
FRIENDS_HANDRIT_MAPPA=data/raw/friends-handrit/season python3.12 src/python/main.py --skref vinna
```

**Myndritin (valkvætt).** Aðeins til að teikna SVG-myndritin upp á nýtt þarf
matplotlib: `pip install -r config/requirements-myndrit.txt`
([`docs/myndrit.md`](docs/myndrit.md)).

## Síðan staðbundið

```bash
python3 -m http.server 8000 --directory web      # http://localhost:8000
```

Opnaðu síðuna gegnum vefþjón, ekki sem `file://`: tölurnar eru sóttar úr
`web/gogn/` með `fetch`.

## Prófin

```bash
PYTHON=python3.12 python3.12 -m unittest discover -s tests
```

Prófin keyra á staðalsafninu einu. Þau sem þurfa matplotlib eða Friends-handritin
(`FRIENDS_HANDRIT_MAPPA`) sleppa sér án þeirra.

## Uppbygging

| Mappa | Hlutverk |
|---|---|
| `web/` | Static vefsíðan — sjálfstætt birtanleg |
| `src/python/` | Söfnun, úrvinnsla, útflutningur, yfirferð á upprunanum |
| `src/sql/` | Migrations og fyrirspurnir |
| `data/` | Gögn (að mestu utan git) |
| `docs/` | Aðferðafræði, heimildir, viðmið |

```
Vefþjónusta → data/raw/ → hreinsun → SQL-grunnur → web/gogn/*.json → vefsíðan
```

Vefsíðan les aðeins tilbúnar JSON-skrár; hún talar aldrei við API eða gagnagrunn.

## Nýtt efni úr gamla verkefninu

Gamla verkefnið er enn í vinnslu. Sjálfvirk lota fer daglega yfir það sem hefur
bæst við, flokkar það og opnar PR með því sem á heima hér:

```bash
scripts/yfirfara-uppruna.sh
```

Verklagið er í [`docs/uppruni.md`](docs/uppruni.md).
