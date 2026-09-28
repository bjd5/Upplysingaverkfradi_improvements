# Viðmiðið — frosið afrit af gamla verkefninu

Þessi mappa er **sönnunargagn, ekki vinnugögn.** Hún svarar einni spurningu:

> **Sýnir nýja síðan sömu tölur og sú gamla?**

Breytist tala er það villa þar til annað er sannað ([`../endurbygging.md`](../endurbygging.md),
kafli 2). Ekkert hér er handbreytt: skrárnar eru afritaðar óbreyttar (`cp -p`)
og hver þeirra tryggð með SHA-256 í [`provenance.json`](provenance.json).

## 1. Hvað er hér

Söfnin voru aðeins til á einni vél — `gitignore`-uð í upprunaverkefninu — og
tvær vefþjónustanna skila öðru í dag en í september.

| Mappa | Skrár | Stærð | Hvað |
|---|---:|---:|---|
| [`vefur/`](vefur/) | 71 | 4,33 MB | Byggða gamla Quarto-síðan, 28 HTML-síður |
| [`generated/`](generated/) | 19 | 0,08 MB | Afleidd úttök sem Quarto límdi inn |
| [`phoebe-stats/`](phoebe-stats/) | 18 | 0,11 MB | Friends-tölfræðin fullreiknuð |
| `../../data/raw/mbl/` | 2 | 0,37 MB | mbl.is-eintakið — eina eintakið sem til er |
| **Samtals** | **110** | **4,89 MB** | |

- **`vefur/`** er eina heildarskráin yfir tölur gömlu síðunnar. `site_libs/`
  (Bootstrap, jQuery) fylgir óbreytt.
- **`generated/vedurstofa-*.md`** eru **eina ummerkið** um veðurstöðvagögnin;
  hráa svarið var aldrei vistað. Munur við nýja söfnun er vænt niðurstaða.
- **`phoebe-stats/_meta.json`** geymir tölurnar sem nýja greiningin verður að
  hitta: 227 handritsskrár, 236 þættir, 61.161 tilsvar, 2,95% óflokkað.
  Handritin sjálf eru **ekki** hér — aðeins tölur um þau (höfundaréttur, issue #3).
- **mbl-eintakið** liggur í `data/raw/` því það er hrágagn. Sótt af
  `https://www.mbl.is/frettir/` 2026-09-16.

## 2. Byggingin er úr þremur commitum, ekki einu

Verklýsing P0.1 sagði `2865ed6`. **Það stenst ekki:** engin skrá er yngri en
2026-09-17 09:51Z, en `2865ed6` er frá 2026-09-20. Quarto endurbyggir aðeins
breyttar síður, svo `vefur/` er samsett úr þremur byggingum:

| Commit | Tími | Á `main`? | Síður |
|---|---|---|---:|
| `5510cab` | 2026-09-16 14:55Z | ❌ Nei | 4 |
| `9cf667d` | 2026-09-16 23:06Z | ✅ Já | 2 |
| `fdf1261` | 2026-09-17 08:53Z | ✅ Já | 22 |

Fjórar síður eru úr grein sem **rataði aldrei á `main`**:
`friends/phoebe-statistics.html`, `lotur/regex/mbl.html`,
`lotur/vefthjonustur/hagstofan.html` og `friends/index.html`.

Þetta var staðfest með breytingartíma hverrar skráar borinn saman við `reflog`
upprunarepo-sins; allar 28 síðurnar falla innan lotu. Sundurliðunin er í
`vidmidsbygging` í [`provenance.json`](provenance.json). `origin/main` var þá í
`fb15d2a` — það er upphafsstaða [uppruna-yfirferðarinnar](../uppruni.md).

**Afleiðingar:** ósamræmi milli síðna úr ólíkum lotum er væntanlegt. **Fimm
slík atriði** eru skráð í [`vidmid.md`](vidmid.md), kafla 5 — tvö alvarleg.
`phoebe-top-talkers.json` er í tveimur röðum (sömu gildi) af því að jafntefli
er brotið án fasts viðmiðs.

## 3. Að staðfesta og lesa viðmiðið

```bash
python3 src/python/vidmid/provenance.py stadfesta   # SHA-256 hverrar skráar
python3 src/python/vidmid/tolur.py stadfesta        # tölurnar við síðurnar
python3 src/python/vidmid/tolur.py skrifa           # byggir vidmid.* upp á nýtt
```

`stadfesta` kvartar undan breyttri, horfinni **og** óskráðri skrá. Skili hún
öðru en núlli eru niðurstöður sem byggja á viðmiðinu ómarktækar.

| Skrá | Hvað |
|---|---|
| [`vidmid.json`](vidmid.json) | **1.391 tala** úr 28 síðum, þar af **445 efnislegar**, hver með síðu, lotu, kafla, einingu og samhengi |
| [`vidmid.md`](vidmid.md) | Sama fyrir manneskju: staðfestar tölur og ósamræmi |
| [`vidmid/`](vidmid/) | Ein skrá á hverja síðu nýju síðunnar |

Tala sem er ekki niðurstaða (auðkenni, dagsetning, CSS-gildi) er skráð með
`visst: false` og síuð frá í prófum.

**Tvær síður reikna tölurnar í vafranum**, svo HTML-ið geymir þær ekki. Þar er
gagnaskráin viðmiðið: `friends/phoebe-statistics.html` (skrárnar í
`vefur/friends/phoebe-stats/`) og `tokens/index.html` (CSV inni í `<script>`).

## 4. Reglur

1. **Ekkert hér er handbreytt eða endurbyggt** (regla 10). Viðmið sem er
   endurbyggt er ekki viðmið.
2. **Handritin koma aldrei hingað** — aðeins tölur um þau (issue #3).
3. Nýtt safn: afritaðu óbreytt, keyrðu `provenance.py skrifa` og skráðu það í
   töfluna í kafla 1.
4. `vidmid.json`, `vidmid.md` og `vidmid/` eru afleiður `tolur.py`.
