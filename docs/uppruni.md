# Uppruni — nýtt efni úr gamla verkefninu

Gamla verkefnið ([`Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe`](https://github.com/Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe))
er enn í vinnslu. Hér er lýst hvernig nýtt efni þaðan er flokkað, yfirfarið og
flutt hingað.

## Hvernig það gengur fyrir sig

1. **Daglega** keyrir sjálfvirk Claude Code-lota `scripts/yfirfara-uppruna.sh`.
2. Skriftan ber upprunann saman við síðustu yfirferð
   ([`uppruni/stada.json`](uppruni/stada.json)) og flokkar hverja breytta skrá
   eftir reglunum í [`config/uppruni.json`](../config/uppruni.json).
3. Sé eitthvað nýtt flytur lotan það hingað samkvæmt töflunni hér að neðan,
   lagar það sem brýtur reglurnar og opnar **eitt PR**. Björn samþykkir.

Handvirk keyrsla:

```bash
scripts/yfirfara-uppruna.sh            # prentar skýrsluna
scripts/yfirfara-uppruna.sh --skrifa   # vistar hana í docs/uppruni/ og færir stöðuna
```

## Hvað er gert við hvern flokk

| Flokkur | Hvað er gert |
|---|---|
| **Hrágögn** | Nýtt safn: bætt í `SOFN` í `src/python/sofnun/frysta_afrit.py` og fryst. Frosnu safni er aldrei breytt (regla 4) — ný eða breytt skrá í því er skráð sem opið atriði í PR-inu. |
| **Kóði** | Breytingin flutt í markeininguna: undir 300 línum, staðalsafnið eitt, SQL með breytum. |
| **Próf** | Prófin flutt í samsvarandi prófskrá hér. |
| **Síða** | Texti og niðurstöður uppfærð á síðunni. Stutt og skýrt; HTML, CSS og JS aðskilin (regla 2). |
| **Skjölun** | Það sem skiptir lesanda máli fer í `docs/heimildir.md` eða `docs/adferdafraedi.md`, stytt. |
| **Þarf ákvörðun** | Ekki flutt. Eitt issue á hvert efni svo Björn geti ákveðið. |
| **Bannað** | Aldrei afritað (handrit, P0.5). |
| **Óflokkað** | Regla bætt í `config/uppruni.json` og keyrt aftur. |
| **Utan umfangs** | Ekkert gert (endurbygging.md §3). |

Sjálfvirku athugasemdirnar í skýrslunni (of löng skrá, inline CSS, leyndarmál,
pakkar utan staðalsafns o.s.frv.) eru lagaðar um leið og skráin er flutt.

## Reglur

- **Tölur sem breytast** í upprunanum eru bornar við viðmiðið. Viðmiðinu
  (`docs/vidmid/`) er aldrei breytt; munurinn er skráður í PR-inu.
- **Eitt PR í einu.** Sé PR frá fyrri yfirferð enn opið bíður lotan.
- **Staðan færist aðeins með samruna:** `--skrifa` er keyrt í sama PR og
  flutningurinn, svo ekkert týnist þótt PR sé hafnað.
- Upprunarepo-ið er **aðeins lesið**. Þangað er aldrei ýtt.
