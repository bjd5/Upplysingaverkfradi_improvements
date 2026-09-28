# Viðmiðið — frosið afrit af gamla verkefninu

Þessi mappa er **sönnunargagn, ekki vinnugögn.** Hún svarar einni spurningu:

> **Sýnir nýja síðan sömu tölur og sú gamla?**

Krafan er að svarið sé já (sjá [`../endurbygging.md`](../endurbygging.md),
kafla 2). Breytist tala er það villa þar til annað er sannað.

Ekkert hér er handbreytt. Hver skrá er tryggð með SHA-256 í
[`provenance.json`](provenance.json).

---

## 1. Hvað er hér — og hvað er í git-taginu

| Staður | Skrár | Hvað þetta er |
|---|---:|---|
| [`vidmid.json`](vidmid.json) | 1 | **Viðmiðið sjálft:** 1.391 tala úr 28 síðum gömlu síðunnar, þar af 445 efnislegar niðurstöður. Prófin bera sig saman við þetta. |
| [`vidmid.md`](vidmid.md) | 1 | Sama efni fyrir manneskju: umfang, staðfestar tölur og ósamræmi milli síðna. |
| [`generated/`](generated/) | 13 | Afleidd úttök sem Quarto límdi inn í síðurnar. **`vedurstofa-*.md` eru eina ummerkið um veðurstöðvagögnin.** |
| `../../data/processed/phoebe-stats/` | 17 | Friends-tölfræðin fullreiknuð. `_meta.json` geymir viðmiðstölurnar: 227 handritsskrár, 236 þættir, 61.161 tilsvar, 2,95% óflokkað. Vinnugagnið og viðmiðið eru sama eintakið. |
| `../../data/raw/mbl/` | 2 | mbl.is-eintakið. Liggur í `data/raw/` því það er hrágagn, en er tryggt hér. |
| **Git-tagið `vidmid-frosid`** | 78 | Byggða gamla Quarto-síðan (`vefur/`, 71 skrá), tokenatöflur teymisins (6), README Friends-greiningarinnar, og verkfærin sem lásu tölurnar úr síðunni. |

### Af hverju gamla síðan er í taginu en ekki í trénu

`vidmid.json` var lesið úr byggðu síðunni í eitt skipti fyrir öll (P0.2).
Eftir það les ekkert próf síðuna sjálfa — hún var 71 skrá og 4,3 MB af HTML,
Bootstrap og jQuery sem enginn þurfti að rýna í. Hún var tekin úr trénu
28.9.2026 og er geymd óbreytt í taginu:

Tagið bendir á commit `8f48a31` á `main` — síðasta commitið áður en síðan var
tekin út — svo efnið er líka í sögu `main` þótt tagið vanti í klón:

```bash
git tag vidmid-frosid 8f48a31                # ef tagið vantar
git worktree add /tmp/vidmid vidmid-frosid   # gamla síðan og verkfærin
git show vidmid-frosid:docs/vidmid/vefur/capstone/earthquakes.html
```

Skráalistinn og SHA-256 hverrar skráar standa áfram í `provenance.json`
undir `geymt_i_tagi`, svo tagið er jafn staðfestanlegt og tréð.

**Höfundaréttur:** Byggðu síðurnar geyma átta orðréttar handritslínur úr
þætti `0101`. Þær eru ekki lengur á `main`, en eru enn í git-sögunni og
taginu. Hvort þær mega standa þar er opin spurning (b) í issue #3 — sjá
[`../adferdafraedi.md`](../adferdafraedi.md), kafla 1.5.1.

---

## 2. Úr hvaða commit er byggða síðan?

**Ekki einu heldur þremur.** Quarto endurbyggir aðeins þær síður sem hafa
breyst, svo gamla síðan er samsett úr þremur byggingum á tveimur dögum:

| Commit | Tími | Á sögu `main`? | Síður |
|---|---|---|---:|
| `5510cab` | 2026-09-16 14:55Z | ❌ **Nei** | 4 |
| `9cf667d` | 2026-09-16 23:06Z | ✅ Já | 2 |
| `fdf1261` | 2026-09-17 08:53Z | ✅ Já | 22 |

Fjórar síðurnar úr `5510cab` — þar á meðal `friends/phoebe-statistics.html`,
`lotur/regex/mbl.html` og `lotur/vefthjonustur/hagstofan.html` — eru byggðar á
grein sem **rataði aldrei á `main`**. Sönnunin er breytingartími hverrar skráar
(varðveittur með `cp -p`) borinn saman við `reflog` upprunarepo-sins. Full
sundurliðun er í `vidmidsbygging` í [`provenance.json`](provenance.json).

**Hvað þetta þýðir:** ósamræmi milli síðna er væntanlegt og er sjálfstæð
niðurstaða, ekki lestrarvilla. Fimm slík atriði eru skráð í
[`vidmid.md`](vidmid.md), kafla 5.

---

## 3. Að staðfesta að viðmiðið sé ósnert

```bash
python3 src/python/vidmid/provenance.py stadfesta
```

Skipunin reiknar SHA-256 af hverri skrá upp á nýtt og ber saman við
`provenance.json`. Hún gerir athugasemd við breytta skrá, horfna skrá **og**
skrá sem hefur bæst við óskráð. Skili hún öðru en núlli er viðmiðið ekki lengur
ósnert og niðurstöður sem á því byggja eru ómarktækar.

`provenance.json` er **ekki** endurskrifað. Breytingartímarnir í henni komu með
afrituninni og tapast við hvert `git clone`.

---

## 4. Reglur um þessa möppu

1. **Ekkert hér er handbreytt** (CLAUDE.md, regla 10).
2. **Ekkert hér er endurbyggt.** Viðmið sem er endurbyggt er ekki viðmið.
3. **Handritin sjálf koma aldrei hingað** — aðeins tölur um þau (issue #3).
4. Sé safn tekið úr trénu færist færsla þess í `provenance.json` óbreytt undir
   `geymt_i_tagi`, og skrárnar eru geymdar í git-tagi.
