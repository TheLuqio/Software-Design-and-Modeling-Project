from __future__ import annotations

from bracketforge.exceptions import DuplicateTeamError, InsufficientTeamsError
from bracketforge.factory import StrategyFactory
from bracketforge.models import Team, Tournament, TournamentFormat

MIN_TEAMS = 2


def _validate_teams(teams: list[Team]) -> None:
    if len(teams) < MIN_TEAMS:
        raise InsufficientTeamsError(f"At least {MIN_TEAMS} teams are required, got {len(teams)}")
    normalized_names = [team.name.strip().lower() for team in teams]
    if len(normalized_names) != len(set(normalized_names)):
        raise DuplicateTeamError("Duplicate team names are not allowed")


class Scheduler:
    def generate(self, teams: list[Team], format_: TournamentFormat) -> Tournament:
        _validate_teams(teams)
        strategy = StrategyFactory.create(format_)
        rounds = strategy.generate_rounds(teams)
        return Tournament(format=format_, teams=list(teams), rounds=rounds)


class TournamentBuilder:
    def __init__(self) -> None:
        self._team_names: list[str] = []
        self._format: TournamentFormat | None = None

    def add_team(self, name: str) -> "TournamentBuilder":
        name = name.strip()
        if not name:
            raise ValueError("Team name cannot be empty")
        self._team_names.append(name)
        return self

    def add_teams(self, names: list[str]) -> "TournamentBuilder":
        for name in names:
            self.add_team(name)
        return self

    def with_format(self, format_: TournamentFormat) -> "TournamentBuilder":
        self._format = format_
        return self

    def build(self) -> Tournament:
        if self._format is None:
            raise ValueError("Tournament format must be set before building")
        teams = [Team(name=name) for name in self._team_names]
        return Scheduler().generate(teams, self._format)
