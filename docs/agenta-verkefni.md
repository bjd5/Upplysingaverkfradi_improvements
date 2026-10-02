# Verkpakkar fyrir agenta

Endurbyggingin brotin í pakka sem **einn agent klárar í einni lotu**.
Hver pakki = eitt issue = ein grein = eitt PR. Samhengið er í
[`endurbygging.md`](endurbygging.md), reglurnar í [`../CLAUDE.md`](../CLAUDE.md).

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
  - Efni á ÍSLENSKU, kóðaheiti samkvæmt reglu 1.2. Texti stuttur (regla 3.6).
  - Engir nýir pakkar, framework eða CDN án þess að spyrja (regla 10).
  - Aldrei handbreyta data/raw/ né web/gogn/ (regla 10).
  - Engin skrá yfir ~300 línur; villur aldrei þaggaðar (regla 6).
  - Ljúktu á gátlista reglu 9: hvað er staðfest og hvað ekki, og af hverju.
  - PR-lýsingin inniheldur `Closes #<N>`. Lokunarorð GitHub eru ENSK —
    „Lokar #N" lokar engu.
```

Þegar fleiri en einn agent vinnur samtímis, bætið við:

```text
  - Þú vinnur EINGÖNGU í möppunni sem þér var úthlutað. Ekki `git checkout`
    yfir á aðra grein og ekki `git add -A`.
  - Athugaðu `git status` áður en þú committar.
