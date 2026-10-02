# Upplýsingaverkfræði — rannsóknarverkefni

Gögn sótt frá vefþjónustum, geymd í SQL-gagnagrunni og birt á static vefsíðu á
íslensku. Endurbygging á eldra Quarto-verkefni ([`docs/endurbygging.md`](docs/endurbygging.md)).

**Reglurnar eru í [CLAUDE.md](CLAUDE.md).** Lestu þær áður en þú bætir við skrá.

## Uppbygging

| Mappa | Hlutverk |
|---|---|
| `web/` | Static vefsíðan — sjálfstætt birtanleg |
| `src/python/` | Söfnun, úrvinnsla, útflutningur, yfirferð á upprunanum |
| `src/sql/` | Schema, migrations, fyrirspurnir |
| `data/` | Gögn (að mestu utan git) |
| `docs/` | Aðferðafræði, heimildir, viðmið |

```
Vefþjónusta → data/raw/ → hreinsun → SQL-grunnur → web/gogn/*.json → vefsíðan
```

Vefsíðan les aðeins tilbúnar JSON-skrár; hún talar aldrei við API eða gagnagrunn.

## Keyrsla

```bash
python3 -m http.server 8000 --directory web      # vefsíðan: http://localhost:8000

cp config/.env.example .env                      # API-lyklar
python3 src/python/main.py --skref allt          # eða: safna | vinna | hlada | flytja-ut

scripts/endurbyggja-grunn.sh                     # byggir grunninn frá grunni
python3 -m unittest discover -s tests            # prófin (Python 3.12+)
python3 src/python/vidmid/provenance.py stadfesta # frosnu gögnin (SHA-256)
```

- **Grunnurinn** verður aðeins til úr `src/sql/migrations/`. Endurbyggingin
  prentar fingrafar; tvær hreinar byggingar eiga að gefa það sama.
- **Migration er aldrei breytt** eftir keyrslu — keyrarinn stöðvast ef SHA-256
  hennar breytist. Ný migration fær næsta númer.
- **Enginn pakki þarf** nema til að teikna myndritin upp á nýtt:
  `pip install -r config/requirements-myndrit.txt` (matplotlib, sjá
  `docs/myndrit.md`). Prófin sem teikna sleppa sér án hans.

## Birting

Síðan birtist á GitHub Pages: <https://bjd5.github.io/Upplysingaverkfradi_improvements/>.
Hver breyting á `web/` í `main` birtir hana aftur, án byggingarskrefa
(`.github/workflows/pages.yml`).

Á undan birtingu staðfestir `tests/test_vefur_birting.py` að gagnaskrár séu
heilar, að engin slóð byrji á `/` og að ekkert leyndarmál sé í `web/`. Falli
það birtist ekkert.

Einu sinni þarf eigandi repo-sins að velja *Settings → Pages → Source:
GitHub Actions*.

## Nýtt efni úr gamla verkefninu

Gamla verkefnið er enn í vinnslu. Sjálfvirk lota fer daglega yfir það sem hefur
bæst við, flokkar það og opnar PR með því sem á heima hér:

```bash
scripts/yfirfara-uppruna.sh
```

Verklagið er í [`docs/uppruni.md`](docs/uppruni.md).
