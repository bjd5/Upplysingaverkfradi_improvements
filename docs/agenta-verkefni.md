# Verkpakkar fyrir agenta

Endurbyggingin brotin í pakka sem **einn agent klárar í einni lotu**.
Hver pakki = eitt issue = ein grein = eitt PR. Samhengið er í
[`endurbygging.md`](endurbygging.md), reglurnar í [`../CLAUDE.md`](../CLAUDE.md).

Prompt loknu pakkanna (P0.1–P0.4, P1.1, P2.1, P3.1) eru í git-sögu þessa
skjals, síðast í commit `781fd7d`.

---

## 1. Notkun

1. Veldu pakka sem er **ekki blokkaður** (kafli 3).
2. Settu **hausinn** (kafli 2) fremst í promptið, svo prompt pakkans.
3. Einn agent = einn pakki. Nýr pakki fær nýja lotu.

`--persona-scribe` styður ekki íslensku: notið `--persona-scribe=en`. Hausinn
tryggir að efni sé samt á íslensku.

## 2. Hausinn — fremst í hverju prompti

```text
Þú vinnur í repo-inu bjd5/Upplysingaverkfradi_improvements.

Lestu ÁÐUR en þú býrð til skrá:
  - CLAUDE.md             (bindandi regluverk — regla 1 ræður staðsetningu)
  - docs/endurbygging.md  (hvaðan verkefnið kemur og hvað má ekki tapast)

Fastar reglur:
  - Vinnið AÐEINS að issue-inu hér að neðan. Annað sem þarf að laga fer sem
    athugasemd í issue-ið.
  - Vinnið á grein, aldrei á main. Greinarheiti: <svið>/<stutt-lýsing>.
  - Commit-skilaboð: `svið: hvað var gert` (regla 7).
  - Committaðu og ýttu upp eftir HVERT áfangaskref, ekki í lokin — lota getur
    stöðvast fyrirvaralaust og ókommituð vinna tapast (kafli 6).
  - Efni á ÍSLENSKU, kóðaheiti á ensku. Texti stuttur (regla 3.6).
  - Engir nýir pakkar, framework eða CDN án þess að spyrja (regla 10).
  - Aldrei handbreyta data/raw/ né web/gogn/ (regla 10).
  - Engin skrá yfir ~300 línur; villur aldrei þaggaðar (regla 6).
  - Ljúktu á gátlista reglu 9: hvað er staðfest og hvað ekki, og af hverju.
```

Þegar fleiri en einn agent vinnur samtímis, bætið við:

```text
  - Þú vinnur EINGÖNGU í möppunni sem þér var úthlutað. Ekki `git checkout`
    yfir á aðra grein og ekki `git add -A`.
  - Athugaðu `git status` áður en þú committar.
```

## 3. Pakkarnir

`✅` lokið · `🟢` laust · `⏸` blokkað · `👤` Björn, ekki agent.
Staðan er frá **27.9.2026**.

### Bylgja 0 — björgun og grunnur

| Pakki | Issue | Persóna | Staða |
|---|---|---|---|
| **P0.1** Bjarga gögnum af disknum | #30 | `--persona-devops` | ✅ |
| **P0.2** Lesa viðmiðstölur úr byggðu síðunni | #30 | `--persona-analyzer` | ✅ |
| **P0.3** Frysta hrágögn + `.gitignore` | #2 | `--persona-devops` | ✅ |
| **P0.4** Heimildir og aðferðafræði | #4 | `--persona-scribe=en` | ✅ |
| **P0.5** Höfundaréttarákvörðun | #3 | 👤 | ✅ valkostur A |
| **P0.6** Myndritaákvörðun | #17 | 👤 | ✅ matplotlib |

- **P0.5 → valkostur A:** handritin fara aldrei í repo-ið, aðeins afleiddu
  tölurnar.
- **P0.6 → matplotlib:** Python teiknar SVG við útflutning, litir úr
  `tokens.css`, gagnatafla í HTML-inu. Leyft **eingöngu** í
  `src/python/utflutningur/`; prófin keyra áfram á staðalsafninu og próf sem
  þarfnast matplotlib sleppa sér.
- TMDB náðist ekki að frysta — `TMDB_TOKEN` vantar (`data/raw/frysting.json`).