```

## 3. Pakkarnir

`✅` lokið · `🔄` í vinnslu · `🟢` laust · `⏸` blokkað · `👤` Björn, ekki agent.
Staðan er frá **1.10.2026**: `main` @ `5f32e31`, eftir samruna PR #73.

### Bylgja 0 — björgun og grunnur

| Pakki | Issue | Persóna | Staða |
|---|---|---|---|
| **P0.1** Bjarga gögnum af disknum | #30 | `--persona-devops` | ✅ |
| **P0.2** Lesa viðmiðstölur úr byggðu síðunni | #30 | `--persona-analyzer` | ✅ |
| **P0.3** Frysta hrágögn + `.gitignore` | #2 | `--persona-devops` | ✅ |
| **P0.4** Heimildir og aðferðafræði | #4 | `--persona-scribe=en` | ✅ |
| **P0.5** Höfundaréttarákvörðun | #3 | 👤 | ✅ valkostur A, PR #56 og #70 |
| **P0.6** Myndritaákvörðun | #17 | 👤 | ✅ matplotlib |

Ákvarðanirnar P0.5 og P0.6 með rökum: [`endurbygging.md`](endurbygging.md),
kafli 5. TMDB náðist ekki að frysta — `TMDB_TOKEN` vantar (#75).

### Bylgja 1 — gagnalag

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P1.1** Migration-keyrari og tengilag | #5 | `--persona-backend` | ✅ PR #35 | — |
| **P1.2** Skjálftavaktin: schema + hleðsla | #6 | `--persona-backend` | ✅ PR #40 | — |
| **P1.3** Hagstofan: schema + hleðsla | #7 | `--persona-backend` | ✅ PR #41 | — |
| **P1.4** Veðurstöðvar: schema + hleðsla | #8 | `--persona-backend` | ✅ PR #42 | — |
| **P1.5** mbl.is: schema + hleðsla | #9 | `--persona-backend` | ✅ PR #46 | — |
| **P1.6** Friends: schema + hleðsla | #10 | `--persona-backend` | ✅ PR #59 og #71 | — |
| **P1.7** Fyrirspurnir | #11 | `--persona-backend` | ✅ PR #62 | — |

Staðfestar tölur: 334 atburðir · 61 dagur (#6) · 36 gildi (#7) · 778 stöðvar,
343 með NULL lokaár (#8) · öll fimm svör æfingarinnar (#9). Allar hleðslur og
vinnslur eru tengdar `hlada()` og `vinna()` í `main.py` (#39, PR #60).

### Bylgja 2 — Python-pípan

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P2.1** HTTP-lag | #12 | `--persona-backend` | ✅ | — |
| **P2.2** Söfnunarskriftur fluttar | #13 | `--persona-backend` | ✅ PR #43 | — |
| **P2.3** Kljúfa `earthquakes.py` (557 l.) | #14 | `--persona-refactorer` | ✅ PR #50 | — |
| **P2.4** Kljúfa `vedurstofa_stodvar.py` (637 l.) | #14 | `--persona-refactorer` | ✅ PR #52 | — |
| **P2.5** Kljúfa `phoebe_analysis.py` (1.199 l.) | #14 | `--persona-refactorer` | ✅ PR #53 | — |
| **P2.6** Kljúfa `phoebe_central_perk.py` (877 l.) | #14 | `--persona-refactorer` | ✅ PR #58 | — |
| **P2.7** Útflutningur í `web/gogn/` | #15 | `--persona-backend` | 🔄 PR #68 og #69 sameinuð; PR #76 opið | — |
| **P2.8** Próf og samanburður við viðmið | #16 | `--persona-qa` | 🔄 í vinnslu | — |
| TMDB: frysting, grunnur, útflutningur | #75 | `--persona-backend` | ⏸ | `TMDB_TOKEN` 👤 |

PR-in fjögur undir #14 eru sameinuð; frágangur issue-sins er 🔄 í vinnslu.
Viðmiðið fyrir P2.8 er **417 efnislegar tölur** í `docs/vidmid/vidmid.json`.

### Bylgja 3 — vefsíðan

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P3.1** Beinagrind og sjónrænt kerfi | #18 | `--persona-frontend` | ✅ PR #36 | — |
| **P3.2** JS-gagnahleðsla | #19 | `--persona-frontend` | ✅ PR #72; PR #74 opið (lagar rautt `main`) | — |
| **P3.3** Myndritalag | #17 | `--persona-frontend` | ✅ PR #57 og #66 | — |
| **P3.4** Síða: Skjálftavaktin | #20 | `--persona-frontend` | 🔄 í vinnslu | — |
| **P3.5** Síða: Hagstofan | #21 | `--persona-frontend` | 🔄 PR #77 opið | — |
| **P3.6** Síða: Veðurstöðvar | #22 | `--persona-frontend` | 🔄 PR #78 opið | — |
| **P3.7** Síða: mbl.is regex | #23 | `--persona-frontend` | 🔄 PR #79 opið | — |
| **P3.8** Síða: Phoebe-tölfræði | #24 | `--persona-frontend` | 🔄 í vinnslu | — |
| **P3.9** Síða: Central Perk | #24 | `--persona-frontend` | 🔄 í vinnslu | PR #76 (gögnin) |
| **P3.10** Síða: TMDB | #24 | `--persona-frontend` | 🔄 í vinnslu | #75 (gögnin) |
| **P3.11** Síða: aðferðafræði | #25 | `--persona-scribe=en` | 🔄 í vinnslu | — |

### Bylgja 4 — gæði og útgáfa

| Pakki | Issue | Persóna | Staða | Blokkað af |
|---|---|---|---|---|
| **P4.1** Aðgengisúttekt | #26 | `--persona-frontend` | 🔄 í vinnslu | — |
| **P4.2** Frammistöðuúttekt | #27 | `--persona-performance` | 🔄 í vinnslu | — |
| **P4.3** Leyndarmálaúttekt | #28 | `--persona-security` | 🔄 í vinnslu | — |
| **P4.4** Birting á Pages | #28 | `--persona-devops` | 🔄 í vinnslu | — |
| **P4.5** README og verklok | #29 | `--persona-scribe=en` | 🔄 README og skjöl | gátlistinn og samanburðurinn: P4.4 og síðurnar |

---

## 4. Laust og blokkað

**Laust:** ekkert — allt sem ekki er blokkað er í vinnslu eða í opnu PR.

**Blokkað:** TMDB (#75) og þar með gögn P3.10 bíða `TMDB_TOKEN` frá Birni.
Gátlisti reglu 9 og samanburðartafla #29 bíða birtingar (#28) og síðnanna.

## 5. Prompt

Prompt hvers pakka er hausinn (kafli 2) og síðan verkið, skrifað þegar pakkinn
losnar. Prompt loknu pakkanna eru í git-sögu þessa skjals
(`git log -p -- docs/agenta-verkefni.md`).

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
