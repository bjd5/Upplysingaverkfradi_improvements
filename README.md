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

## Gagnaflæði

```
Vefþjónusta → data/raw/ → hreinsun → SQL-grunnur → web/gogn/*.json → vefsíðan
```

Vefsíðan talar aldrei beint við API eða gagnagrunn. Hún les eingöngu tilbúnar
JSON-skrár úr `web/gogn/`.
