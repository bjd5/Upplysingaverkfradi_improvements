-- hagstofan-hlutfoll.sql
-- Spurning: Hvert er hlutfall brautskráðra, þeirra sem enn eru í námi og
--           þeirra sem hættu, eftir námssviði og kyni — árgangur 2017, n+3?
-- Síða: web/sidur/hagstofan.html (töflurnar tvær: ósundurliðuð og eftir kyni)
-- Breytur:
--   ?1 töfluauðkenni Hagstofunnar (dataset_id, t.d. SKO04208b)
--
-- Les sýnina hagstofan_labelled_observations (003), sem ber íslensku heitin
-- við hlið kóðanna. Gildin eru prósentur eins og Hagstofan skilar þeim,
-- ÓAFRÚNNUÐ; gamla síðan birti einn aukastaf og birtingin námundar.
-- Áður var þessi fyrirspurn aðeins til sem strengur í prófi
-- (tests/test_hagstofan_vidmid.py) og námundaði í SQL.

SELECT field_code, field_label,
       sex_code, sex_label,
       student_status_code, student_status_label,
       value AS percentage
FROM hagstofan_labelled_observations
WHERE dataset_id = ?
ORDER BY field_code, sex_code, student_status_code;
