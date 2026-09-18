class BracketForgeError(Exception):
    pass


class InvalidTournamentError(BracketForgeError):
    pass


class InsufficientTeamsError(InvalidTournamentError):
    pass


class DuplicateTeamError(InvalidTournamentError):
    pass


class InvalidMatchTransitionError(BracketForgeError):
    pass
