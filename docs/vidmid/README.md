# Viðmiðið — frosið afrit af gamla verkefninu

Þessi mappa er **sönnunargagn, ekki vinnugögn.** Hún svarar einni spurningu:

> **Sýnir nýja síðan sömu tölur og sú gamla?**

Breytist tala er það villa þar til annað er sannað ([`../endurbygging.md`](../endurbygging.md),
kafli 2). Ekkert hér er handbreytt: skrárnar voru afritaðar óbreyttar (`cp -p`)
og hver þeirra er tryggð með SHA-256 í [`provenance.json`](provenance.json).

## 1. Hvað er hér — og hvað er í git-taginu

Söfnin voru aðeins til á einni vél — `gitignore`-uð í upprunaverkefninu — og
tvær vefþjónustanna skila öðru í dag en í september.

| Staður | Skrár | Hvað |
|---|---:|---|
| [`vidmid.json`](vidmid.json) | 1 | **Viðmiðið sjálft:** 1.255 tölur úr 24 síðum gömlu síðunnar, þar af 417 efnislegar, hver með síðu, lotu, kafla, einingu og samhengi. Prófin bera sig saman við þetta. |
| [`vidmid.md`](vidmid.md) | 1 | Sama fyrir manneskju: staðfestar tölur og ósamræmi milli síðna. |
| [`generated/`](generated/) | 13 | Afleidd úttök sem Quarto límdi inn. **`vedurstofa-*.md` eru eina ummerkið um veðurstöðvagögnin**; hráa svarið var aldrei vistað. |
| `../../data/processed/phoebe-stats/` | 17 | Friends-tölfræðin fullreiknuð. `_meta.json` geymir tölurnar sem greiningin verður að hitta: 227 handritsskrár, 236 þættir, 61.161 tilsvar, 2,95% óflokkað. Vinnugagnið og viðmiðið eru sama eintakið. |
| `../../data/raw/mbl/` | 2 | mbl.is-eintakið, sótt af `https://www.mbl.is/frettir/` 2026-09-16. Liggur í `data/raw/` því það er hrágagn. |
| **Git-tagið `vidmid-frosid`** | 61 | Byggða gamla Quarto-síðan (`vefur/`, 60 skrár, 24 HTML-síður) og README Friends-greiningarinnar, ásamt hópaskránum `vidmid/*.md` og verkfærunum sem lásu tölurnar úr síðunni (`tolur.py` o.fl.). |

Handritin sjálf eru **hvergi** hér — aðeins tölur um þau (höfundaréttur, issue #3).

### Af hverju gamla síðan er í taginu en ekki í trénu

`vidmid.json` var lesið úr byggðu síðunni (P0.2). Eftir það les ekkert próf
síðuna sjálfa — hún var 60 skrár og 3,8 MB af HTML, Bootstrap og jQuery sem
enginn þurfti að rýna í. Hún var tekin úr trénu 28.9.2026 og er geymd óbreytt.
Tagið bendir á commit `f23035c` á `main` — síðasta commitið áður en síðan var
tekin út — svo efnið er líka í sögu `main` þótt tagið vanti í klón:

```bash
git tag vidmid-frosid f23035c                # ef tagið vantar
git worktree add /tmp/vidmid vidmid-frosid   # gamla síðan og verkfærin
git show vidmid-frosid:docs/vidmid/vefur/capstone/earthquakes.html
```

Skráalistinn og SHA-256 hverrar skráar standa áfram í `provenance.json` undir
`geymt_i_tagi`, svo tagið er jafn staðfestanlegt og tréð.

**Höfundaréttur:** byggðu síðurnar geyma orðréttar handritslínur úr þætti
`0101` (átta í `<pre>`-dæminu og ein hóplína). Þær eru ekki lengur á `main`, en
eru enn í git-sögunni og taginu. Ákvörðun (b) í issue #3, 28.9.2026: þær standa
sem stutt tilvitnun og sagan er ekki endurskrifuð. Handritsleitin ber þær við
frysta undanþágu í commit `f23035c` — sjá
[`../adferdafraedi.md`](../adferdafraedi.md), kafla 1.5.1–1.5.2.

## 2. Byggingin er úr þremur commitum, ekki einu

Verklýsing P0.1 sagði `2865ed6`. **Það stenst ekki:** engin skrá er yngri en
2026-09-17 09:51Z, en `2865ed6` er frá 2026-09-20. Quarto endurbyggir aðeins
breyttar síður, svo gamla síðan er samsett úr þremur byggingum:

| Commit | Tími | Á `main`? | Síður |
|---|---|---|---:|
| `5510cab` | 2026-09-16 14:55Z | ❌ **Nei** | 4 |
| `9cf667d` | 2026-09-16 23:06Z | ✅ Já | 2 |
| `fdf1261` | 2026-09-17 08:53Z | ✅ Já | 18 |

Fjórar síður eru úr grein sem **rataði aldrei á `main`**:
`friends/phoebe-statistics.html`, `lotur/regex/mbl.html`,
`lotur/vefthjonustur/hagstofan.html` og `friends/index.html`.

Þetta var staðfest með breytingartíma hverrar skráar borinn saman við `reflog`
upprunarepo-sins; allar 24 síðurnar falla innan lotu. Sundurliðunin er í
`vidmidsbygging` í [`provenance.json`](provenance.json). `origin/main` var þá í
`fb15d2a` — það er upphafsstaða [uppruna-yfirferðarinnar](../uppruni.md).

**Afleiðingar:** ósamræmi milli síðna úr ólíkum lotum er væntanlegt. **Fimm
slík atriði** eru skráð í [`vidmid.md`](vidmid.md), kafla 5 — tvö alvarleg.

## 3. Að staðfesta viðmiðið

```bash
python3 src/python/vidmid/provenance.py stadfesta
```

Skipunin reiknar SHA-256 af hverri frosinni skrá — hrágögnunum og viðmiðinu —
og kvartar undan breyttri, horfinni **og** óskráðri skrá. Skili hún öðru en
núlli eru niðurstöður sem byggja á viðmiðinu ómarktækar. `provenance.json` er
ekki endurskrifað: breytingartímarnir í henni komu með afrituninni.

Tala í `vidmid.json` sem er ekki niðurstaða (auðkenni, dagsetning, CSS-gildi)
er skráð með `visst: false` og síuð frá í prófum.

## 4. Reglur

1. **Ekkert hér er handbreytt eða endurbyggt** (regla 10). Viðmið sem er
   endurbyggt er ekki viðmið. **Eina undantekningin:** tokenmælaborð gamla
   verkefnisins var fjarlægt 2026-09-28 að ósk Björns, ásamt tenglum á það.
   Það var utan umfangs og geymdi engar rannsóknartölur.
2. **Handritin koma aldrei hingað** — aðeins tölur um þau (issue #3).
3. Sé safn tekið úr trénu færist færsla þess í `provenance.json` óbreytt undir
   `geymt_i_tagi`, og skrárnar eru geymdar í git-tagi.
