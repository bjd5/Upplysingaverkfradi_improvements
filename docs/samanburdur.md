# Samanburður við upprunalega verkefnið

Viðmiðið er frosið afrit af tölum gömlu síðunnar: [`vidmid/vidmid.json`](vidmid/vidmid.json). Í því eru 1.255 tölur úr 24 síðum, þar af 417 efnislegar niðurstöður. Spurningin er einföld: sýnir nýja síðan sömu tölur?

Prófið `tests/test_vidmid_samanburdur.py` ber hverja efnislega tölu við `web/gogn/*.json` og fellur ef taflan hér á eftir segir annað en kóðinn reiknar. Reglurnar eru í `tests/vidmid_reglur.py`.

```bash
python3 -m unittest discover -s tests -p "test_vidmid_samanburdur.py"
```

Hver tala fær einn flokk. **Stemmir** og **víkur** ráðast af raunverulegum samanburði; flokkurinn er aldrei skrifaður inn. **Á ekki við** og **ekki borið saman** eru ákvarðanir með ástæðu.


## Niðurstaða

Af 417 efnislegum tölum eru 288 bornar saman: 266 stemma og 22 víkja, allar með skýringu. Hinar 129 eru ekki bornar saman (70 eiga ekki lengur við, 59 af öðrum ástæðum). Allar 16 staðfestu tölurnar stemma.

## Síða fyrir síðu

| Gömul síða | Ný síða | Efnislegar | Bornar saman | Stemma | Víkja | Á ekki við | Ekki borið saman |
|---|---|---:|---:|---:|---:|---:|---:|
| `capstone/earthquakes.html` | skjalftavaktin | 89 | 87 | 87 | 0 | 0 | 2 |
| `friends/index.html` | friends-gagnasagan | 16 | 10 | 7 | 3 | 0 | 6 |
| `friends/phoebe-statistics.html` | phoebe-tolfraedi | 23 | 18 | 18 | 0 | 0 | 5 |
| `friends/phoebe-tribute.html` | phoebe-tribute | 5 | 0 | 0 | 0 | 0 | 5 |
| `friends/uppahalds-video.html` | uppahalds-video | 0 | 0 | 0 | 0 | 0 | 0 |
| `index.html` | forsíða | 2 | 2 | 2 | 0 | 0 | 0 |
| `lotur/git-ai-reproducible/agents.html` | — | 6 | 0 | 0 | 0 | 6 | 0 |
| `lotur/git-ai-reproducible/git.html` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| `lotur/git-ai-reproducible/index.html` | — | 2 | 0 | 0 | 0 | 2 | 0 |
| `lotur/git-ai-reproducible/reproducible-reports.html` | — | 14 | 0 | 0 | 0 | 14 | 0 |
| `lotur/logic-sets/index.html` | — | 1 | 0 | 0 | 0 | 1 | 0 |
| `lotur/regex/index.html` | phoebe-tolfraedi | 3 | 2 | 2 | 0 | 0 | 1 |
| `lotur/regex/mbl.html` | mbl-regex | 57 | 38 | 19 | 19 | 0 | 19 |
| `lotur/sql-advanced/index.html` | — | 3 | 0 | 0 | 0 | 3 | 0 |
| `lotur/sql-basics/index.html` | — | 2 | 0 | 0 | 0 | 2 | 0 |
| `lotur/storytelling/index.html` | — | 1 | 0 | 0 | 0 | 1 | 0 |
| `lotur/vefthjonustur/hagstofan.html` | hagstofan | 84 | 82 | 82 | 0 | 0 | 2 |
| `lotur/vefthjonustur/vedurstofan.html` | vedurstodvar | 41 | 28 | 28 | 0 | 0 | 13 |
| `phoebe-central-perk.html` | phoebe-central-perk | 28 | 21 | 21 | 0 | 1 | 6 |
| `project-management.html` | — | 23 | 0 | 0 | 0 | 23 | 0 |
| `reflections/bjorn.html` | — | 1 | 0 | 0 | 0 | 1 | 0 |
| `reflections/ottar.html` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| `reflections/sveinn.html` | — | 0 | 0 | 0 | 0 | 0 | 0 |
| `team.html` | — | 16 | 0 | 0 | 0 | 16 | 0 |
| Samtals | | 417 | 288 | 266 | 22 | 70 | 59 |

Nýja síðan `adferdafraedi` á sér enga gamla samsvörun; hún lýsir aðferðinni sjálfri. `phoebe-tmdb` er biðstaða (sjá „Ekki borið saman“).

## Staðfestu tölurnar

Sextán tölur eru staðfestar í viðmiðinu (`stadfestar`). Hver þeirra er lesin úr nýju gagnaskránni og borin við gildið.

