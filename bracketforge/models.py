from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from bracketforge.exceptions import InvalidMatchTransitionError


class TournamentFormat(Enum):
    ROUND_ROBIN = "round_robin"
    SINGLE_ELIMINATION = "single_elimination"
    SWISS = "swiss"


class MatchStatus(Enum):
    SCHEDULED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()


@dataclass(frozen=True)
class Team:
    name: str


@dataclass
class Match:
    id: int
    round_number: int
    team_a: Optional[Team]
    team_b: Optional[Team]
    status: MatchStatus = MatchStatus.SCHEDULED
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    next_match: Optional["Match"] = field(default=None, repr=False)
    next_match_slot: Optional[int] = None

    @classmethod
    def bye(cls, id: int, round_number: int, team: Team) -> "Match":
        return cls(
            id=id,
            round_number=round_number,
            team_a=team,
            team_b=None,
            status=MatchStatus.COMPLETED,
        )

    @property
    def is_bye(self) -> bool:
        # a walkover is COMPLETED with only one side ever set; a match still
        # waiting on its other feeder round is SCHEDULED, not a bye
        return self.status == MatchStatus.COMPLETED and (self.team_a is None) != (
            self.team_b is None
        )

    @property
    def is_ready(self) -> bool:
        return self.team_a is not None and self.team_b is not None

    @property
    def winner(self) -> Optional[Team]:
        if self.status != MatchStatus.COMPLETED:
            return None
        if self.is_bye:
            return self.team_a if self.team_a is not None else self.team_b
        if self.score_a is None or self.score_b is None:
            return None
        return self.team_a if self.score_a > self.score_b else self.team_b

    def start(self) -> None:
        if self.status != MatchStatus.SCHEDULED:
            raise InvalidMatchTransitionError(
                f"Match {self.id} cannot start from state {self.status.name}"
            )
        if not self.is_ready:
            raise InvalidMatchTransitionError(f"Match {self.id} is missing a team and cannot start")
        self.status = MatchStatus.IN_PROGRESS
        self.score_a = 0
        self.score_b = 0

    def adjust_score(self, side: str, delta: int) -> None:
        if self.status != MatchStatus.IN_PROGRESS:
            raise InvalidMatchTransitionError(f"Match {self.id} is not in progress")
        if side not in ("a", "b"):
            raise ValueError("side must be 'a' or 'b'")
        if side == "a":
            self.score_a = max(0, (self.score_a or 0) + delta)
        else:
            self.score_b = max(0, (self.score_b or 0) + delta)

    def complete(self, score_a: int, score_b: int) -> None:
        if self.status != MatchStatus.IN_PROGRESS:
            raise InvalidMatchTransitionError(
                f"Match {self.id} cannot complete from state {self.status.name}"
            )
        if score_a == score_b:
            raise InvalidMatchTransitionError("Draws are not supported; scores must differ")
        self.score_a = score_a
        self.score_b = score_b
        self.status = MatchStatus.COMPLETED


@dataclass
class Round:
    number: int
    matches: list[Match] = field(default_factory=list)


@dataclass
class Tournament:
    format: TournamentFormat
    teams: list[Team]
    rounds: list[Round] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return all(
            match.status == MatchStatus.COMPLETED
            for round_ in self.rounds
            for match in round_.matches
        )

    def start_match(self, match: Match) -> None:
        match.start()

    def adjust_score(self, match: Match, side: str, delta: int) -> None:
        match.adjust_score(side, delta)

    def complete_match(
        self, match: Match, score_a: Optional[int] = None, score_b: Optional[int] = None
    ) -> None:
        final_a = match.score_a if score_a is None else score_a
        final_b = match.score_b if score_b is None else score_b
        match.complete(final_a, final_b)
        self._advance_winner(match)

    def _advance_winner(self, match: Match) -> None:
        next_match = match.next_match
        if next_match is None:
            return
        if match.next_match_slot == 0:
            next_match.team_a = match.winner
        else:
            next_match.team_b = match.winner
