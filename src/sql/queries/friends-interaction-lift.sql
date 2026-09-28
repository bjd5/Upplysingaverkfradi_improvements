-- friends-interaction-lift.sql
-- Spurning: Hver vinanna talar oftar við Phoebe en málgleði hans eða hennar
--           ein skýrir — og í hvaða röð?
-- Síða: web/sidur/phoebe-tolfraedi.html (TENGSL)
-- Breytur: engar
--
-- interaction_lift er reiknað í fjórum læsilegum CTE-þrepum í sýninni
-- phoebe_interaction_lift (006): turns → turn_shares → line_shares → lift.
-- Hér er sýnin ENDURNÝTT en ekki endurskrifuð — sama útreikningur á tveimur
-- stöðum fer fyrr eða síðar á skjön. Fyrirspurnin bætir aðeins við röðinni.
-- Notuð líka af vinnsla/friends_hledsla.py til að staðfesta lift við skrána.
--
-- Lift > 1: persónan á stærri hlut í ræðuskiptum við Phoebe en í línum
-- vinanna fimm alls. Hrá talning sýndi alltaf Rachel efsta, því hún talar mest.
--
-- UNDANTEKNING FRÁ NÁMUNDUNARVENJUNNI: sýnin námundar (ROUND … 2 og 3 í 006,
-- sem er ekki breytt — regla 5). Ekkert óafrúnnaðra gilda liggur á helmingi,
-- svo SQLite og Python gefa sömu tölu; prófið ber hvert gildi nákvæmlega við
-- phoebe-top-talkers.csv, sem Python námundaði.

SELECT character_name,
       adjacent_turns,
       total_lines,
       adjacency_share_pct,
       expected_share_pct,
       interaction_lift,
       RANK() OVER (ORDER BY interaction_lift DESC) AS lift_rank
FROM phoebe_interaction_lift
ORDER BY lift_rank, character_name;
