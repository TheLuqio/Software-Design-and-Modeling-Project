import pytest

from bracketforge.exceptions import (
    DuplicateTeamError,
    InsufficientTeamsError,
    InvalidTournamentError,
)
from bracketforge.factory import StrategyFactory
from bracketforge.models import Team, TournamentFormat
from bracketforge.scheduler import Scheduler, TournamentBuilder
from bracketforge.strategies import RoundRobinStrategy, SingleEliminationStrategy, SwissStrategy


class TestStrategyFactory:
    @pytest.mark.parametrize(
        "format_, expected_type",
        [
            (TournamentFormat.ROUND_ROBIN, RoundRobinStrategy),
            (TournamentFormat.SINGLE_ELIMINATION, SingleEliminationStrategy),
            (TournamentFormat.SWISS, SwissStrategy),
        ],
    )
    def test_creates_matching_strategy(self, format_, expected_type):
        assert isinstance(StrategyFactory.create(format_), expected_type)


class TestScheduler:
    def test_generate_returns_populated_tournament(self):
        teams = [Team("A"), Team("B"), Team("C"), Team("D")]
        tournament = Scheduler().generate(teams, TournamentFormat.ROUND_ROBIN)
        assert tournament.format == TournamentFormat.ROUND_ROBIN
        assert tournament.teams == teams
        assert len(tournament.rounds) == 3

    def test_rejects_too_few_teams(self):
        with pytest.raises(InsufficientTeamsError):
            Scheduler().generate([Team("A")], TournamentFormat.ROUND_ROBIN)

    def test_rejects_empty_team_list(self):
        with pytest.raises(InsufficientTeamsError):
            Scheduler().generate([], TournamentFormat.SWISS)

    def test_rejects_duplicate_team_names(self):
        with pytest.raises(DuplicateTeamError):
            Scheduler().generate([Team("A"), Team("a")], TournamentFormat.ROUND_ROBIN)

    def test_duplicate_and_insufficient_are_invalid_tournament_errors(self):
        assert issubclass(DuplicateTeamError, InvalidTournamentError)
        assert issubclass(InsufficientTeamsError, InvalidTournamentError)


class TestTournamentBuilder:
    def test_builds_tournament_from_names(self):
        tournament = (
            TournamentBuilder()
            .add_teams(["Alpha", "Beta", "Gamma", "Delta"])
            .with_format(TournamentFormat.SINGLE_ELIMINATION)
            .build()
        )
        assert len(tournament.teams) == 4
        assert tournament.format == TournamentFormat.SINGLE_ELIMINATION

    def test_add_team_strips_whitespace(self):
        builder = TournamentBuilder().add_team("  Alpha  ")
        assert builder._team_names == ["Alpha"]

    def test_add_team_rejects_empty_name(self):
        with pytest.raises(ValueError):
            TournamentBuilder().add_team("   ")

    def test_build_without_format_raises(self):
        builder = TournamentBuilder().add_teams(["A", "B"])
        with pytest.raises(ValueError):
            builder.build()

    def test_build_propagates_scheduler_validation(self):
        builder = TournamentBuilder().add_team("Solo").with_format(TournamentFormat.ROUND_ROBIN)
        with pytest.raises(InsufficientTeamsError):
            builder.build()
