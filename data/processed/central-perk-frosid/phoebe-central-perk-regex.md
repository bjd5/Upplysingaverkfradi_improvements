#### `SCENE_START_RE`

```python
^\s*(?:\[[^]]*\b(?:scene|cut|later|time lapse|back at|meanwhile|opening credits|closing credits)\b|\([^)]*\b(?:scene|cut to|cut back|later|time lapse|back at|meanwhile)\b)
```

**Grípur:** Byrjun senu. Blokk sem hefst á hornklofa eða sviga með orði á borð við `Scene`, `Cut to`, `Later` eða `Time lapse` hækkar senuteljarann og ræður hvort næstu tilsvör eru í Central Perk (ef fyrirsögnin nefnir staðinn).

**Sleppur:** Senuskipti sem umritari skrifaði án hornklofa eða sviga, og senur sem gerast í Central Perk án þess að fyrirsögnin nefni staðinn.

#### `SPEAKER_RE`

```python
^\s*([^:\n]{1,100}):\s*(.*)$
```

**Grípur:** Tilsvar á forminu `Nafn: texti`. Fyrri hópurinn er ræðumaður (færður á kanónískt nafn með `NAME_ALIASES`), sá seinni línan sjálf.

**Sleppur:** Tilsvör þar sem umritari sleppti tvípunktinum, og sviðslýsingar sem innihalda tvípunkt innan fyrstu 100 stafa lenda sem „ræðumaður“ sem engin aðalpersóna á og eru þá ekki taldar.

#### `SINGING_CUE_RE`

```python
[\[(][^)\]]*\b(?:singing|sings|sung|starts? to (?:play and )?sing)\b[^)\]]*[\])]
```

**Grípur:** Skýr söngmerking í svigum eða hornklofum í tilsvari Phoebe: `(singing)`, `(sings)`, `(sung)`, `(starts to sing)`. Senan telst söngsena aðeins ef hún er í Central Perk.

**Sleppur:** Söngur sem umritari merkti ekki, eða merkti með orðum sem segðin leitar ekki að (`(humming)`, `(plays guitar)`). Misheppnaða byrjunin í `0107`, þar sem Phoebe slær einn hljóm áður en rafmagnið fer, fellur því utan.

#### `PHOEBE_PERFORMANCE_RE`

```python
(?:\bphoebe(?:'s|’s)?\b.{0,80}\b(?:is singing|performing|finishing up a song)\b|\bboth\b.{0,40}\bphoebe\b.{0,80}\bsinging\b)
```

**Grípur:** Sviðslýsing sem segir að Phoebe sé að koma fram: „Phoebe is singing“, „Phoebe's performing“, „Phoebe … finishing up a song“, „both … Phoebe … singing“. Grípur söng sem er lýst í sviðsfyrirsögn eða sjálfstæðri sviðslýsingu frekar en inni í tilsvari.

**Sleppur:** Lýsingar með annarri orðanotkun (`Phoebe plays`, `Phoebe strums`) og tilvik þar sem nafnið og sögnin standa lengra en 80 stöfum hvort frá öðru.

#### `STAGE_DIRECTION_RE`

```python
\([^)]*\)|\[[^]]*\]|\{[^}]*\}
```

**Grípur:** Sviðsleiðbeiningar innan tilsvars: `(laughs)`, `[to Joey]`, `{pause}`. Þær eru klipptar burt áður en orð eru talin.

**Sleppur:** Óparaður svigi (t.d. `(laughs` án lokunar) sleppur í gegn og orðin í honum teljast töluð.

#### `WORD_RE`

```python
[A-Za-z]+(?:['’][A-Za-z]+)?
```

**Grípur:** Eitt talað orð: enskir bókstafir, með einni úrfellingu leyfðri (`don't`). Fjöldi samsvarana er orðafjöldi tilsvarsins.

**Sleppur:** Tölur (`2`) og bandstrikuð orð telja sem tvö (`well-known` → `well`, `known`). Það hefur sömu áhrif á allar persónur og skekkir ekki hlutföll.