| Heiti | Gildi | Ný gagnaskrá | Stemmir |
|---|---:|---|---|
| jarðskjálftar | 334 | `skjalftar.json` | já |
| dagar í glugganum | 61 | `skjalftar.json` | já |
| handritsskrár | 227 | `phoebe-tolfraedi.json` | já |
| þættir | 236 | `phoebe-tolfraedi.json` | já |
| textablokkir alls | 70.553 | `phoebe-tolfraedi.json` | já |
| tilsvör | 61.161 | `phoebe-tolfraedi.json` | já |
| sviðsfyrirsagnir | 4055 | `phoebe-tolfraedi.json` | já |
| sviðsleiðbeiningar | 3259 | `phoebe-tolfraedi.json` | já |
| óflokkað | 2078 | `phoebe-tolfraedi.json` | já |
| óflokkað hlutfall | 2,95 | `phoebe-tolfraedi.json` | já |
| línur Phoebe | 7483 | `phoebe-tolfraedi.json` | já |
| línur Rachel | 9259 | `phoebe-tolfraedi.json` | já |
| línur Ross | 9058 | `phoebe-tolfraedi.json` | já |
| línur Chandler | 8446 | `phoebe-tolfraedi.json` | já |
| línur Monica | 8395 | `phoebe-tolfraedi.json` | já |
| línur Joey | 8183 | `phoebe-tolfraedi.json` | já |

## Frávik

Tuttugu og tvö gildi víkja frá gömlu síðunni. Öll eru skýrð og prófið ber hvert þeirra við þessa töflu.

### mbl-eintakið er nýtt

Gamla síðan byggði á eintaki frá 7.9.2026. Það er glatað: hrágögnin voru aðeins á einni vél. Nýja síðan notar eintak frá 16.9.2026, sem gamla síðan sótti líka og bar saman við fyrra eintakið. Allar tölur 16.9.-dálksins stemma.

Fréttirnar eru 43 í stað 42, gengið 121,33 í stað 121,05, orðin 2.188 í stað 2.127 og auglýsingareitirnir 47 í stað 50. Hitinn, 11 °C, er sá sami. Tölurnar eru endurskapanlegar héðan í frá; samanburðurinn við 7.9. er það ekki.

### Tvöfaldir þættir og „línur“

Níu skrár geyma tvöfalda þætti, svo 227 skrár ná yfir 236 þætti. Gamla forsíða Friends taldi 223 skrár með stöku þáttanúmeri; réttu töluna, 218, gefa 227 − 9.

Hún taldi líka „um 69.500 línur“ eftir þáttun. Það er áætlun delvinso. Nýja síðan telur 70.553 textablokkir og 61.161 tilsvör.

### Öll frávik

| Gömul tala | Mæling | Gamalt | Nýtt | Skýring |
|---|---|---:|---:|---|
| `lotur/regex/mbl.html#0009` | Stærð eintaks (bæti) | 370.113 | 367.351 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0019` | Einstakar fréttir | 42 | 43 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0021` | Gengi USD (ISK) | 121,05 | 121,33 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0023` | Sýnileg orð | 2127 | 2188 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0024` | Auglýsingareitir | 50 | 47 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0026` | Fréttahlekkjatilvik | 96 | 99 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0027` | Einstakar fréttir | 42 | 43 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0048` | Gengi USD (ISK) | 121,05 | 121,33 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0054` | Sýnileg orð | 2127 | 2188 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0067` | Auglýsingareitir | 50 | 47 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0070` | Auglýsingareitir | 50 | 47 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0074` | MD5-hakk eintaks (upphaf) | 020024 | c2c83b | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0076` | Einstakar fréttir | 42 | 43 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0078` | Gengi USD (ISK) | 121,05 | 121,33 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0079` | Sýnileg orð | 2127 | 2188 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0080` | Auglýsingareitir | 50 | 47 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0092` | Fréttahlekkjatilvik | 96 | 99 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0094` | Einstakar fréttir | 42 | 43 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `lotur/regex/mbl.html#0095` | Gengi USD (ISK) | 121,05 | 121,33 | mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026 |
| `friends/index.html#0012` | „Línur“ eftir þáttun | 69.500 | 70.553 | talan 69.500 er áætlun delvinso; textablokkir hér eru taldar úr sömu handritum |
| `friends/index.html#0014` | Skrár með stöku þáttanúmeri | 223 | 218 | gamla talan er 229 − 6: hún taldi fjórar bandstriksskrár og tvær undanskildar, en níu skrár geyma tvo þætti |
| `friends/index.html#0021` | „Línur“ eftir þáttun | 69.500 | 70.553 | talan 69.500 er áætlun delvinso; textablokkir hér eru taldar úr sömu handritum |

### Ósamræmi innan gömlu síðnanna

Gömlu síðurnar voru byggðar í þremur lotum og ósamræmi milli þeirra er skráð í viðmiðinu. Nýja síðan notar eitt hugtak fyrir hvert.

