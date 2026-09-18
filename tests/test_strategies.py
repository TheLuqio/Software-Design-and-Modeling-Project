from math import ceil, log2

from bracketforge.models import MatchStatus, Team, Tournament, TournamentFormat
from bracketforge.strategies import RoundRobinStrategy, SingleEliminationStrategy, SwissStrategy


def teams(n: int) -> list[Team]:
    return [Team(f"Team {i}") for i in range(1, n + 1)]


class TestRoundRobinStrategy:
    def test_even_teams_every_pair_meets_once(self):
        n = 6
        rounds = RoundRobinStrategy().generate_rounds(teams(n))
        assert len(rounds) == n - 1

        pairs_seen = set()
        for round_ in rounds:
            round_teams = set()
            for match in round_.matches:
                assert not match.is_bye
                pair = frozenset({match.team_a.name, match.team_b.name})
                assert pair not in pairs_seen
                pairs_seen.add(pair)
                round_teams.update({match.team_a.name, match.team_b.name})
            assert len(round_teams) == n

        assert len(pairs_seen) == n * (n - 1) // 2

    def test_odd_teams_produce_exactly_one_bye_per_round(self):
        n = 5
        rounds = RoundRobinStrategy().generate_rounds(teams(n))
        assert len(rounds) == n

        for round_ in rounds:
            byes = [m for m in round_.matches if m.is_bye]
            assert len(byes) == 1
            assert byes[0].status == MatchStatus.COMPLETED

    def test_no_team_plays_itself(self):
        rounds = RoundRobinStrategy().generate_rounds(teams(4))
        for round_ in rounds:
            for match in round_.matches:
                assert match.team_a != match.team_b


class TestSingleEliminationStrategy:
    def test_power_of_two_has_no_byes(self):
        rounds = SingleEliminationStrategy().generate_rounds(teams(4))
        assert len(rounds) == 2
        assert len(rounds[0].matches) == 2
        assert len(rounds[1].matches) == 1
        assert all(not m.is_bye for m in rounds[0].matches)
        assert rounds[1].matches[0].team_a is None
        assert rounds[1].matches[0].team_b is None

    def test_non_power_of_two_gets_correct_bye_count(self):
        n = 5
        rounds = SingleEliminationStrategy().generate_rounds(teams(n))
        first_round = rounds[0]
        assert len(first_round.matches) == 4
        byes = [m for m in first_round.matches if m.is_bye]
        assert len(byes) == 3
        real_matches = [m for m in first_round.matches if not m.is_bye]
        assert len(real_matches) == 1

    def test_bracket_produces_single_champion_slot(self):
        rounds = SingleEliminationStrategy().generate_rounds(teams(6))
        final_round = rounds[-1]
        assert len(final_round.matches) == 1

    def test_winner_propagates_through_bracket(self):
        t = Tournament(format=TournamentFormat.SINGLE_ELIMINATION, teams=teams(4),
                        rounds=SingleEliminationStrategy().generate_rounds(teams(4)))
        r1_matches = t.rounds[0].matches
        final_match = t.rounds[1].matches[0]

        t.start_match(r1_matches[0])
        t.complete_match(r1_matches[0], 2, 1)
        assert final_match.team_a == r1_matches[0].winner

        t.start_match(r1_matches[1])
        t.complete_match(r1_matches[1], 0, 3)
        assert final_match.team_b == r1_matches[1].winner
        assert final_match.is_ready

    def test_placeholder_partially_filled_by_a_bye_is_not_itself_a_bye(self):
        """A round-2 slot that a round-1 bye has already advanced into (while
        its other feeder match is still unplayed) must not read as a bye
        itself -- it is a pending TBD match, not a walkover."""
        rounds = SingleEliminationStrategy().generate_rounds(teams(5))
        second_round = rounds[1]
        partially_filled = next(
            m for m in second_round.matches if m.team_a is not None and m.team_b is None
        )
        assert not partially_filled.is_ready
        assert not partially_filled.is_bye
        assert partially_filled.status == MatchStatus.SCHEDULED

    def test_bye_winner_propagates_immediately(self):
        rounds = SingleEliminationStrategy().generate_rounds(teams(3))
        first_round = rounds[0]
        bye_match = next(m for m in first_round.matches if m.is_bye)
        assert bye_match.next_match is not None
        slot_team = (
            bye_match.next_match.team_a
            if bye_match.next_match_slot == 0
            else bye_match.next_match.team_b
        )
        assert slot_team == bye_match.winner


class TestSwissStrategy:
    def test_round_count_is_log2_of_team_count(self):
        n = 8
        rounds = SwissStrategy().generate_rounds(teams(n))
        assert len(rounds) == ceil(log2(n))

    def test_no_repeated_pairings_across_rounds(self):
        rounds = SwissStrategy().generate_rounds(teams(8))
        pairs_seen = set()
        for round_ in rounds:
            for match in round_.matches:
                if match.is_bye:
                    continue
                pair = frozenset({match.team_a.name, match.team_b.name})
                assert pair not in pairs_seen
                pairs_seen.add(pair)

    def test_odd_team_count_has_bye_each_round(self):
        rounds = SwissStrategy().generate_rounds(teams(5))
        for round_ in rounds:
            byes = [m for m in round_.matches if m.is_bye]
            assert len(byes) == 1

    def test_two_teams_gets_one_round(self):
        rounds = SwissStrategy().generate_rounds(teams(2))
        assert len(rounds) == 1
        assert len(rounds[0].matches) == 1
