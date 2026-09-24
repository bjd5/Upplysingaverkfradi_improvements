## Gögn og lýsigögn

Gögn sótt: **2026-09-10T09:02:26+00:00** (UTC). Heimild: Nemendaskrá og prófaskrá Hagstofu Íslands.

Tafla: **Brautskráningarhlutfall og árgangsbrotthvarf í þriggja ára bakkalárnámi eftir námssviði 2014-2023**.

GET á sama endapunkt skilaði eftirfarandi breytum, leyfðum kóðum og heitum. Síðasti dálkurinn sýnir valið sem fór í POST-fyrirspurnina.

| Breyta | Leyfðir kóðar og heiti úr lýsigögnum | Valdir kóðar |
|---|---|---|
| Innritunarár | `2014` = 2014; `2017` = 2017 | `2017` |
| Tími | `n+3` = Sex árum eftir innritun | `n+3` |
| Nemendur | `1` = Nýnemar alls; `2` = Brautskráðir með bakkalárgráðu af sama sviði; `3` = Brautskráðir með bakkalárgráðu af öðru sviði; `4` = Brautskráðir úr öðru háskólanámi; `5` = Brautskráðir alls; `6` = Brottfallnir; `7` = Enn í námi | `5`, `6`, `7` |
| Fjöldi/Hlutfall | `0` = Fjöldi; `1` = Hlutfall % | `1` |
| Námssvið | `Alls` = Alls; `01` = Menntun; `02` = Hugvisindi og listir; `03` = Félagsvísindi, fjölmiðlun og upplýsingafræði; `04` = Viðskipti, stjórnun og lögfræði; `05` = Raunvísindi, stærðfræði og tölfræði; `06` = Upplýsinga- og samskiptatækni; `07` = Verkfræði, framleiðsla og mannvirkjagerð; `08` = Landbúnaður, skógrækt, fiskveiðar og dýralækningar; `09` = Heilbrigði og velferð; `10` = Þjónusta | `Alls`, `05`, `06`, `07` |
| Kyn | `Alls` = Alls; `1` = Karlar; `2` = Konur | `Alls`, `1`, `2` |


`Innritunarár` er merkt `time: true`. `values` geymir kóðana en `valueTexts` skýringar þeirra. Verkfræðisviðið hefur kóðann `07`.

## POST-fyrirspurnin

Beiðnin notar `Content-Type: application/json; charset=utf-8` og `filter: item` fyrir hverja breytu. Svarið inniheldur aðeins valda sneið: fjögur svið, þrjá stöðuflokka og þrjá kynflokka (Alls, Karlar, Konur), samtals 36 prósentugildi.

```json
{
  "query": [
    {
      "code": "Innritunarár",
      "selection": {
        "filter": "item",
        "values": [
          "2017"
        ]
      }
    },
    {
      "code": "Tími",
      "selection": {
        "filter": "item",
        "values": [
          "n+3"
        ]
      }
    },
    {
      "code": "Nemendur",
      "selection": {
        "filter": "item",
        "values": [
          "5",
          "6",
          "7"
        ]
      }
    },
    {
      "code": "Fjöldi/Hlutfall",
      "selection": {
        "filter": "item",
        "values": [
          "1"
        ]
      }
    },
    {
      "code": "Námssvið",
      "selection": {
        "filter": "item",
        "values": [
          "Alls",
          "05",
          "06",
          "07"
        ]
      }
    },
    {
      "code": "Kyn",
      "selection": {
        "filter": "item",
        "values": [
          "Alls",
          "1",
          "2"
        ]
      }
    }
  ],
  "response": {
    "format": "json-stat2"
  }
}
```

## Hvernig á að lesa svarið?

`value` er flatt fylki. Kóðinn les röð vídda úr `id`, stærðir úr `size` og röðun gilda úr `dimension[breyta].category.index`. Síðasta víddin breytist hraðast. Röð lykla í `label` er ekki notuð til að para ár, kyn og tölur.

::: {.callout-important}
`Tími = n+3` merkir **sex árum eftir innritun**, samkvæmt `valueTexts`. Niðurstöðurnar mæla því stöðuna sex árum eftir innritun 2017, ekki lok náms á þremur árum. `Fjöldi/Hlutfall = 1` merkir prósentur, ekki fjölda nemenda.
:::

