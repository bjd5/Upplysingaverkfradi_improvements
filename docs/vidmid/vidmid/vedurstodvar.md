# Viðmið — Veðurstöðvar Veðurstofunnar

Afleidd skrá. Uppfært 2026-09-24T11:39:24Z af `src/python/vidmid/tolur.py`; **ekki handbreytt** (regla 10).

41 efnislegar tölur úr 1 síðum gamla verkefnisins.

## `lotur/vefthjonustur/vedurstofan.html`

Byggingarlota `9cf667d`. 41 efnislegar tölur.

| Tala | Eining | Tegund | Hvar | Samhengi |
|---|---|---|---|---|
| `1` | — | heiltala | Veðurstofan (æfing 1B) | Þetta er æfing 1B úr hluta 1: vefþjónusta Veðurstofunnar. Verkefnið er einfalt í orðum: forrit á að sýna veðr… |
| `6` | — | heiltala | Veðurstofan (æfing 1B) | Þetta er æfing 1B úr hluta 1: vefþjónusta Veðurstofunnar. Verkefnið er einfalt í orðum: forrit á að sýna veðr… |
| `64,1386922` | — | desimal | Gögnin: hvaðan þau koma og hvað þau lýsa | Hnit VR-II (64,1386922, -21,9556406) voru flett upp í Nominatim hjá OpenStreetMap og eru fest sem fastar í sk… |
| `-21,9556406` | — | desimal | Gögnin: hvaðan þau koma og hvað þau lýsa | Hnit VR-II (64,1386922, -21,9556406) voru flett upp í Nominatim hjá OpenStreetMap og eru fest sem fastar í sk… |
| `1` | — | heiltala | Beiðnin: síurnar eru sendar með | station_id=<auðkenni> — ein tiltekin stöð. Þetta er beiðnin sem forritið sjálft sendir þegar búið er að velja… |
| `2` | — | heiltala | Beiðnin: síurnar eru sendar með | station_id=<auðkenni> — ein tiltekin stöð. Þetta er beiðnin sem forritið sjálft sendir þegar búið er að velja… |
| `778` | — | heiltala | Beiðnirnar eru margar en ekki ein, því … · engin sía · allar stöðvar … | 778 |
| `343` | — | heiltala | Beiðnirnar eru margar en ekki ein, því … · active=true · aðeins stöðv… | 343 |
| `5` | km | heiltala | Beiðnirnar eru margar en ekki ein, því … · polygon · Hvað beiðnin bið… | aðeins stöðvar innan 5 km kassans um VR-II |
| `21` | — | heiltala | Beiðnirnar eru margar en ekki ein, því … · polygon · Stöðvar í svari | 21 |
| `9` | — | heiltala | Beiðnirnar eru margar en ekki ein, því … · polygon + active=true · hv… | 9 |
| `1469` | — | heiltala | Beiðnirnar eru margar en ekki ein, því … · Færibreytur í beiðninni | station_id=1469 |
| `1` | — | heiltala | Beiðnirnar eru margar en ekki ein, því … · station_id=1469 · stöðin s… | 1 |
| `200` | — | heiltala | Beiðnin: síurnar eru sendar með | Mikilvægt HTTP 200 þýðir ekki að sían hafi virkað |
| `200` | — | heiltala | Beiðnin: síurnar eru sendar með | Þjónustan hunsar færibreytur sem hún þekkir ekki og svarar samt með stöðukóða 200. Til dæmis skilar ?limit=3 … |
| `3` | — | heiltala | Beiðnin: síurnar eru sendar með | Þjónustan hunsar færibreytur sem hún þekkir ekki og svarar samt með stöðukóða 200. Til dæmis skilar ?limit=3 … |
| `1` | — | heiltala | Hvernig kóðinn vinnur gögnin | 1. Afmarka svæðið. Kassi með 5 km radíus utan um VR-II er skrifaður á WKT-sniði og sendur sem polygon : |
| `5` | km | heiltala | Hvernig kóðinn vinnur gögnin | 1. Afmarka svæðið. Kassi með 5 km radíus utan um VR-II er skrifaður á WKT-sniði og sendur sem polygon : |
| `111` | km | heiltala | Hvernig kóðinn vinnur gögnin | Breiddargráða er um 111 km alls staðar, en lengdargráða styttist í \(111\cos\varphi\) — um 48 km á breiddargr… |
| `111` | — | heiltala | Hvernig kóðinn vinnur gögnin | Breiddargráða er um 111 km alls staðar, en lengdargráða styttist í \(111\cos\varphi\) — um 48 km á breiddargr… |
| `48` | km | heiltala | Hvernig kóðinn vinnur gögnin | Breiddargráða er um 111 km alls staðar, en lengdargráða styttist í \(111\cos\varphi\) — um 48 km á breiddargr… |
| `2` | — | heiltala | Hvernig kóðinn vinnur gögnin | 2. Reikna fjarlægð. Haversine-formúlan gefur stórbaugsfjarlægð milli tveggja hnita: |
| `3` | — | heiltala | Hvernig kóðinn vinnur gögnin | 3. Raða og meta. Stöðvarnar úr polygon -beiðninni fá fjarlægð, er raðað eftir henni og eru síðan metnar út fr… |
| `4` | — | heiltala | Hvernig kóðinn vinnur gögnin | 4. Skrifa niðurstöðuna. Skriftan skrifar töfluna, myndina og svörin hér á síðunni sem tilbúnar skrár. Engin t… |
| `1469` | — | heiltala | Niðurstaða | Forritið á að lesa Reykjavík Hljómskálagarður (1469) , 639 m frá VR-II: hún er næsta stöð við húsið og ending… |
| `639` | m | heiltala | Niðurstaða | Forritið á að lesa Reykjavík Hljómskálagarður (1469) , 639 m frá VR-II: hún er næsta stöð við húsið og ending… |
| `1469` | — | heiltala | Svör við spurningum æfingarinnar | Hver er næsta veðurstöð við VR-II og er hún enn í notkun? Reykjavík Hljómskálagarður (1469), 639 m frá húsinu… |
| `639` | m | heiltala | Svör við spurningum æfingarinnar | Hver er næsta veðurstöð við VR-II og er hún enn í notkun? Reykjavík Hljómskálagarður (1469), 639 m frá húsinu… |
| `1469` | — | heiltala | Svör við spurningum æfingarinnar | Hver er næsta virka stöðin og hversu miklu munar? Reykjavík Hljómskálagarður (1469), 639 m frá VR-II. Næsta a… |
| `639` | m | heiltala | Svör við spurningum æfingarinnar | Hver er næsta virka stöðin og hversu miklu munar? Reykjavík Hljómskálagarður (1469), 639 m frá VR-II. Næsta a… |
| `2` | — | heiltala | Svör við spurningum æfingarinnar | Hver er næsta virka stöðin og hversu miklu munar? Reykjavík Hljómskálagarður (1469), 639 m frá VR-II. Næsta a… |
| `689` | m | heiltala | Svör við spurningum æfingarinnar | Hver er næsta virka stöðin og hversu miklu munar? Reykjavík Hljómskálagarður (1469), 639 m frá VR-II. Næsta a… |
| `50` | m | heiltala | Svör við spurningum æfingarinnar | Hver er næsta virka stöðin og hversu miklu munar? Reykjavík Hljómskálagarður (1469), 639 m frá VR-II. Næsta a… |
| `343` | — | heiltala | Svör við spurningum æfingarinnar | Hversu margar af stöðvunum eru virkar? 343 af 778, eða um 44 %. Listinn er því ekki listi yfir stöðvar í reks… |
| `778` | — | heiltala | Svör við spurningum æfingarinnar | Hversu margar af stöðvunum eru virkar? 343 af 778, eða um 44 %. Listinn er því ekki listi yfir stöðvar í reks… |
| `44 %` | % | hlutfall | Svör við spurningum æfingarinnar | Hversu margar af stöðvunum eru virkar? 343 af 778, eða um 44 %. Listinn er því ekki listi yfir stöðvar í reks… |
| `50` | — | heiltala | Svör við spurningum æfingarinnar | Dygði sama stöð til að bera saman við veður fyrir 50 árum? Nei. Reykjavík Hljómskálagarður (1469) hóf mælinga… |
| `1469` | — | heiltala | Svör við spurningum æfingarinnar | Dygði sama stöð til að bera saman við veður fyrir 50 árum? Nei. Reykjavík Hljómskálagarður (1469) hóf mælinga… |
| `1` | — | heiltala | Svör við spurningum æfingarinnar | Dygði sama stöð til að bera saman við veður fyrir 50 árum? Nei. Reykjavík Hljómskálagarður (1469) hóf mælinga… |
| `2547` | m | heiltala | Svör við spurningum æfingarinnar | Dygði sama stöð til að bera saman við veður fyrir 50 árum? Nei. Reykjavík Hljómskálagarður (1469) hóf mælinga… |
| `5` | km | heiltala | Fyrirvarar | Kassi, ekki hringur. polygon afmarkar ferning, svo horn hans ná ríflega 5 km frá VR-II. Það breytir fjöldanum… |