### Bylgja 1 — gagnalag

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P1.1** Migration-keyrari og tengilag | #5 | `--persona-backend` | ✅ | — |
| **P1.2** Skjálftavaktin: schema + hleðsla | #6 | `--persona-backend` | ✅ PR #40 | — |
| **P1.3** Hagstofan: schema + hleðsla | #7 | `--persona-backend` | ✅ PR #41 | — |
| **P1.4** Veðurstöðvar: schema + hleðsla | #8 | `--persona-backend` | ✅ PR #42 | — |
| **P1.5** mbl.is: schema + hleðsla | #9 | `--persona-backend` | ✅ PR #46 | — |
| **P1.6** Friends: schema + hleðsla | #10 | `--persona-backend` | 🟢 | — |
| **P1.7** Fyrirspurnir | #11 | `--persona-backend` | ⏸ | P1.6 |

Staðfestar tölur: 334 atburðir · 61 dagur (#6) · 36 gildi (#7) · 778 stöðvar,
343 með NULL lokaár (#8) · öll fimm svör æfingarinnar (#9). Hleðslan er ekki
tengd `hlada()` í `main.py` — það er **#39**, eitt verk til að forðast
samrunaárekstra.

### Bylgja 2 — Python-pípan

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P2.1** HTTP-lag | #12 | `--persona-backend` | ✅ | — |
| **P2.2** Söfnunarskriftur fluttar | #13 | `--persona-backend` | ✅ PR #43 | — |
| **P2.3** Kljúfa `earthquakes.py` (557 l.) | #14 | `--persona-refactorer` | 🟢 | — |
| **P2.4** Kljúfa `vedurstofa_stodvar.py` (637 l.) | #14 | `--persona-refactorer` | 🟢 | — |
| **P2.5** Kljúfa `phoebe_analysis.py` (1.199 l.) | #14 | `--persona-refactorer` | 🟢 | — |
| **P2.6** Kljúfa `phoebe_central_perk.py` (877 l.) | #14 | `--persona-refactorer` | 🟢 | — |
| **P2.7** Útflutningur í `web/gogn/` | #15 | `--persona-backend` | ⏸ | P1.7, P2.3–P2.6 |
| **P2.8** Próf og samanburður við viðmið | #16 | `--persona-qa` | ⏸ | P2.7 |

P2.3–P2.6 eru óháð innbyrðis. Viðmiðið fyrir P2.8 er **440 efnislegar tölur**
í `docs/vidmid/vidmid.json` (445 áður; fimm voru auðkenni, PR #45).

### Bylgja 3 — vefsíðan

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P3.1** Beinagrind og sjónrænt kerfi | #18 | `--persona-frontend` | ✅ PR #36 | — |
| **P3.2** JS-gagnahleðsla | #19 | `--persona-frontend` | ⏸ | P2.7 |
| **P3.3** Myndritalag | #17 | `--persona-frontend` | 🟢 | — |
| **P3.4** Síða: Skjálftavaktin | #20 | `--persona-frontend` | ⏸ | P3.2, P3.3 |
| **P3.5** Síða: Hagstofan | #21 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.6** Síða: Veðurstöðvar | #22 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.7** Síða: mbl.is regex | #23 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.8** Síða: Phoebe-tölfræði | #24 | `--persona-frontend` | ⏸ | P3.2, P3.3 |
| **P3.9** Síða: Central Perk | #24 | `--persona-frontend` | ⏸ | P3.2, P3.3 |
| **P3.10** Síða: TMDB | #24 | `--persona-frontend` | ⏸ | P3.2 |
| **P3.11** Síða: aðferðafræði | #25 | `--persona-scribe=en` | 🟢 | — |

### Bylgja 4 — gæði og útgáfa

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P4.1** Aðgengisúttekt | #26 | `--persona-frontend` | ⏸ | P3.4–P3.11 |
| **P4.2** Frammistöðuúttekt | #27 | `--persona-performance` | ⏸ | P3.4–P3.11 |
| **P4.3** Leyndarmálaúttekt | #28 | `--persona-security` | ⏸ | P3.4–P3.11 |
| **P4.4** Birting á Pages | #28 | `--persona-devops` | ⏸ | P4.1–P4.3 |
| **P4.5** README og verklok | #29 | `--persona-scribe=en` | ⏸ | P4.4 |

### Laust núna

Sjö pakkar snerta engar sömu skrár og má vinna samhliða: **P1.6, P2.3, P2.4,
P2.5, P2.6, P3.3, P3.11**. Auk þeirra eru laus: **#3** og **#17** (skjölun
ákvarðananna), **#39** (tengja `hlada()`), **#44** (prósentukóðun í
viðmiðsútdrætti) og **#47** (fingrafarið telur vegguklukkustimpla).

Prompt fyrir bylgjur 2–4 eru skrifuð þegar pakkinn losnar, á sama sniði og hér.

---

## 4. Prompt: P1.6 — schema og hleðsla

**Persóna:** `--persona-backend` · **Issue:** #10 · 🟢 **Laust**

Sama snið og P1.2–P1.5 notuðu.

```text
[HAUSINN úr kafla 2]

Verk: issue #10 — schema og hleðsla fyrir Friends-tölfræðina.

Migration-keyrarinn úr #5 er til; notaðu hann. Uppruni gagnanna, töflur,
dálkar og sannreyningar eru í issue-inu sjálfu. Viðmiðstölurnar eru í
docs/vidmid/phoebe-stats/_meta.json.

Smíðið:
- src/sql/migrations/006_friends.sql, með athugasemd um uppruna og leyfi
  (regla 5).
- Hleðslu í src/python/vinnsla/ sem SANNREYNIR hverja færslu. Frávik STÖÐVA
  keyrsluna (regla 6).
- Próf sem staðfesta: 227 skrár · 236 þættir · 61.161 lína · 2,95% óflokkað.

Handritin sjálf fara ALDREI í repo-ið, aðeins tölur um þau (P0.5).

Lokið: fjöldatölurnar úr grunninum bornar við viðmiðið, og engin fyrirspurn
notar strengjasamsetningu.
```

Migration-númer eru frátekin: 001–005 eru notuð, `006_friends.sql` er P1.6.
Keyrarinn stöðvast ef tvær migrations bera sama númer.

## 5. Prompt: P1.7 — endurnýtanlegar fyrirspurnir

**Persóna:** `--persona-backend` · **Issue:** #11 · ⏸ **Blokkað af P1.6**

```text
[HAUSINN úr kafla 2]

Verk: issue #11 — fyrirspurnirnar sem síðurnar byggja á fara í
src/sql/queries/, ein .sql-skrá á hverja, með athugasemd efst: hvaða spurningu
hún svarar og hvaða síða notar hana.

Að minnsta kosti:
  - Daglegur fjöldi jarðskjálfta MEÐ núlldögum (LEFT JOIN á earthquake_days).
  - Miðgildi og dreifing stærðar INNAN hvers kvarða (GROUP BY magnitude_type).
  - Hlaupandi 7 daga meðaltal:
    AVG(...) OVER (ORDER BY utc_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
  - Röðun persóna eftir plássi: RANK() OVER (PARTITION BY season)
  - interaction_lift sem CTE í læsilegum þrepum.

Python les skrárnar í stað þess að geyma SQL í strengjum. Skrárnar geyma
?-staðgengla, ALDREI innsett gildi (regla 5). Próf keyra hverja fyrirspurn.

Lokið: engin SQL-strengjasamsetning eftir í Python, og hver fyrirspurn ber
athugasemd um spurninguna sem hún svarar.
```

## 6. Verklag sem reynslan setti

**Committaðu og ýttu upp eftir hvert áfangaskref.** 24.9.2026 stöðvuðust
fjórir samhliða agentar á sömu mínútu þegar reikningsþakið náðist, og vinnan
lá ókommituð í vinnumöppum. Það sem er aðeins á einni vél er ekki til.

**Ein vinnumappa á hvern agent.** Tveir agentar í sömu möppu deila `HEAD` og
index, og sá seinni sópar verkum hins inn í sitt commit. Notið `git worktree`:

```sh
git worktree add ../uv-P2.3 -b vinnsla/kljufa-earthquakes main
git worktree remove ../uv-P2.3          # þegar PR er samþykkt
```

**Þegar lota fellur:** athugaðu `git status` í hverri vinnumöppu
(`git worktree list`) áður en nýr agent tekur við. Committaðu strandaða vinnu
með nafngreindum skrám og merktu sem björgun. Haltu agentinum frekar áfram en
að byrja nýja lotu.

**Staðfesting sem getur stemmt af tilviljun er ekki staðfesting.**
Yfirferð á strandaðri vinnu fann að fingrafar grunnsins taldi
vegguklukkustimpla með (#47): tvær hraðar keyrslur stemmdu af því þær lentu á
sömu sekúndu. Prófaðu skilyrðið þar sem það á að bresta.
