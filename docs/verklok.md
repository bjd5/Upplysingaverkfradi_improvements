# Verklok — gátlisti reglu 9 fyrir verkefnið í heild

Mælt 2.10.2026 á `claude/bold-gates-66qscg` eftir að `main` var sameinaður inn. `✅` stenst · `⚠️` stenst með
frávikum · `❌` stenst ekki. Aðgengi er í [`adgengi.md`](adgengi.md), stærð í
[`frammistada.md`](frammistada.md), tölurnar í [`samanburdur.md`](samanburdur.md).

| # | Regla | Staða | Sönnun |
|---|---|:-:|---|
| 1 | Skrár á réttum stað | ⚠️ | Rótin geymir aðeins skjölun og stillingar; `.github/workflows/` er í möppuskipaninni. Engin `.gitkeep`. Frávik 1–2 hér að neðan. |
| 2 | HTML/CSS/JS aðskilin | ✅ | Engin `<style>`, `style=`, inline `<script>` né `on…=` í `web/`; öll `<script>` með `defer`. |
| 3 | Sími (320 px) og borðtölva | ✅ | 12 síður × ljóst/dökkt × 320 og 1280 px í Chromium: `scrollWidth` = breidd gluggans alls staðar. |
| 4 | Lyklaborð og `alt` | ✅ | „Fara beint í efni“ fyrst á öllum síðum, fókusumgjörð og snertifletir ≥ 44 px mæld; engar `<img>` á síðunum. Firefox, Safari og skjálesarar óprófaðir. |
| 5 | Engin villa í console | ✅ | Sömu 12 × 2 × 2 keyrslur: engin villa og engin viðvörun. |
| 6 | Engin leyndarmál | ✅ | Hvorki í trénu né í öllum 302 commitum: enginn `.env`, lykill, token né einkalykill. Eina fundið er gervi-JWT í `tests/test_uppruni_flokkun.py`. `tests/test_vefur_birting.py` gætir `web/`. |
| 7 | Efni á íslensku; kóðaheiti skv. reglu 1.2 | ✅ | Efni á íslensku; SQL-töflur og dálkar á ensku; íslensk heiti í Python eru leyfð án séríslenskra stafa (regla 1.2). |
| 8 | Commit með lýsandi skilaboðum | ✅ | Öll 211 commit utan samruna eru á forminu `svið: hvað var gert`. |

## Frávik

1. **Skrár yfir ~300 línur:** `vedurstodvar.html` 424, `mbl-regex.html` 381,
   `adferdafraedi.html` 378, `skjalftavaktin.html` 362, `hagstofan.html` 354,
   `phoebe-tolfraedi.html` 330 (síður með gagnatöflum sem verða að vera í
   HTML-inu), `test_vefur.py` 363, `test_hagstofan_hledsla.py` 361 og
   `vidmid_reglur.py` 309.
2. **Skráaheiti með hástöfum:** `README.md` (venja) og tímastimplar frystu
   hrágagnanna (`…T120851Z.json`), sem provenance vísar í og eru því ekki endurnefnd.

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
