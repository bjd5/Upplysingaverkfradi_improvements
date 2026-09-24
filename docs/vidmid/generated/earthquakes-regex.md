### Regex 1: UTC-tímastimpill verður daglykill

```python
(?P<utc_day>[0-9]{4}-[0-9]{2}-[0-9]{2})T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z
```

`fullmatch` krefst alls textans. Nafngreindi hópurinn `utc_day` gefur UTC-daginn; sekúndubrot mega hafa mismargar tölur. `datetime` hafnar síðan ógildum dögum og klukkum. Daglykillinn er notaður í daglegri talningu og getur síðar tengt dagsett gögn.

| Fyrir: raunverulegt `time` | Eftir: `utc_day` |
|---|---|
| `2023-11-01T00:56:41.645Z` | `2023-11-01` |
| `2023-11-02T20:35:42.458Z` | `2023-11-02` |

### Regex 2: SIL-auðkenni verður samsettur atburðalykill

```python
(?P<source_system>SIL)(?P<event_number>[1-9][0-9]*)
```

`fullmatch` skilur kerfisheitið `SIL` frá atburðanúmerinu. Lykillinn `source_system:event_number` sannreynir einkvæmni og er tiltækur fyrir framtíðartengingar. Númerið er texti, ekki dagsetning; upprunalega auðkennið helst í `original_id`. Rangt kerfisheiti, aukatexti og tvíteknir lyklar valda skýrri villu.

| Fyrir: raunverulegt `event_id` | Eftir: kerfi | Eftir: númer | Eftir: lykill |
|---|---|---|---|
| `SIL1235710` | `SIL` | `1235710` | `SIL:1235710` |
| `SIL1237655` | `SIL` | `1237655` | `SIL:1237655` |
