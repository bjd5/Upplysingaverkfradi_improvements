# Verklok — gátlisti reglu 9 fyrir verkefnið í heild

Mælt 2.10.2026 á `claude/bold-gates-66qscg`. `✅` stenst · `⚠️` stenst með
frávikum · `❌` stenst ekki. Aðgengi er í [`adgengi.md`](adgengi.md), stærð í
[`frammistada.md`](frammistada.md), tölurnar í [`samanburdur.md`](samanburdur.md).

| # | Regla | Staða | Sönnun |
|---|---|:-:|---|
| 1 | Skrár á réttum stað | ⚠️ | Rótin geymir aðeins skjölun, stillingar og `.github/`. Engin `.gitkeep`. Frávik 1–3 hér að neðan. |
| 2 | HTML/CSS/JS aðskilin | ✅ | Engin `<style>`, `style=`, inline `<script>` né `on…=` í `web/`; öll `<script>` með `defer`. |
| 3 | Sími (320 px) og borðtölva | ✅ | 12 síður × ljóst/dökkt × 320 og 1280 px í Chromium: `scrollWidth` = breidd gluggans alls staðar. |
| 4 | Lyklaborð og `alt` | ✅ | „Fara beint í efni“ fyrst á öllum síðum, fókusumgjörð og snertifletir ≥ 44 px mæld; engar `<img>` á síðunum. Firefox, Safari og skjálesarar óprófaðir. |
| 5 | Engin villa í console | ✅ | Sömu 12 × 2 × 2 keyrslur: engin villa og engin viðvörun. |
| 6 | Engin leyndarmál | ✅ | Hvorki í trénu né í öllum 293 commitum: enginn `.env`, lykill, token né einkalykill. Eina fundið er gervi-JWT í `tests/test_uppruni_flokkun.py`. `tests/test_vefur_birting.py` gætir `web/`. |
| 7 | Efni á íslensku, kóðaheiti á ensku | ❌ | Efni á íslensku ✅; SQL-töflur á ensku ✅; **Python-föll og breytur eru víða á íslensku** — frávik 4. |
| 8 | Commit með lýsandi skilaboðum | ✅ | Öll 158 commit utan samruna eru á forminu `svið: hvað var gert`. |

## Frávik

1. **`.github/` í rót.** GitHub Actions les workflow-skrár aðeins þaðan. Mappan er
   ekki í möppuskipan CLAUDE.md og bíður þess að hún sé skráð þar.
2. **Skrár yfir ~300 línur:** `adferdafraedi.html` 378, `skjalftavaktin.html` 362
   (61 raða gagnatafla sem verður að vera í HTML-inu), `phoebe-tolfraedi.html` 330
   (gagnatöflur), `test_hagstofan_hledsla.py` 361, `vefleit.py` 302.
3. **Skráaheiti með hástöfum:** `README.md` (venja) og tímastimplar frystu
   hrágagnanna (`…T120851Z.json`), sem provenance vísar í og eru því ekki endurnefnd.
4. **Íslensk kóðaheiti.** Af 529 Python-föllum bera a.m.k. 115 íslensk orð
   (`lesa_skjalfta`, `kassi_eftir_fjarlaegd`). Regla 1.2 vill ensk kóðaheiti.
   Endurnöfnun snertir prófin og alla útflutningsleiðina. Ákvörðun er óteknin:
   breyta reglunni eða endurnefna.

## Opið

- **Pages er ekki kveikt.** Eigandi þarf að velja *Settings → Pages → Source:
  GitHub Actions*; birtingin er óprófuð á opinberu léni.
- **Biðsíður:** `phoebe-tmdb` (lykil vantar, #75), `friends-gagnasagan`,
  `uppahalds-video` og `phoebe-tribute`.
- **Veðurstöðvakortið** (SVG) vantar: matplotlib er ekki uppsett og útflutningurinn
  hefur engin hnit.
- **Endurbætur Björns** í #54 (viðauki, vinnudagbók, hetjusvæði, orðalag) eru ekki unnar.

## Endurtekning

`python3 -m unittest discover -s tests` keyrir allt sem má keyra án vafra.
Vaframælingarnar (liðir 3–5) nota Playwright á `python3 -m http.server --directory web`;
skrefin eru í [`adgengi.md`](adgengi.md) kafla 4.
