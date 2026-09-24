# Upplýsingaverkfræði — rannsóknarverkefni

Gögn sótt frá vefþjónustum, geymd í SQL-gagnagrunni og birt á static vefsíðu
á íslensku.

> **Reglur verkefnisins eru í [CLAUDE.md](CLAUDE.md).** Lestu þær áður en þú
> bætir við skrá. Þar er möppuskipanin, aðskilnaður HTML/CSS/JS, sjónræna
> kerfið, gagnareglur og gátlisti fyrir verklok.

## Uppbygging

| Mappa | Hlutverk |
|---|---|
| `web/` | Static vefsíðan — sjálfstætt birtanleg |
| `src/python/` | Gagnasöfnun, úrvinnsla, útflutningur |
| `src/sql/` | Schema, migrations, fyrirspurnir |
| `src/cpp/`, `src/java/` | Annar kóði, aðskilinn eftir máli |
| `data/` | Gögn (að mestu utan git) |
| `docs/` | Aðferðafræði og heimildir |

## Keyrsla

**Vefsíðan** — enginn byggingarferill, bara static skrár:

```bash
python3 -m http.server 8000 --directory web
# opnaðu http://localhost:8000
```

**Gagnaflæðið:**

```bash
cp config/.env.example .env      # fylltu út API-lykla
python3 src/python/main.py --skref allt
```

Skrefin má líka keyra hvert í sínu lagi:
`--skref safna | vinna | hlada | flytja-ut`

**Gagnagrunnurinn** er afleiða og verður eingöngu til úr `src/sql/migrations/`:

```bash
scripts/endurbyggja-grunn.sh     # eyðir grunninum og byggir hann frá grunni
```

Skriftan prentar fingrafar grunnsins á stdout. Tvær hreinar byggingar úr sömu
heimildum eiga að gefa sömu summu — geri þær það ekki er eitthvað í grunninum
sem hvergi á sér heimild.

Ný migration fær næsta lausa númer (`002_heiti.sql`) og er **aldrei breytt
eftir að hún hefur verið keyrð**: keyrarinn stöðvast ef SHA-256 hennar breytist.

**Prófin** keyra á staðalsafninu einu:

```bash
python3 -m unittest discover -s tests
```

## Gagnaflæði

```
Vefþjónusta → data/raw/ → hreinsun → SQL-grunnur → web/gogn/*.json → vefsíðan
```

Vefsíðan talar aldrei beint við API eða gagnagrunn. Hún les eingöngu tilbúnar
JSON-skrár úr `web/gogn/`.
