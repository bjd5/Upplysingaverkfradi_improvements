# data/processed/phoebe-stats

Unnin gögn um **Phoebe Buffay** úr Friends-handritunum.

Allar skrár hér eru **afleiddar** — þær eru búnar til af `src/phoebe_analysis.py`.
Ekki handbreyta þeim; keyrðu skriftuna aftur í staðinn:

```bash
python3 src/phoebe_analysis.py
```

Skriftan notar **eingöngu Python-staðalsafnið** (engin pandas/bs4), svo hún keyrir
án uppsetningar. Keyrslutími ≈ 6 sek.

> **Athugið:** `.gitignore` útilokar `data/processed/phoebe-stats/`, svo skrárnar hér
> eru **ekki** í Git — aðeins þetta README. GitHub Actions keyrir greininguna sjálf
> á undan `quarto render` (sjá `.github/workflows/pages.yml`), svo úttökin verða til
> upp á nýtt í hverri byggingu.

## Gagnagrunnur og aðferð

| Atriði | Gildi |
|---|---|
| Heimild | `data/external/delvinso-friends/season/*.html` (HTML-handrit) |
| Handritsskrár notaðar | 227 |
| Þættir sem það svarar til | 236 (9 skrár innihalda tvo þætti) |
| Undanskildar skrár | `0423uncut.html`, `07outtakes.html` (tvítekning/aukaefni) |
| Línur greindar | 61.161 |
| Óflokkaðar textablokkir | 2.078 (2,95% — nær eingöngu „Commercial Break“, „End“, kreditlínur) |

**Af hverju `delvinso` en ekki `fangj`:** söfnin tvö eru nánast eins, en í
`delvinso` er búið að laga brotna HTML-byggingu í þáttum `0911` og `0915`.
Greiningin var keyrð á báðum söfnum til samanburðar og gaf sömu tölur
(Monica munaði 1 línu), svo niðurstöðurnar eru ekki háðar valinu.

### Skilgreiningar sem gilda alls staðar

- **Lína (line)** = ein `Nafn: texti` blokk í handritinu.
- **Orð (word)** = `[a-z][a-z'-]*` eftir að **svigainnskot voru fjarlægð**, því
  `(hlær)` og `(til Joey)` eru sviðsleiðbeiningar en ekki töluð orð.
- **Sena (scene)** = talin upp á nýtt í hvert sinn sem lína byrjar á `[Scene: …]`.
- **Hóplínur eru undanskildar.** `All:`, `Monica and Phoebe:` o.s.frv. eru **ekki**
  eignaðar einstaklingum (338 `All:`-línur o.fl.).
- **Phoebe Sr. (móðirin), Ursula (tvíburasystirin) og Mrs Buffay teljast EKKI Phoebe.**
  Þær eru sérstakar persónur í gögnunum (51 / 71 / 7 línur).
- Skammstafanir úr þáttaröð 2 (`Phoe:`, `Mnca:`, `Chan:`, `Rach:`) eru samræmdar.
- Nafnmyndir Phoebe: `\bph(oe|ee)b\w*\b` → *Phoebe, Phoebe's, Phoebs, Pheebs, Pheeboh*.

---

# A. Skrár sem vefsíðan les

`site/friends/phoebe-statistics.qmd` les þessar sex skrár gegnum symlinkið
`site/friends/phoebe-stats`. **Skráarnöfn og dálkaheiti eru samningur — ekki breyta
þeim án þess að uppfæra síðuna líka.**

Allar CSV: UTF-8, komma sem skil, haus í fyrstu línu, **punktur** sem tugabrot.
Nöfn persóna eru hástafuð (`Phoebe`, `Rachel`, …).

### `summary.json`

| Lykill | Tag | Skýring |
|---|---|---|
| `placeholder` | bool | `false` — þetta eru **raunniðurstöður** |
| `generated_at` | strengur | Dagsetning keyrslu, `YYYY-MM-DD` |
| `source` | strengur | Stutt lýsing á gagnagrunni |
| `character` | strengur | `"Phoebe Buffay"` |
| `characters` | listi | Persónurnar sex í birtingarröð |
| `seasons` / `episodes` | heiltala | `10` / `236` |
| `episodes_present` | heiltala | Þættir með a.m.k. eina Phoebe-línu (`236` — hún er í öllum) |
| `lines_total` | heiltala | `7483` |
| `words_total` | heiltala | `83788` |
| `line_share` | tala 0–1 | Hlutdeild af línum vinanna sex (`0.1472`) |
| `line_share_baseline` | tala | `0.1667` (= 1/6, jöfn skipting) |
| `words_per_line` | tala | `11.2` |
| `words_per_line_others` | tala | Sama fyrir hina fimm samanlagt (`10.7`) |
| `top_partner` | strengur | Sá sem á flestar línur beint til Phoebe (`"Monica"`) |

