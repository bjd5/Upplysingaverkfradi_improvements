# Myndrit — frá gögnum til SVG

Hvernig myndritin á vefsíðunni verða til, hvaða kröfur þau standast og hvernig
síða notar þau. Skráin er skjölun **myndritalagsins** (issue #17); fyrsta
myndritið sem notar það er sýnidæmið fyrir Skjálftavaktina (issue #20).

---

## 1. Ákvörðunin

Björn valdi 27.9.2026 **valkost A** á
[#17](https://github.com/bjd5/Upplysingaverkfradi_improvements/issues/17#issuecomment-5857519732):
Python teiknar myndritin sem SVG við útflutning. Samþykkið á matplotlib (regla 10)
fylgir skilyrðum sem öll eru uppfyllt hér:

| Skilyrði | Hvernig það er uppfyllt |
|---|---|
| matplotlib **eingöngu** í `src/python/utflutningur/` | Aðeins `myndrit.py` og `myndrit_skjalftar.py` flytja það inn. |
| `python3 -m unittest discover -s tests` keyrir á staðalsafninu einu | Teikniprófin (`tests/test_myndrit_svg.py`) sleppa sér með `skipUnless` þegar matplotlib vantar. |
| Pakki og útgáfa skráð með rökum | Kafli 8 hér að neðan. |
| Litir úr `tokens.css` (regla 3.1) | `lesa_tokens()` les skrána; Python þekkir engan lit sjálft. |
| Litur aldrei eina merkingarberan (regla 3.3) | Núll-dagar fá sérstaka lögun og texta — kafli 4. |
| Gagnatafla í HTML-inu | HTML-brotið í kafla 7. |

Rökin fyrir valinu (JS-laus síða, engin framework) eru á issue-inu. Skráning
þeirra í `docs/adferdafraedi.md` tilheyrir issue #3 og er ekki gerð hér.

---

## 2. Leiðin

```
data/raw/vedur-quakes/events.json        (frosið, aldrei breytt)
        │  vinnsla.jardskjalftar.lesa_skjalfta        — sannreynir hverja færslu
        ▼
dagleg_talning()                          (vinnsla.jardskjalftar_talning)
        │  61 lína, ein á hvern UTC-dag, núll-dagar með
        ▼
utflutningur.myndrit_skjalftar.byggja_mynd()
        │  litir, letur og stærðir úr web/assets/css/tokens.css
        │  (utflutningur.tokens.lesa_tokens — ljóst og dökkt þema)
        ▼
web/assets/img/skjalftar-dagar-ljost.svg
web/assets/img/skjalftar-dagar-dokkt.svg
```

Keyrsla (þarf Python með matplotlib, sjá kafla 8):

```bash
PYTHONPATH=src/python python -m utflutningur.myndrit_skjalftar
```

Keyrslan stöðvast með skýringu, og skrifar ekkert, ef einhver litur myndritsins
fellur undir andstæðukröfuna í kafla 3.

SVG-skrárnar eru **afleiddar**. Þeim er aldrei breytt í hendi; breytist
`tokens.css` eða gögnin eru þær endurteiknaðar. Prófið
`test_vistudu_skrarnar_eru_i_takt_vid_gogn_og_tokens` fellur ef vistaða skráin
og ný teikning eru ekki sömu bæti.

### Einingarnar

| Skrá | Hlutverk | Þarf matplotlib |
|---|---|---|
| `utflutningur/tokens.py` | Les `tokens.css`, leysir `var()`, skilar báðum þemum | nei |
| `utflutningur/myndrit_litir.py` | Litahlutverk `--myndrit-*`, kröfur þeirra og WCAG 2.1 andstæðumæling | nei |
| `utflutningur/islenskt_snid.py` | `5,5`, `1.234`, `70,5%`, `1. nóv.` — án `locale` | nei |
| `utflutningur/myndrit.py` | Sameiginlega lagið: rcParams úr tokens, ákvarðað SVG | **já** |
| `utflutningur/myndrit_skjalftar.py` | Sýnidæmið: daglegir skjálftar | **já** |

Nýtt myndrit (t.d. fyrir veðurstöðvarnar) skrifar eigið `byggja_mynd()` og
kallar í `myndrit.thema_samhengi`, `myndrit.nytt_myndrit` og `myndrit.svg_baeti`.
Litir, letur, ákvarðað úttak og letursnið fylgja þá sjálfkrafa.

---

## 3. Litir og mæld andstæða

Litahlutverkin eru skilgreind í `tokens.css` undir `--myndrit-*` og mæld gegn
`--myndrit-bak` í báðum þemum. Mælt með `utflutningur.myndrit_litir` (WCAG 2.1):

| Hlutverk | Token | Ljóst | Dökkt | Krafa |
|---|---|---|---|---|
| súluflötur | `--myndrit-flotur` | `#12657d` á `#ffffff` — **6,60:1** | `#6cbcd4` á `#121a23` — **8,17:1** | 4,5:1 |
| núll-merki | `--myndrit-null` | `#9a4614` á `#ffffff` — **6,44:1** | `#e08a4a` á `#121a23` — **6,60:1** | 4,5:1 |
| ásmerkingar, titill | `--myndrit-texti` | `#1e2935` — **14,75:1** | `#eceff3` — **15,20:1** | 4,5:1 |
| heimildarlína | `--myndrit-texti-dauft` | `#4f5d6e` — **6,72:1** | `#b4bfcc` — **9,41:1** | 4,5:1 |
| ásar | `--myndrit-as` | `#4f5d6e` — **6,72:1** | `#b4bfcc` — **9,41:1** | 3,0:1 |
| hjálparlínur | `--myndrit-grind` | 1,86:1 | 1,66:1 | ekki mælt — skraut |

Súlan og núll-merkið eru mæld gegn **4,5:1** þótt WCAG 1.4.11 krefjist aðeins
3:1 fyrir grafík, því #17 krefst 4,5:1 fyrir myndritið. Ásarnir fá 3:1: þeir
afmarka flöt en bera ekki gildi. Hjálparlínurnar bera enga merkingu — gildin
eru lesin af ásmerkingunum — og mega því vera daufar.

`tests/test_myndrit_tokens.py` (staðalsafnið eitt, keyrir alltaf) fellur ef
eitthvert hlutverk fer undir kröfu sína í hvoru þema sem er. Prófið er líka
keyrt á falsaðri `tokens.css` til að sýna að það bresti — sitt í hvoru þema.

### Súla gegn núll-merki: 1,02:1 og 1,24:1

Súluflöturinn og núll-merkið hafa nánast sama ljósstyrk (ljóst 1,02:1, dökkt
1,24:1). **Það er ásættanlegt, og tokenin eru látin standa**, af tveimur ástæðum:

1. Munurinn er ekki borinn af lit. Súludagur er fylltur ferhyrningur sem rís upp
   ásinn; núll-dagur er **opinn hringur** við grunnlínuna, og skýringin nefnir
   hann með orðum: *„Enginn atburður í úrtakinu (0)“*. Á gráskalaútprenti eða
   hjá litblindum lesanda greinast dagarnir á lögun og texta.
2. Litablærinn er blágrænn gegn brenndu appelsínugulu — parið sem helst
   aðgreinanlegt í algengustu litblindu (rauð-græn). Liturinn er því viðbót
   ofan á lögunina, ekki í stað hennar.

Að gera tokenin ólík í ljósstyrk myndi kosta annað hvort: ljósara núll-merki
(fellur undir 4,5:1 gegn bakgrunni) eða dekkri súlur (minni andstæða við
dökkan texta í skýringu). Hvorugt vinnur neitt sem lögunin gerir ekki þegar.

`test_nulldagar_greinast_thott_litirnir_seu_eins` falsar þemað svo núll-merkið
fái **nákvæmlega** lit súlnanna, og krefst þess að dagarnir greinist samt: merkið
er önnur lögun, það er ófyllt, engin súla er á núll-degi og skýringin nefnir
það. Prófið féll þegar merkinu var breytt í fylltan ferning.

---

## 4. Myndritið: lograkvarði og núll-dagar

Úrtakið hefur 334 atburði á 61 degi; stærsti dagurinn (10. nóv.) hefur 187 og
43 dagar hafa engan. Á línulegum kvarða yrðu dagar með 1–3 atburði ósýnilegir,
svo y-ásinn er á **lograkvarða** eins og á gömlu síðunni — og ásinn segir það
með orðum: *„Atburðir á dag (lograkvarði)“*.

Lograkvarðinn hefur tvær afleiðingar sem eru leystar, ekki faldar:

* **Súla fyrir 1 atburð.** Ef ásinn byrjaði í 1 hefði hún hæðina núll. Ásinn
  byrjar því í 0,5 og allar súlur rísa þaðan.
* **Núll á engan stað á lograkvarða.** Núll-dagar fá því enga súlu heldur opinn
  hring í hæð √0,5 ≈ 0,71, þar sem engin súla getur verið þann dag.

Titill, ásar og skýringar eru á íslensku; tölur með íslensku sniði
(`islenskt_snid`): heimildarlínan segir *„43 dagar án atburðar (70,5%)“*.

---

## 5. Ákvarðað úttak

Sömu gögn og sömu tokens gefa **sömu bæti**. Án þess myndi git sjá nýja mynd við
hverja keyrslu og „breytingin“ segði ekkert um gögnin — sama gildra og fingrafarið
í #47. Tvennt þarf að festa, og prófað var að hvort tveggja breytist annars:

| Uppspretta breytileika | Lausn |
|---|---|
| `<dc:date>` í lýsigögnum (keyrslutími, í míkrósekúndum) | `metadata={"Date": None}` |
| Auðkenni `clip-path` og merkja, söltuð með slembigildi | `svg.hashsalt` fast |

`test_sama_svg_tvisvar_i_rod` teiknar tvisvar og ber bætin saman.
`test_profid_greinir_oakvardad_uttak` sýnir að án festinganna **verða** tvær
teikningar ólíkar — prófið getur því brostið og er ekki grænt af tilviljun.

Samanburðurinn á vistuðu skránum er háður matplotlib-útgáfunni (hún stendur í
`<dc:title>`). Með annarri útgáfu sleppir prófið sér með skýringu í stað þess
að falla á mun sem segir ekkert um gögnin.

---

## 6. Frammistaða og letur (regla 3.4)

| Skrá | Bæti | gzip -9 |
|---|---|---|
| `web/assets/img/skjalftar-dagar-ljost.svg` | 23.387 | 3.362 |
| `web/assets/img/skjalftar-dagar-dokkt.svg` | 23.387 | 3.362 |

Vafrinn sækir **aðeins aðra** skrána (`<picture>` velur eftir þema), svo
myndritið kostar um 23 KB af 500 KB þakinu. Prófið `test_skrarnar_eru_undir_thakinu`
fellur fari skrá yfir 40.000 bæti.

`svg.fonttype = "none"` skrifar texta sem `<text>`. Með innfelldum stafaferlum
(`"path"`, sjálfgefið í matplotlib) var sama mynd **70.780 bæti** — þrefalt
stærri. Auk þess verður textinn leitanlegur og teiknaður með letri síðunnar.

**Letrið** er `--letur-texti` úr `tokens.css`. matplotlib þarf þó letur *á
vélinni* til að mæla textann við uppsetningu, og ekkert letranna í tokens fylgir
Linux. `DejaVu Sans` (fylgir matplotlib) er því sett aftast í listann til
mælingar. Það er breiðara en Arial og Segoe UI, svo texti sem rúmast í mælingunni
rúmast líka í vafranum. Afleiðing: `DejaVu Sans` stendur í `font-family` í SVG-inu
á undan almenna `sans-serif`; vafri sem hefur ekkert letranna úr tokens notar það.

---

## 7. Notkun á síðu (HTML-brot)

Brotið sýnir mynstrið sem #20 setur á síðuna. Það er **ekki** í `web/sidur/`.
Stíllinn er `web/assets/css/components/myndrit.css`; ekkert inline (regla 2).

```html
<link rel="stylesheet" href="../assets/css/components/myndrit.css">

<figure class="myndrit" aria-labelledby="skjalftar-dagar-titill">
  <picture>
    <source srcset="../assets/img/skjalftar-dagar-dokkt.svg"
            media="(prefers-color-scheme: dark)">
    <img class="myndrit__mynd"
         src="../assets/img/skjalftar-dagar-ljost.svg"
         width="640" height="360" loading="lazy" decoding="async"
         alt="Stöplarit af fjölda skjálfta á dag á Reykjanesi frá 1. nóvember
              til 31. desember 2023. Virknin er mest 3.–11. nóvember og nær
              hámarki 10. nóvember með 187 atburði. Eftir miðjan nóvember eru
              flestir dagar án atburðar, 43 af 61 degi. Allar tölur eru í
              töflunni hér fyrir neðan.">
  </picture>
  <figcaption class="myndrit__skyring" id="skjalftar-dagar-titill">
    Fjöldi yfirfarinna skjálfta (stærð 3–7) á hverjum UTC-degi. Y-ásinn er á
    lograkvarða; opinn hringur merkir dag án atburðar í úrtakinu.
    Heimild: Veðurstofa Íslands (CC BY 4.0).
  </figcaption>

  <details class="myndrit__gogn">
    <summary>Sjá tölurnar sem töflu (61 dagur)</summary>
    <div class="tafla-umgjord">
      <table>
        <caption class="skjalesari">Skjálftar á dag, 1. nóv.–31. des. 2023</caption>
        <thead>
          <tr><th scope="col">Dagur (UTC)</th><th scope="col">Atburðir</th></tr>
        </thead>
        <tbody>
          <tr><td>1. nóv. 2023</td><td>1</td></tr>
          <tr><td>2. nóv. 2023</td><td>3</td></tr>
          <tr><td>3. nóv. 2023</td><td>24</td></tr>
          <tr><td>4. nóv. 2023</td><td class="myndrit__null">0 — enginn atburður</td></tr>
          <!-- … ein lína á hvern dag, 61 alls … -->
        </tbody>
      </table>
    </div>
  </details>
</figure>
```

Af hverju svona:

* **`<picture>` + `prefers-color-scheme`** velur þema án JavaScript, eins og
  `tokens.css` gerir. `<img>` í `<picture>` er líka varaleiðin fyrir vafra sem
  þekkja ekki `<source>`.
* **`width`/`height`** eru stærð viewBox (640 × 360), svo vafrinn tekur frá plássið
  áður en myndin hleðst. CSS (`width: 100%; height: auto`) skalar hana svo.
* **`alt` á íslensku** lýsir *niðurstöðunni*, ekki forminu („stöplarit með bláum
  súlum“ segir lesanda ekkert). Hann vísar á töfluna fyrir tölurnar.
* **Taflan** er í HTML-inu sjálfu (ákvörðunin á #17). `<details>` opnast án
  JavaScript og skjálesarar lesa töfluna óháð myndinni. Núll-dagar eru merktir
  með orðum í töflunni líka.
* **`loading="lazy"`** aðeins ef myndritið er neðan við fold (regla 3.4). Sé það
  efst á síðunni á að sleppa því.

**Tölurnar í brotinu eru ekki til afritunar.** Regla 8: hver tala á síðunni
kemur úr `web/gogn/`. Hvernig taflan og `alt`-textinn verða til úr gögnunum
(útflutningur skrifar HTML-bút, eða síðan er byggð úr JSON við útflutning) er
ákvörðun fyrir #20.

---

## 8. matplotlib: útgáfa og keyrsluumhverfi

| | |
|---|---|
| Pakki | matplotlib **3.11.2** |
| Python | 3.12.3 |
| Samþykki | Björn, 27.9.2026, [#17](https://github.com/bjd5/Upplysingaverkfradi_improvements/issues/17#issuecomment-5857519732) |
| Umfang | eingöngu `src/python/utflutningur/` |
| Bakendi | `Agg` (enginn gluggi), SVG skrifað með `Figure.savefig` án `pyplot` |

SVG-skrárnar í `web/assets/img/` voru teiknaðar með þessari útgáfu, og hún
stendur í `<dc:title>` hverrar skrár.

**Uppsetning:** útgáfan er fest í
[`config/requirements-myndrit.txt`](../config/requirements-myndrit.txt)
(ákveðið 28.9.2026, #17). Skráin er í `config/` en ekki í rót því hún er
*valkvæð*: hún varðar aðeins það að teikna myndritin upp á nýtt, og allt annað í
verkefninu — prófin meðtalin — keyrir á staðalsafninu einu. Nafnið segir það.

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r config/requirements-myndrit.txt
PYTHONPATH=src/python .venv/bin/python -m utflutningur.myndrit_skjalftar
```

---

## 9. Þekktar takmarkanir

* **Smár texti á síma.** Myndin skalast niður með breidd skjásins; við 320 px
  er ástextinn um 6 px. Taflan er framsetningin sem gildir þar. Sérstök
  símaútgáfa (`<source media="(max-width: …)">`) væri möguleg viðbót fyrir #20.
* **Engin handvirk þemaskipti.** `<picture>` fylgir stillingu stýrikerfisins,
  eins og `tokens.css`. Bætist við hnappur til að skipta um þema þarf myndin
  að fylgja honum líka.
* **`-apple-system`** í `--letur-texti` lendir innan gæsalappa í SVG-inu og
  virkar þar ekki sem kerfisleturslykilorð; vafrinn fer þá í næsta letur í
  listanum. Það hefur engin áhrif á læsileika.