| Ósamræmi | Nýja síðan |
|---|---|
| Fjöldi skráa sem geyma tvöfalda þætti | níu skrár; 227 + 9 = 236 |
| Orðið „lína“ merkir þrennt | tilsvör 61.161, textablokkir 70.553; engin tala delvinso |
| phoebe-top-talkers.json er í tveimur röðum | birtir ekki raðaða lista utan vinanna sex; röðin er ekki borin saman |
| _meta.json er í tveimur eintökum frá tveimur keyrslum | eitt eintak (17.9.2026); allar tölur stemma |
| Talan 236 var eitt sinn birt sem skráafjöldi | skrár 227, þættir 236 |

## Ekki borið saman

Talan er ekki niðurstaða úr nýju gögnunum, eða nýja síðan sýnir hana ekki. Fjöldi og ástæða eru prófuð.

| Gömul síða | Flokkur | Fjöldi | Ástæða |
|---|---|---:|---|
| `capstone/earthquakes.html` | ekki borið saman | 2 | númer regex-skrefs í fyrirsögn, ekki niðurstaða |
| `lotur/vefthjonustur/hagstofan.html` | ekki borið saman | 2 | fyrirsögn eða gildissvið staðfestingar, ekki niðurstaða |
| `lotur/vefthjonustur/vedurstofan.html` | ekki borið saman | 9 | tala í texta, nafni eða lista, ekki niðurstaða |
| `lotur/vefthjonustur/vedurstofan.html` | ekki borið saman | 2 | HTTP-staða beiðnanna er ekki vistuð í nýju gagnaskránni |
| `lotur/vefthjonustur/vedurstofan.html` | ekki borið saman | 2 | fasti í reiknireglu (111 km á breiddargráðu), ekki niðurstaða |
| `lotur/regex/mbl.html` | ekki borið saman | 3 | tala í texta, nafni eða lista, ekki niðurstaða |
| `lotur/regex/mbl.html` | ekki borið saman | 5 | númer kafla í fyrirsögn |
| `lotur/regex/mbl.html` | ekki borið saman | 10 | orðatíðnitaflan er ekki í nýju gögnunum — mbl.json geymir aðeins fimm spurningar |
| `lotur/regex/mbl.html` | ekki borið saman | 1 | fjöldi prófa gamla kóðans, ekki niðurstaða úr eintaki |
| `friends/phoebe-statistics.html` | ekki borið saman | 3 | dæmi um eitt handritsbrot, ekki niðurstaða úr gögnunum |
| `friends/phoebe-statistics.html` | ekki borið saman | 2 | teljari brotsins 1/6 |
| `phoebe-central-perk.html` | ekki borið saman | 6 | tala í aðferðalýsingu eða tilvísun í aðra greiningu, ekki niðurstaða |
| `lotur/regex/index.html` | ekki borið saman | 1 | þáttaröð 2 í texta, ekki niðurstaða |
| `friends/index.html` | ekki borið saman | 6 | samanburður handritasafnanna tveggja, ekki í nýju gögnunum |
| `friends/phoebe-tribute.html` | ekki borið saman | 5 | biðstaða — nýja síðan birtir engar tölur úr þessu efni |

### Á ekki við lengur

Lotusíður, ígrundanir og teymissíður fluttust ekki (umfangið er í [`endurbygging.md`](endurbygging.md), kafla 3). Tokenmælaborðið var fjarlægt úr viðmiðinu.

| Gömul síða | Flokkur | Fjöldi | Ástæða |
|---|---|---:|---|
| `phoebe-central-perk.html` | á ekki við | 1 | innfelling á upprunahandriti var tekin út (höfundaréttur, issue #3) |
| `lotur/git-ai-reproducible/agents.html` | á ekki við | 6 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `lotur/git-ai-reproducible/index.html` | á ekki við | 2 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `lotur/git-ai-reproducible/reproducible-reports.html` | á ekki við | 14 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `lotur/logic-sets/index.html` | á ekki við | 1 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `lotur/sql-advanced/index.html` | á ekki við | 3 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `lotur/sql-basics/index.html` | á ekki við | 2 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `lotur/storytelling/index.html` | á ekki við | 1 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `project-management.html` | á ekki við | 23 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `reflections/bjorn.html` | á ekki við | 1 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |
| `team.html` | á ekki við | 16 | lotusíða, ígrundun eða teymissíða — utan umfangs (endurbygging.md, kafli 3) |

### Biðstöður

| Ný síða | Gömul síða | Ástæða |
|---|---|---|
| `friends-gagnasagan` | `friends/index.html` | Síðan birtir engar tölur enn. Tíu tölur gömlu síðunnar eru bornar við nýju gögnin: sjö stemma og þrjár víkja; sex eru ekki bornar saman. |
| `phoebe-tmdb` | — | TMDB-gögnin voru aldrei varðveitt ([`takmarkanir.md`](takmarkanir.md)). |
| `uppahalds-video` | `friends/uppahalds-video.html` | Gamla síðan hafði enga tölu. |
| `phoebe-tribute` | `friends/phoebe-tribute.html` | Biðstaða; fimm tölur um TMDB-köll eru ekki bornar saman. |