Svarið gefur `updated = 9999-12-31T23:59:59Z`. Þessi reitur er varðveittur sem lýsigagn; hann er ekki sóknartími okkar. Gildið `9999-12-31T23:59:59Z` í vistaða svarinu er ekki nothæf dagsetning síðustu uppfærslu. Við styðjum tímasetningu gagnasóknar við eigin UTC-tímastimpil.

`extension.px.decimals` í vistaða svarinu er 0 þótt `value` innihaldi aukastafi. Við varðveitum raunveruleg tölugildi og birtum einn aukastaf.

## Samanburður námssviða

Hlutfall (%) sex árum eftir innritun 2017, kyn alls.

| Námssvið | Brautskráðir alls | Brottfallnir | Enn í námi |
|---|---:|---:|---:|
| Alls | 73,5 | 19,6 | 6,9 |
| Raunvísindi, stærðfræði og tölfræði | 71,0 | 22,5 | 6,5 |
| Upplýsinga- og samskiptatækni | 68,6 | 23,4 | 8,0 |
| Verkfræði, framleiðsla og mannvirkjagerð | 84,3 | 11,9 | 3,8 |


Brautskráningarhlutfall verkfræðisviðsins er **84,3%**, samanborið við **73,5%** alls: munurinn (verkfræði − alls) er **10,8 prósentustig**. Þetta er lýsandi samanburður á innritunarárgangi, ekki mæling á áhrifum námsvals.

## Svör við æfingaspurningunum

### Hvers vegna leggja dálkarnir saman í 100?

Brautskráðir alls, brottfallnir og enn í námi eru þrír stöðuflokkar sama innritunarhóps við sama viðmiðunartíma. Hver nemandi tilheyrir einum flokki. Heildin er því 100%, en námundun getur gefið 99,9% eða 100,1%. `Brautskráðir alls` tekur líka til þeirra sem brautskráðust úr öðru námi; það jafngildir ekki því að allir hafi lokið bakkalárgráðu á upphaflega sviðinu.

### Hvers vegna duga tvö innritunarár ekki til að meta þróun?

Lýsigögnin bjóða aðeins 2014 og 2017. Tveir punktar sýna mun milli tveggja árganga en aðgreina ekki varanlega þróun frá tilviljun, samsetningu hópa eða breytingum á námsumhverfi. Þessi fyrirspurn velur aðeins 2017; hún reiknar ekki breytingu milli árganga.

### Breytist myndin þegar skipt er eftir kyni?

Sama POST-fyrirspurn sækir Karla (`1`) og Konur (`2`) til viðbótar við Alls. Hér er öll staðan, ekki aðeins brautskráningin; tölurnar eru prósentur innan hvers kyns og sviðs.

| Námssvið | Kyn | Brautskráðir alls | Brottfallnir | Enn í námi |
|---|---|---:|---:|---:|
| Alls | Karlar | 70,3 | 23,0 | 6,6 |
| Alls | Konur | 75,9 | 17,0 | 7,1 |
| Raunvísindi, stærðfræði og tölfræði | Karlar | 68,9 | 23,0 | 8,2 |
| Raunvísindi, stærðfræði og tölfræði | Konur | 72,7 | 22,1 | 5,2 |
| Upplýsinga- og samskiptatækni | Karlar | 67,6 | 25,4 | 7,0 |
| Upplýsinga- og samskiptatækni | Konur | 71,7 | 17,4 | 10,9 |
| Verkfræði, framleiðsla og mannvirkjagerð | Karlar | 84,2 | 12,6 | 3,3 |
| Verkfræði, framleiðsla og mannvirkjagerð | Konur | 84,5 | 10,9 | 4,7 |


Í verkfræði er brautskráningarhlutfall karla **84,2%** og kvenna **84,5%**. Munurinn (konur − karlar) er **0,3 prósentustig**. Fyrir öll svið saman er sami munur **5,6 prósentustig**. Samanburðurinn breytist því eftir því hvort svið er tekið með. Án fjölda nemenda metum við hvorki óvissu né tölfræðilega marktækni; Alls er heldur ekki einfalt meðaltal kynjahlutfallanna.