### `screentime-by-season.csv` — 60 línur (6 persónur × 10 þáttaraðir)

| Dálkur | Tag | Skýring |
|---|---|---|
| `season` | heiltala | 1–10 |
| `character` | strengur | Ein af persónunum sex |
| `lines` | heiltala | Línur í þáttaröðinni |
| `words` | heiltala | Töluð orð í þáttaröðinni |
| `line_share` | tala 0–1 | Hlutdeild af línum vinanna sex; leggst saman í 1,0 innan þáttaraðar |

### `mentions-by-season.csv` — 10 línur

| Dálkur | Tag | Skýring |
|---|---|---|
| `season` | heiltala | 1–10 |
| `mentions` | heiltala | Hversu oft nafn Phoebe er nefnt **í töluðu máli** (allir, líka hún sjálf) |
| `episodes` | heiltala | Fjöldi þátta í þáttaröðinni |
| `mentions_per_episode` | tala | `mentions / episodes` |

Nefningar í sviðsleiðbeiningum eru **ekki** taldar hér (þær eru í
`phoebe-mentions-by-season.json`).

### `speaks-with-phoebe.csv` — 15 línur (vinirnir fimm + 10 aðrar persónur)

| Dálkur | Tag | Skýring |
|---|---|---|
| `character` | strengur | Persóna (aldrei Phoebe sjálf) |
| `lines_to_phoebe` | heiltala | Skipti sem persónan talar **strax á eftir** Phoebe innan sömu senu |
| `lines_from_phoebe` | heiltala | Skipti sem Phoebe talar **strax á eftir** persónunni |
| `scenes_together` | heiltala | Senur þar sem báðar tala |

### `interaction-matrix.csv` — 30 línur (öll röðuð pör innan vinanna sex)

| Dálkur | Tag | Skýring |
|---|---|---|
| `speaker` | strengur | Sá sem talar |
| `addressee` | strengur | Sá sem talað er við |
| `lines` | heiltala | Skipti sem `speaker` talar strax á eftir `addressee` |

Fylkið er **ósamhverft** og tölurnar stemma við `speaks-with-phoebe.csv`.
Gagnleg staðfesting: sterkustu pörin eru Ross↔Rachel (2478/2416) og
Chandler↔Monica (2279/2219) — nákvæmlega parasamböndin tvö í þáttunum.

### `signature-phrases.csv` — 11 línur

| Dálkur | Tag | Skýring |
|---|---|---|
| `phrase` | strengur | Orðasambandið |
| `count` | heiltala | Hversu oft **Phoebe** segir það |
| `first_season` / `last_season` | heiltala | Fyrsta/síðasta þáttaröð þar sem hún segir það |

---

# B. Ítarskrár úr greiningunni

Þessar skrár innihalda fulla greiningu með aðferðafræði og stuðningsmælikvörðum.
JSON-skrárnar hafa `question`, `method`, `unit` og `headline` reiti efst.

| Skrá | Innihald |
|---|---|
| `phoebe-top-talkers.json` | Spurning 1 — hver talar mest við Phoebe. `overall`, `by_season`, `non_friend_characters` |
| `phoebe-top-talkers.csv` | `overall`-hlutinn flatur (5 línur) |
| `phoebe-top-talkers-by-season.csv` | 50 línur (5 persónur × 10 þáttaraðir) |
| `phoebe-mentions-by-season.json` | Spurning 2 — full sundurliðun nefninga + samanburður við hin nöfnin |
| `phoebe-mentions-by-season.csv` | Sama, flatt (10 línur, 15 dálkar) |
| `phoebe-screentime-by-season.json` | Spurning 3 — `overall`, `by_season`, `phoebe_share_trend` |
| `phoebe-screentime-by-season.csv` | 60 línur með fleiri mælikvörðum en samningsskráin |
| `phoebe-per-episode.csv` | **227 línur — ein per handritsskrá.** Fínasta upplausnin sem til er |
| `phoebe-extra-stats.json` | Spurning 4 — málgleði, toppþættir, þemaorð, samnefni, tengsl |
| `phoebe-distinctive-words.csv` | 60 einkennandi orð með z-gildi |
| `_meta.json` | Uppruni, gæðamat þáttunar, samtölur, allar reglur |

