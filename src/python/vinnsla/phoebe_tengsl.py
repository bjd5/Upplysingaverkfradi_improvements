"""Tengsl: hver talar mest við Phoebe (issue #14, pakki P2.5).

Aðalmælikvarðinn er nálæg ræðuskipti innan sömu senu: tali X strax á eftir
Phoebe (eða öfugt) telst það ein samskipti. Stuðningsmælikvarðar: línur í
senum þar sem aðeins þau tvö tala, sameiginlegar senur og línur X sem nefna
hana á nafn.

``interaction_lift`` leiðréttir fyrir mælgi: mæld hlutdeild X í samskiptum
Phoebe deilt með hlutdeild X í öllum línum hinna fimm. Gildi yfir 1 þýðir að X
talar oftar við hana en mælgi hans ein skýrir. Flutt óbreytt að virkni úr
skrefum 2c og 3 í ``src/phoebe_analysis.py`` (commit ``2865ed6``).

Eingöngu staðalsafnið (regla 10).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

try:  # keyrt sem eining innan pakkans
    from .friends_thattari import PERSON, Episode, speaker_lines
    from .phoebe_skilgreiningar import (
        ADDRESS_EDGE_WORDS, FRIENDS, LIFT_DECIMALS, MAX_GUEST_ROWS, OTHER_FRIENDS,
        PERCENT_DECIMALS, PHOEBE, PHOEBE_NAME_RE, pct,
    )
except ImportError:  # keyrt beint úr möppunni
    from friends_thattari import PERSON, Episode, speaker_lines
    from phoebe_skilgreiningar import (
        ADDRESS_EDGE_WORDS, FRIENDS, LIFT_DECIMALS, MAX_GUEST_ROWS, OTHER_FRIENDS,
        PERCENT_DECIMALS, PHOEBE, PHOEBE_NAME_RE, pct,
    )


@dataclass
class Interactions:
    """Hráar talningar samskipta við Phoebe, yfir alla ræðumenn (líka gesti)."""

    after_phoebe: Counter = field(default_factory=Counter)    # X talar strax á eftir henni
    before_phoebe: Counter = field(default_factory=Counter)   # hún talar strax á eftir X
    duet_lines: Counter = field(default_factory=Counter)      # senur með aðeins henni og X
    addressed: Counter = field(default_factory=Counter)       # línur X sem nefna hana
    addressed_edge: Counter = field(default_factory=Counter)  # nafnið fremst eða aftast
    shared_scenes: Counter = field(default_factory=Counter)   # senur þar sem bæði tala
    after_by_season: dict = field(default_factory=lambda: defaultdict(Counter))
    before_by_season: dict = field(default_factory=lambda: defaultdict(Counter))


def _count_adjacent(episode: Episode, turns: list, result: Interactions) -> None:
    for a, b in zip(turns, turns[1:]):
        if a.scene != b.scene or a.speaker == b.speaker:
            continue
        if a.speaker == PHOEBE:
            result.after_phoebe[b.speaker] += 1
            result.after_by_season[episode.season][b.speaker] += 1
        elif b.speaker == PHOEBE:
            result.before_phoebe[a.speaker] += 1
            result.before_by_season[episode.season][a.speaker] += 1


def _count_scenes(turns: list, result: Interactions) -> None:
    by_scene: dict[int, list[str]] = defaultdict(list)
    for line in turns:
        by_scene[line.scene].append(line.speaker)
    for speakers in by_scene.values():
        present = set(speakers)
        if PHOEBE not in present:
            continue
        for other in present - {PHOEBE}:
            result.shared_scenes[other] += 1
        if len(present) == 2:
            other = next(iter(present - {PHOEBE}))
            result.duet_lines[other] += len(speakers)


def _count_addresses(episode: Episode, result: Interactions) -> None:
    for line in episode.lines:
        if line.kind != PERSON or line.speaker in ("", PHOEBE):
            continue
        if not PHOEBE_NAME_RE.search(line.spoken):
            continue
        result.addressed[line.speaker] += 1
        words = line.spoken.split()
        head = " ".join(words[:ADDRESS_EDGE_WORDS]).lower()
        tail = " ".join(words[-ADDRESS_EDGE_WORDS:]).lower()
        if PHOEBE_NAME_RE.search(head) or PHOEBE_NAME_RE.search(tail):
            result.addressed_edge[line.speaker] += 1


def count_interactions(episodes: list[Episode]) -> Interactions:
    """Telur ræðuskipti, sameiginlegar senur og ávörp — hóplínum sleppt."""
    result = Interactions()
    for episode in episodes:
        turns = speaker_lines(episode)
        _count_adjacent(episode, turns, result)
        _count_scenes(turns, result)
        _count_addresses(episode, result)
    return result


def talker_rows(result: Interactions, total_lines: Counter) -> list[dict]:
    """Vinirnir fimm raðaðir eftir ræðuskiptum, með ``interaction_lift``.

    Fellur með ``ValueError`` ef enginn vinanna talaði við Phoebe eða enginn
    þeirra sagði neitt — þá er hlutdeildin ekki skilgreind.
    """
    total_after = sum(result.after_phoebe[c] for c in OTHER_FRIENDS)
    total_before = sum(result.before_phoebe[c] for c in OTHER_FRIENDS)
    base_total = sum(total_lines[c] for c in OTHER_FRIENDS)
    if not (total_after + total_before) or not base_total:
        raise ValueError("Engin ræðuskipti við Phoebe fundust — tengslin eru óskilgreind.")

    rows = []
    for c in OTHER_FRIENDS:
        adjacent = result.after_phoebe[c] + result.before_phoebe[c]
        observed = adjacent / (total_after + total_before)
        expected = total_lines[c] / base_total
        rows.append(dict(
            character=c,
            adjacent_turns=adjacent,
            replies_to_phoebe=result.after_phoebe[c],
            phoebe_replies_to=result.before_phoebe[c],
            two_person_scene_lines=result.duet_lines[c],
            shared_speaking_scenes=result.shared_scenes[c],
            lines_mentioning_phoebe=result.addressed[c],
            lines_naming_phoebe_at_edge=result.addressed_edge[c],
            adjacency_share_pct=round(100 * observed, PERCENT_DECIMALS),
            expected_share_pct=round(100 * expected, PERCENT_DECIMALS),
            interaction_lift=round(observed / expected, LIFT_DECIMALS),
            total_lines_in_show=total_lines[c]))
    rows.sort(key=lambda r: -r["adjacent_turns"])
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows


def guest_rows(result: Interactions) -> list[dict]:
    """Persónur utan vinahópsins sem tala mest við Phoebe (efstu ``MAX_GUEST_ROWS``).

    Raðað úr röðuðu mengi og jafntefli leyst eftir nafni: ítrun yfir ``set``
    er háð ``PYTHONHASHSEED`` og röðunin á að vera ástand gagnanna, ekki tilviljun.
    """
    rows = [
        dict(character=c,
             adjacent_turns=result.after_phoebe[c] + result.before_phoebe[c],
             replies_to_phoebe=result.after_phoebe[c],
             phoebe_replies_to=result.before_phoebe[c],
             shared_speaking_scenes=result.shared_scenes[c])
        for c in sorted(set(result.after_phoebe) | set(result.before_phoebe))
        if c not in FRIENDS
    ]
    rows.sort(key=lambda r: (-r["adjacent_turns"], r["character"]))
    return rows[:MAX_GUEST_ROWS]


def season_talker_rows(result: Interactions, seasons: list[int]) -> list[dict]:
    """Ræðuskipti vinanna fimm við Phoebe innan hverrar þáttaraðar."""
    rows = []
    for s in seasons:
        totals: Counter = Counter()
        for c in OTHER_FRIENDS:
            totals[c] = result.after_by_season[s][c] + result.before_by_season[s][c]
        season_total = sum(totals.values())
        for c, turns in totals.most_common():
            rows.append(dict(
                season=s, character=c, adjacent_turns=turns,
                replies_to_phoebe=result.after_by_season[s][c],
                phoebe_replies_to=result.before_by_season[s][c],
                share_of_phoebe_interactions_pct=pct(turns, season_total)))
    return rows


def interaction_matrix(episodes: list[Episode]) -> Counter:
    """Hversu oft talar A strax á eftir B innan senu, fyrir öll pör vinanna.

    Lykillinn er ``(A, B)`` = A svarar B. Báðar áttir eru geymdar sér, því
    „Phoebe svarar Ross“ og „Ross svarar Phoebe“ eru ekki sama talan. Sami
    ræðulisti og í ``count_interactions`` svo tölurnar stemmi milli skráa.
    """
    pairs: Counter = Counter()
    for episode in episodes:
        turns = speaker_lines(episode)
        for a, b in zip(turns, turns[1:]):
            if (a.scene == b.scene and a.speaker != b.speaker
                    and a.speaker in FRIENDS and b.speaker in FRIENDS):
                pairs[(b.speaker, a.speaker)] += 1
    return pairs
