from __future__ import annotations

from abc import ABC, abstractmethod
from math import ceil, log2
from typing import Optional

from bracketforge.models import Match, MatchStatus, Round, Team


class SchedulingStrategy(ABC):
    @abstractmethod
    def generate_rounds(self, teams: list[Team]) -> list[Round]:
        pass


def _round_robin_pairings(
    teams: list[Team], max_rounds: Optional[int] = None
) -> list[list[tuple[Optional[Team], Optional[Team]]]]:
    # circle method: fix one team, rotate the rest each round
    working: list[Optional[Team]] = list(teams)
    if len(working) % 2 == 1:
        working.append(None)
    n = len(working)
    total_rounds = n - 1
    rounds_to_build = min(total_rounds, max_rounds) if max_rounds is not None else total_rounds

    fixed, rotating = working[0], working[1:]
    pairings_per_round = []
    for _ in range(rounds_to_build):
        round_teams = [fixed] + rotating
        pairs = [(round_teams[i], round_teams[-(i + 1)]) for i in range(n // 2)]
        pairings_per_round.append(pairs)
        rotating = [rotating[-1]] + rotating[:-1]
    return pairings_per_round


def _build_rounds_from_pairings(
    pairings_per_round: list[list[tuple[Optional[Team], Optional[Team]]]],
) -> list[Round]:
    rounds: list[Round] = []
    match_id = 1
    for round_number, pairs in enumerate(pairings_per_round, start=1):
        matches = []
        for home, away in pairs:
            if home is None or away is None:
                matches.append(Match.bye(match_id, round_number, home or away))
            else:
                matches.append(Match(id=match_id, round_number=round_number, team_a=home, team_b=away))
            match_id += 1
        rounds.append(Round(number=round_number, matches=matches))
    return rounds


class RoundRobinStrategy(SchedulingStrategy):
    def generate_rounds(self, teams: list[Team]) -> list[Round]:
        return _build_rounds_from_pairings(_round_robin_pairings(teams))


class SwissStrategy(SchedulingStrategy):
    # non-adaptive: pairs are seeded upfront over ceil(log2(n)) rounds using
    # the same circle method as round robin, instead of re-pairing each round
    # from live standings (generate() returns the whole schedule in one call)
    def generate_rounds(self, teams: list[Team]) -> list[Round]:
        num_rounds = max(1, ceil(log2(len(teams)))) if len(teams) > 1 else 1
        pairings = _round_robin_pairings(teams, max_rounds=num_rounds)
        return _build_rounds_from_pairings(pairings)


def _standard_seed_order(size: int) -> list[int]:
    seeds = [1]
    while len(seeds) < size:
        n = len(seeds) * 2
        seeds = [value for seed in seeds for value in (seed, n + 1 - seed)]
    return seeds


class SingleEliminationStrategy(SchedulingStrategy):
    def generate_rounds(self, teams: list[Team]) -> list[Round]:
        n = len(teams)
        bracket_size = 1 << (n - 1).bit_length()
        seed_order = _standard_seed_order(bracket_size)
        slots: list[Optional[Team]] = [teams[s - 1] if s <= n else None for s in seed_order]

        match_id = 1
        first_round_matches = []
        for i in range(0, bracket_size, 2):
            a, b = slots[i], slots[i + 1]
            if a is None or b is None:
                first_round_matches.append(Match.bye(match_id, 1, a or b))
            else:
                first_round_matches.append(Match(id=match_id, round_number=1, team_a=a, team_b=b))
            match_id += 1
        rounds = [Round(number=1, matches=first_round_matches)]

        round_number = 1
        current_round_matches = first_round_matches
        while len(current_round_matches) > 1:
            round_number += 1
            next_round_matches = []
            for i in range(0, len(current_round_matches), 2):
                placeholder = Match(id=match_id, round_number=round_number, team_a=None, team_b=None)
                match_id += 1
                current_round_matches[i].next_match = placeholder
                current_round_matches[i].next_match_slot = 0
                current_round_matches[i + 1].next_match = placeholder
                current_round_matches[i + 1].next_match_slot = 1
                next_round_matches.append(placeholder)
            rounds.append(Round(number=round_number, matches=next_round_matches))
            current_round_matches = next_round_matches

        self._propagate_byes(rounds)
        return rounds

    @staticmethod
    def _propagate_byes(rounds: list[Round]) -> None:
        for round_ in rounds:
            for match in round_.matches:
                if match.status == MatchStatus.COMPLETED and match.next_match is not None:
                    if match.next_match_slot == 0:
                        match.next_match.team_a = match.winner
                    else:
                        match.next_match.team_b = match.winner
