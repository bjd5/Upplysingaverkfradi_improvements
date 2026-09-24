**Heimild:** Veðurstofa Íslands, [Quakes API](https://api.vedur.is/quakes/openapi.json); opið, án auðkenningar eða API-lykils. Gögnin eru merkt [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

**Endapunktur:** `https://api.vedur.is/quakes/events`. **Haus:** `x-vi-api-version: 2026-08-06`.

Nákvæmt GET-kall með öllum síum:

```text
https://api.vedur.is/quakes/events?start_time=2023-11-01T00%3A00%3A00%2B00%3A00&end_time=2024-01-01T00%3A00%3A00%2B00%3A00&depth_min=0&depth_max=50&size_min=3&size_max=7&polygon=POLYGON%28%28-23+64.1%2C-23+63.7%2C-21.5+63.7%2C-21.5+64.1%2C-23+64.1%29%29&type=earthquake&evaluation_mode=manual&format=json&system=sil
```

**Sótt (UTC):** 2026-09-10T11:46:23Z. Sóknartími er annar en **athugunartímabilið:** 2023-11-01 kl. 00:00 UTC til 2024-01-01 kl. 00:00 UTC; upphaf meðtalið, endir undanskilinn. Lengdargráða −23 til −21,5; breiddargráða 63,7 til 64,1. Stærð 3–7, dýpt 0–50 km; aðeins `earthquake`, `manual`, `sil`.

**Notaðir reitir:** `geometry.coordinates` (lengd, breidd); `properties.time`, `event_id`, `type`, `depth`, `magnitude`, `magnitude_type` og `evaluation_mode`. JSON er lesið með JSON-þáttara; regex vinnur aðeins á tímastimpli og auðkenni. Umbreytingar: sannprófun, tveir lyklar, röðun og dagleg talning; hráa svarið helst óbreytt.

**SHA-256:** `a535359ea84346426d5ce7fccf4ce8e5158b712e4fc66378dae4b291f771fa9a`.
