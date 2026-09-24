"""Ósamræmi MILLI síðna í gamla verkefninu — sjálfstæð niðurstaða P0.2.

Verklýsingin krefst þess að þetta sé skráð sérstaklega. Ósamræmið er ekki
lestrarvilla: viðmiðið er samsett úr þremur Quarto-byggingum á tveimur dögum og
fjórar síður eru byggðar úr grein sem rataði aldrei á main (sjá
docs/vidmid/README.md, kafla 2). Síða úr einni lotu þarf ekki að sýna sömu tölu
og síða úr annarri.

Hvert atriði hér er sannreynt, ekki ætlað. `profun` segir hvernig — og
tests/test_tolur.py keyrir þær prófanir svo niðurstaðan rotni ekki þegjandi.
"""

from __future__ import annotations

from typing import NamedTuple


class Osamraemi(NamedTuple):
    heiti: str
    alvarleiki: str          # hatt | midlungs | skrad
    stadir: tuple[tuple[str, str], ...]   # (síða, það sem hún segir)
    nidurstada: str
    profun: str
    afleiding: str           # hvað þetta þýðir fyrir endurbygginguna


OSAMRAEMI: tuple[Osamraemi, ...] = (
    Osamraemi(
        heiti="Fjöldi skráa sem geyma tvöfalda þætti",
        alvarleiki="hatt",
        stadir=(
            ("friends/phoebe-statistics.html",
             "„níu skráanna geyma tvöfalda þætti“"),
            ("friends/index.html",
             "„223 með stöku þáttanúmeri og sex sem ná yfir tvöfalda þætti "
             "eða sérefni“"),
            ("phoebe-central-perk.html",
             "„Fjórar skrár sameina tvöfalda þætti“"),
        ),
        nidurstada=(
            "Þrjár tölur — 9, 6 og 4 — um sama hlutinn. Aðeins 9 stemmir: "
            "`_meta.json` telur níu skrár í `double_episode_files`, og "
            "227 + 9 = 236. `friends/index.html` telur aðeins skrárnar "
            "sem hafa bandstrik í "
            "nafni (0212-0213, 0615-0616, 0923-0924, 1017-1018) auk tveggja "
            "sérefnisskráa; `phoebe-central-perk.html` aðeins bandstriksskrárnar "
            "fjórar. Fimm skrár (0423, 0523, 0624, 0723, 0823) geyma tvöfalda "
            "þætti þótt nafnið sýni aðeins eitt þáttanúmer."
        ),
        profun=(
            "`len(conventions.double_episode_files) == 9` og "
            "`transcript_files_used + 9 == aired_episodes_covered` í "
            "`_meta.json`"
        ),
        afleiding=(
            "Reikningur `friends/index.html` gengur ekki upp: 223 stakar + 4 "
            "tvöfaldar skrár gefa 231 þátt, ekki 236. Nýja síðan á að nota 218 "
            "stakar + 9 tvöfaldar = 236 og aðeins eina orðanotkun."
        ),
    ),
    Osamraemi(
        heiti="Orðið „lína“ merkir þrennt",
        alvarleiki="hatt",
        stadir=(
            ("friends/phoebe-statistics.html",
             "61 161 er „tilsvör“ af 70 553 textablokkum"),
            ("lotur/regex/index.html",
             "„Þátta 61.161 línur úr 70.553 textablokkum“"),
            ("friends/index.html",
             "„delvinso gefur upp 236 þætti og um 69.500 línur“"),
        ),
        nidurstada=(
            "Sama tala (61 161) heitir „tilsvör“ á einni síðu og „línur“ á "
            "annarri, og á þriðju síðu er „línur“ 69.500 — tala delvinso sem "
            "telur líka sviðslýsingar, leikaraskrá og höfundatexta. "
            "`friends/index.html` skýrir sína tölu sjálf, svo það frávik "
            "er skjalfest; hin tvö orðanotin standa óskýrð hlið við hlið."
        ),
        profun=(
            "61161 finnst með `eining='línur'` á `lotur/regex/index.html` og sem "
            "„tilsvör“ á `friends/phoebe-statistics.html`; 69500 aðeins "
            "á `friends/index.html`"
        ),
        afleiding=(
            "Nýja síðan þarf eitt orð á hvert hugtak: tilsvör (61 161), "
            "textablokkir (70 553), og tala delvinso sé kölluð það sem hún er."
        ),
    ),
    Osamraemi(
        heiti="phoebe-top-talkers.json er í tveimur röðum",
        alvarleiki="midlungs",
        stadir=(
            ("docs/vidmid/vefur/friends/phoebe-stats/phoebe-top-talkers.json",
             "non_friend_characters[1]=frank, [2]=david, [16]=man, "
             "[17]=grandmother"),
            ("docs/vidmid/phoebe-stats/phoebe-top-talkers.json",
             "non_friend_characters[1]=david, [2]=frank, [16]=grandmother, "
             "[17]=man"),
        ),
        nidurstada=(
            "Gildin eru eins; röðin er ekki. `frank` og `david` eru bæði með "
            "`adjacent_turns=174`, `man` og `grandmother` bæði með 32. Röðunin í "
            "gömlu greiningunni brýtur jafntefli án fasts viðmiðs, svo tvær "
            "keyrslur á sömu gögnum skila ólíkri röð. Myndritið í byggðu "
            "síðunni sýnir því aðra röð en nýjasta úrvinnslan."
        ),
        profun=(
            "Fletjuð lyklakort skránna tveggja: 479 lyklar í báðum, 16 "
            "ólíkir, allir innan þessara fjögurra sæta"
        ),
        afleiding=(
            "P2.7 verður að raða með föstu jafnteflisviðmiði (t.d. nafni) "
            "annars sýnir nýja síðan „aðra“ niðurstöðu sem er sama niðurstaðan. "
            "P2.8 á að bera saman mengi, ekki röð, nema röðin sé bundin."
        ),
    ),
    Osamraemi(
        heiti="_meta.json er í tveimur eintökum frá tveimur keyrslum",
        alvarleiki="skrad",
        stadir=(
            ("docs/vidmid/vefur/friends/phoebe-stats/_meta.json",
             "generated_utc = 2026-09-16T14:56:00Z"),
            ("docs/vidmid/phoebe-stats/_meta.json",
             "generated_utc = 2026-09-17T09:47:09Z"),
        ),
        nidurstada=(
            "Eintökin eru eins að öðru leyti en tímastimplinum — allar tölur "
            "stemma. Viðvörunin í `README.md` (kafli 2) um að síðan gæti víkið frá "
            "`_meta.json` á því ekki við um þessar tölur."
        ),
        profun="diff á skránum gefur aðeins línuna `generated_utc`",
        afleiding=(
            "Staðfestu tölurnar í kafla 3 má nota án þess að velja milli "
            "eintaka."
        ),
    ),
    Osamraemi(
        heiti="Talan 236 var eitt sinn birt sem skráafjöldi",
        alvarleiki="skrad",
        stadir=(
            ("lotur/git-ai-reproducible/agents.html",
             "„Fyrsta útgáfa forsíðunnar sagði … að þættirnir væru 236 … "
             "skrárnar eru 229, ekki 236“"),
            ("reflections/bjorn.html",
             "„Talan 236 og orðið „replikka“ stóðu bæði á síðunni eftir mína "
             "rýni“"),
            ("friends/phoebe-statistics.html",
             "„227 skrár sem ná yfir 236 sýnda þætti“"),
        ),
        nidurstada=(
            "236 er réttur fjöldi sýndra þátta en var einhvern tíma birtur sem "
            "fjöldi handritsskráa. Gamla verkefnið skjalfestir sína eigin "
            "leiðréttingu á tveimur síðum."
        ),
        profun="236 finnst á fjórum síðum; tvær þeirra lýsa því sem villu",
        afleiding=(
            "Nýja síðan má ekki nota 236 sem skráafjölda. Skrár = 227, "
            "þættir = 236."
        ),
    ),
)
