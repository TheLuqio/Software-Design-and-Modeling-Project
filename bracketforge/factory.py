from __future__ import annotations

from bracketforge.exceptions import InvalidTournamentError
from bracketforge.models import TournamentFormat
from bracketforge.strategies import (
    RoundRobinStrategy,
    SchedulingStrategy,
    SingleEliminationStrategy,
    SwissStrategy,
)

_STRATEGIES: dict[TournamentFormat, type[SchedulingStrategy]] = {
    TournamentFormat.ROUND_ROBIN: RoundRobinStrategy,
    TournamentFormat.SINGLE_ELIMINATION: SingleEliminationStrategy,
    TournamentFormat.SWISS: SwissStrategy,
}


class StrategyFactory:
    @staticmethod
    def create(format_: TournamentFormat) -> SchedulingStrategy:
        try:
            strategy_cls = _STRATEGIES[format_]
        except KeyError:
            raise InvalidTournamentError(f"Unsupported tournament format: {format_}") from None
        return strategy_cls()