### Lykildálkar í `phoebe-top-talkers.csv`

| Dálkur | Skýring |
|---|---|
| `adjacent_turns` | `replies_to_phoebe + phoebe_replies_to` — **aðalmælikvarðinn** |
| `replies_to_phoebe` | X talar strax á eftir Phoebe |
| `phoebe_replies_to` | Phoebe talar strax á eftir X |
| `two_person_scene_lines` | Línur í senum þar sem **aðeins** Phoebe og X tala |
| `shared_speaking_scenes` | Senur þar sem báðar tala |
| `lines_mentioning_phoebe` | Línur X sem nefna Phoebe á nafn |
| `lines_naming_phoebe_at_edge` | Nafnið í fyrstu eða síðustu 3 orðum (ávarpsmerki) |
| `interaction_lift` | Hlutfall af samskiptum Phoebe **deilt með** hlutdeild X í öllum línum. `> 1` = X talar oftar við Phoebe en málgleði hans ein og sér skýrir |

`interaction_lift` er mikilvægur: hrátt `adjacent_turns` hyglar þeim sem tala mikið
hvort eð er. Lift leiðréttir fyrir því.

### Lykildálkar í `phoebe-mentions-by-season.csv`

| Dálkur | Skýring |
|---|---|
| `mentions_in_dialogue_by_others` | Nefningar í töluðu máli **annarra** |
| `mentions_in_own_dialogue` | Phoebe nefnir sjálfa sig |
| `mentions_in_dialogue_total` | Summa þessara tveggja (= `mentions` í samningsskránni) |
| `mentions_in_stage_directions` | Í `[Scene: …]`, `(hlær)` og `(til Phoebe)`-innskotum |
| `mentions_total` | Allt samanlagt |
| `mentions_formal_phoebe` / `mentions_nickname_pheebs` | *Phoebe* á móti *Pheebs*; summan = `mentions_in_dialogue_total` |
| `dialogue_mentions_per_episode` | Leiðrétt fyrir mislöngum þáttaröðum — **notið þennan í samanburði** |
| `change_vs_prev_season_pct` | Breyting frá fyrri þáttaröð (`null` í þáttaröð 1) |

### `phoebe-per-episode.csv` (227 línur)

`episode_code`, `season`, `title`, `n_aired_episodes`, `friends_lines_total`,
`friends_words_total`, `phoebe_lines`, `phoebe_words`, `phoebe_line_share_pct`,
`phoebe_word_share_pct`, og svo `{persóna}_lines` / `{persóna}_words` fyrir allar sex.

`episode_code` er skráarnafnið án `.html` (`0101`, `0212-0213`). Þar sem
`n_aired_episodes = 2` nær línan yfir tvo sýnda þætti — það skýrir hvers vegna
`0523` og `1017-1018` eru efst í fjölda lína.

### `phoebe-distinctive-words.csv`

z-gildi úr log-odds hlutfalli með Dirichlet-prior (Monroe, Colaresi & Quinn 2008),
Phoebe á móti hinum fimm. Hátt jákvætt z = orð sem Phoebe notar hlutfallslega
miklu oftar. Aðeins orð sem koma ≥ 40 sinnum fyrir, án algengra stopporða.

`phoebe_per_10k` / `others_per_10k` eru tíðnir á hver 10.000 orð og eru
**samanburðarhæfar** þótt Phoebe eigi færri orð alls.

---

## Helstu niðurstöður

- **Phoebe á fæstar línur** af vinunum sex: 7.483 (14,7%) á móti jöfnu 16,7%.
  Það á við í **öllum tíu þáttaröðum**.
- **En hún talar lengst í einu:** 11,2 orð á línu — hæst allra sex.
- **Monica og Rachel eru í raun jafnar** um það hver talar mest við Phoebe
  (2.718 á móti 2.701 ræðuskiptum, 0,6% munur). Rachel á fleiri tveggja-manna
  senur (677 á móti 522) og nefnir hana oftar (322 á móti 272); Monica er hærri í lift (1,31).
- **Chandler er fjærst Phoebe:** aðeins 131 lína í tveggja-manna senum og
  lift 0,75.
- **Þáttaröð 5 er hápunktur Phoebe** í nefningum (8,75 á þátt, +76% frá þáttaröð 4).
- **Phoebe er fjórða mest nefnda persónan** af sexmenningunum (1.385 nefningar);
  Ross er efstur (1.826).
