import pytest

from bracketforge.exceptions import InvalidMatchTransitionError
from bracketforge.models import Match, MatchStatus, Round, Team, Tournament, TournamentFormat


def make_match(team_b_present: bool = True) -> Match:
    team_a = Team("Alpha")
    team_b = Team("Beta") if team_b_present else None
    return Match(id=1, round_number=1, team_a=team_a, team_b=team_b)


class TestMatchLifecycle:
    def test_new_match_is_scheduled(self):
        match = make_match()
        assert match.status == MatchStatus.SCHEDULED
        assert match.winner is None

    def test_start_moves_to_in_progress(self):
        match = make_match()
        match.start()
        assert match.status == MatchStatus.IN_PROGRESS

    def test_cannot_start_twice(self):
        match = make_match()
        match.start()
        with pytest.raises(InvalidMatchTransitionError):
            match.start()

    def test_cannot_start_without_both_teams(self):
        match = make_match(team_b_present=False)
        with pytest.raises(InvalidMatchTransitionError):
            match.start()

    def test_complete_before_start_raises(self):
        match = make_match()
        with pytest.raises(InvalidMatchTransitionError):
            match.complete(1, 0)

    def test_full_lifecycle_and_winner(self):
        match = make_match()
        match.start()
        match.complete(3, 1)
        assert match.status == MatchStatus.COMPLETED
        assert match.winner == match.team_a

    def test_cannot_complete_twice(self):
        match = make_match()
        match.start()
        match.complete(3, 1)
        with pytest.raises(InvalidMatchTransitionError):
            match.complete(1, 0)

    def test_draw_is_rejected(self):
        match = make_match()
        match.start()
        with pytest.raises(InvalidMatchTransitionError):
            match.complete(2, 2)


class TestLiveScoring:
    def test_start_resets_score_to_zero(self):
        match = make_match()
        match.start()
        assert match.score_a == 0
        assert match.score_b == 0

    def test_adjust_score_increments_each_side(self):
        match = make_match()
        match.start()
        match.adjust_score("a", 1)
        match.adjust_score("a", 1)
        match.adjust_score("b", 1)
        assert match.score_a == 2
        assert match.score_b == 1

    def test_adjust_score_cannot_go_negative(self):
        match = make_match()
        match.start()
        match.adjust_score("a", -1)
        assert match.score_a == 0

    def test_adjust_score_requires_match_in_progress(self):
        match = make_match()
        with pytest.raises(InvalidMatchTransitionError):
            match.adjust_score("a", 1)

    def test_adjust_score_rejects_unknown_side(self):
        match = make_match()
        match.start()
        with pytest.raises(ValueError):
            match.adjust_score("c", 1)

    def test_tournament_complete_match_defaults_to_live_score(self):
        team_a, team_b = Team("Alpha"), Team("Beta")
        match = Match(id=1, round_number=1, team_a=team_a, team_b=team_b)
        tournament = Tournament(
            format=TournamentFormat.ROUND_ROBIN,
            teams=[team_a, team_b],
            rounds=[Round(number=1, matches=[match])],
        )
        tournament.start_match(match)
        tournament.adjust_score(match, "a", 3)
        tournament.adjust_score(match, "b", 1)
        tournament.complete_match(match)
        assert match.status == MatchStatus.COMPLETED
        assert match.winner == team_a


class TestBye:
    def test_bye_is_completed_immediately(self):
        team = Team("Alpha")
        match = Match.bye(1, 1, team)
        assert match.status == MatchStatus.COMPLETED
        assert match.is_bye
        assert match.winner == team

    def test_bye_cannot_be_started(self):
        match = Match.bye(1, 1, Team("Alpha"))
        with pytest.raises(InvalidMatchTransitionError):
            match.start()

    def test_regular_match_is_not_a_bye(self):
        match = make_match()
        assert not match.is_bye
        assert match.is_ready
