# Upplýsingaverkfræði — rannsóknarverkefni

Gögn sótt frá vefþjónustum, geymd í SQL-gagnagrunni og birt á static vefsíðu á
íslensku. Endurbygging á eldra Quarto-verkefni ([`docs/endurbygging.md`](docs/endurbygging.md)).

**Síðan:** <https://bjd5.github.io/Upplysingaverkfradi_improvements/>
**Reglurnar eru í [CLAUDE.md](CLAUDE.md).** Lestu þær áður en þú bætir við skrá.

## Hvaða spurningum svarar það?

- Eru bein tengsl milli kvikusöfnunar og jarðskjálftavirkni? *(Skjálftavaktin)*
- Fær Phoebe sinn sjötta hluta af plássinu í Friends, og syngur hún meira en
  hún talar? *(Phoebe-síðurnar)*
- Hvað segja opin gögn Hagstofunnar og Veðurstofunnar, og hvað má lesa úr
  forsíðu mbl.is með reglulegum segðum? *(Viðaukar)*

## Gagnasöfnin sex

| Safn | Heimild | Leyfi |
|---|---|---|
| Jarðskjálftar | Veðurstofa Íslands, `api.vedur.is/quakes/events` | CC BY 4.0 |
| Brautskráning | Hagstofa Íslands, `px.hagstofa.is` (SKO04208b) | óstaðfest |
| Veðurstöðvar | Veðurstofa Íslands, `api.vedur.is/weather/stations` | CC BY 4.0 |
| mbl.is forsíða | `www.mbl.is/frettir/`, eintak frá 16.9.2026 | ekkert gefið |
| Friends-handrit | afrit aðdáenda; aðeins afleiddar tölur eru í repo-inu | ekkert leyfi |
| TMDB | `api.themoviedb.org` | **ekki sótt** — lykil vantar |

Slóðir, sóknartímar og fyrirvarar eru í [`docs/heimildir.md`](docs/heimildir.md);
takmarkanir gagnanna í [`docs/takmarkanir.md`](docs/takmarkanir.md).

## Uppbygging

| Mappa | Hlutverk |
|---|---|
| `web/` | Static vefsíðan — sjálfstætt birtanleg |
| `src/python/` | Söfnun, úrvinnsla, útflutningur, yfirferð á upprunanum |
| `src/sql/` | Schema, migrations, fyrirspurnir |
| `data/` | Gögn (að mestu utan git) |
| `docs/` | Aðferðafræði, heimildir, viðmið |
| `tests/` | Próf, staðalsafnið eitt |

```
Vefþjónusta → data/raw/ → hreinsun → SQL-grunnur → web/gogn/*.json → vefsíðan
```

Vefsíðan les aðeins tilbúnar JSON-skrár; hún talar aldrei við API eða gagnagrunn.

## Keyrsla frá tómri vél

Þarf **Python 3.12 eða nýrra** og git — enga pakka. Eldri Python stöðvast með
villu, því migrations keyra í heilli færslu.

```bash
git clone https://github.com/bjd5/Upplysingaverkfradi_improvements
cd Upplysingaverkfradi_improvements

scripts/endurbyggja-grunn.sh                 # grunnurinn úr migrations + frystum gögnum
python3 src/python/main.py --skref allt      # hleður, vinnur og flytur út í web/gogn/
python3 -m http.server 8000 --directory web  # vefsíðan: http://localhost:8000
python3 -m unittest discover -s tests        # prófin
```

Þetta virkar **án nets og án `.env`**: frystu hrágögnin eru í `data/raw/` og
Friends-tölurnar í `data/processed/`. Handritin sjálf eru hvergi í repo-inu, svo
undirmappan `data/raw/friends-handrit` er tóm og þarf ekki.

Skrefin eitt og eitt: `--skref safna | vinna | hlada | flytja-ut | allt`.
Ný gögn eru sótt með `scripts/saekja-gogn.sh` (sjá skriftuna); þá þarf
`cp config/.env.example .env`. TMDB þarf auk þess `TMDB_TOKEN`.

- **Grunnurinn** verður aðeins til úr `src/sql/migrations/`. Endurbyggingin
  prentar fingrafar; tvær hreinar byggingar eiga að gefa það sama.
- **Migration er aldrei breytt** eftir keyrslu — keyrarinn stöðvast ef SHA-256
  hennar breytist. Ný migration fær næsta númer.
- **`web/gogn/` er afleidd.** Skrárnar eru aldrei handbreyttar; þær verða til
  í `--skref flytja-ut`.
- **Frosnu gögnin** eru staðfest með `python3 src/python/vidmid/provenance.py stadfesta`.
- **Myndrit:** aðeins til að teikna þau upp á nýtt þarf
  `pip install -r config/requirements-myndrit.txt` (matplotlib, sjá
  [`docs/myndrit.md`](docs/myndrit.md)). Prófin sem teikna sleppa sér án hans.

## Birting

Hver breyting á `web/` í `main` birtir síðuna aftur á GitHub Pages, án
byggingarskrefa (`.github/workflows/pages.yml`). Á undan birtingu staðfestir
`tests/test_vefur_birting.py` að gagnaskrár séu heilar, að engin slóð byrji á
`/` og að ekkert leyndarmál sé í `web/`. Falli það birtist ekkert.

Einu sinni þarf eigandi repo-sins að velja *Settings → Pages → Source:
GitHub Actions*.

## Skjölun

| Skjal | Efni |
|---|---|
| [`docs/adferdafraedi.md`](docs/adferdafraedi.md) | Aðferðin, ákvarðanir og viðmiðstölur |
| [`docs/samanburdur.md`](docs/samanburdur.md) | Tölur nýju síðunnar borðnar við gömlu síðuna |
| [`docs/adgengi.md`](docs/adgengi.md) · [`docs/frammistada.md`](docs/frammistada.md) | Mælt aðgengi og stærð |
| [`docs/verklok.md`](docs/verklok.md) | Gátlisti reglu 9 fyrir verkefnið í heild, með frávikum |
| [`docs/vefur-gogn.md`](docs/vefur-gogn.md) · [`docs/myndrit.md`](docs/myndrit.md) | Gagnalag og myndritalag vefsins |

## Nýtt efni úr gamla verkefninu

Gamla verkefnið er enn í vinnslu. Sjálfvirk lota fer daglega yfir það sem hefur
bæst við, flokkar það og opnar PR með því sem á heima hér:

```bash
scripts/yfirfara-uppruna.sh
```

Verklagið er í [`docs/uppruni.md`](docs/uppruni.md).
