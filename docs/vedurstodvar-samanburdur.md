# Veðurstöðvar — frosið eintak borið við gömlu síðuna

Veðurstöðvarnar eru eina gagnasafnið í verkefninu sem **átti sér ekkert
eintak**. Gamla verkefnið sótti stöðvalistann upp á nýtt í hverri byggingu og
vistaði svarið aldrei, svo gamla veðurstöðvasíðan gat sýnt aðrar tölur í dag en
í gær án þess að nokkur tæki eftir því.

P0.3 (issue #2) sótti **eitt** eintak og frysti það. Þetta skjal svarar
spurningunni sem frystingin kallar á: *hvað víkur frosna eintakið frá því sem
gamla síðan birti?* Munur er vænt niðurstaða, ekki villa — það er ekki hægt að
bera frosið gagn við gagn sem var aldrei fryst og vænta þess að þau séu eins.

Skjalið er **afleitt**: það verður til úr
`src/python/vinnsla/vedurstodvar_samanburdur.py` og er ekki handbreytt (regla 10).

---

## 1. Hvað er borið saman

| | Heimild |
|---|---|
| **Frosið eintak** | `data/raw/vedurstodvar/stations-20260924T112218Z.json` (provenance í sömu möppu) |
| **Viðmið** | `docs/vidmid/generated/vedurstofa-siur.md`, `-nidurstada.md` og `-svor.md` — byggð 2026-09-17 |

Fjöldatölurnar eru **lesnar** úr viðmiðsskjalinu, ekki slegnar inn. Gamla síðan
sendi fimm beiðnir; frosna eintakið er ósíaða svarið og síurnar fjórar eru
reiknaðar staðbundið úr því með sömu skilyrðum og gamla skriftan sendi
þjónustunni.

## 2. Fjöldi stöðva í hverri síu

| Sía í beiðninni | Viðmið (gamla síðan) | Frosið eintak | Munur |
|---|---:|---:|---:|
| engin sía | 778 | 778 | — |
| `active=true` | 343 | 343 | — |
| `polygon` | 21 | 21 | — |
| `polygon` + `active=true` | 9 | 9 | — |
| `station_id=1469` | 1 | 1 | — |

Af stöðvunum eru 435 aflagðar — reiturinn `ending` er
ártal en ekki tómt. Listinn er því ekki listi yfir stöðvar í rekstri heldur
allar stöðvar sem Veðurstofan þekkir, virkar og aflagðar.

## 3. Stöðvavalið sjálft

| Spurning | Viðmið (gamla síðan) | Frosið eintak | Sama stöð? |
|---|---|---|:-:|
| Næsta virka stöð við VR-II | Reykjavík Hljómskálagarður (1469), 639 m | Reykjavík Hljómskálagarður (1469), 639 m | ✅ |
| Næsta aflagða stöð | Sjómannaskóli (2), 689 m | Sjómannaskóli (2), 689 m | ✅ |
| Næsta virka stöð sem mælir 50 ár aftur | Reykjavík (1), 2547 m | Reykjavík (1), 2547 m | ✅ |

Hnit VR-II: 64.1386922, -21.9556406 — Nominatim (OpenStreetMap), flett upp 2026-09-03 í upprunaverkefninu.

## 4. Niðurstaða

**Allar tölur stemma.** Frosna eintakið gefur sömu fjöldatölur og sama stöðvaval og gamla síðan birti, þrátt fyrir að vera sótt viku síðar og óháð henni.

Það þýðir **ekki** að listinn sé stöðugur. Stöðvaskrá Veðurstofunnar er lýsigagnaskrá sem breytist þegar stöð er sett upp eða tekin niður, ekki mælingaröð sem breytist á klukkutíma fresti. Vikan sem skilur eintökin að var einfaldlega vika án breytinga. Næsta uppfærsla þjónustunnar getur hreyft hvaða tölu sem er hér — og gerði það óséð í hverri byggingu gömlu síðunnar, því hún vistaði svarið aldrei.

## 5. Takmarkanir sem fylgja þessu safni

- Eintakið er **ný söfnun**, ekki afrit af því sem gamla síðan sá. Tala sem
  víkur frá gömlu síðunni er breyting á stöðvaskránni, ekki villa.
- Eintakið er **ekki lifandi staða**. Stöð sem bætist við eða er tekin niður
  eftir söfnunardag kemur ekki fram fyrr en nýtt eintak er fryst.
- Stöðin sem síðan les, Reykjavík Hljómskálagarður (1469), hóf mælingar
  2022 og á því engar mælingar frá því fyrir þann tíma.
- Nálægð og samfelld tímaröð eru tvö ólík skilyrði; sama stöðin uppfyllir
  sjaldnast bæði. Röðun eftir fjarlægð einni saman getur skilað aflagðri stöð.

---

*Afleitt skjal úr eintaki sem var sótt 2026-09-24T11:22:18Z, byggt af `src/python/vinnsla/vedurstodvar_samanburdur.py`. Sama keyrsla á sömu gögnum gefur sama skjal — óháð því hvenær hún er gerð.*
