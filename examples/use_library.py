# Run with: python examples/use_library.py
# Only imports bracketforge, no app/ dependency.

from bracketforge import (
    InvalidTournamentError,
    Scheduler,
    Team,
    TournamentBuilder,
    TournamentFormat,
)


def print_tournament(tournament):
    for round_ in tournament.rounds:
        print(f"  Round {round_.number}")
        for match in round_.matches:
            if match.is_bye:
                team = match.team_a or match.team_b
                print(f"    {team.name} gets a bye")
            else:
                a = match.team_a.name if match.team_a else "TBD"
                b = match.team_b.name if match.team_b else "TBD"
                print(f"    {a} vs {b}")


def round_robin_example():
    print("== Round robin (facade + Team objects) ==")
    teams = [Team("Falcons"), Team("Hawks"), Team("Eagles"), Team("Owls")]
    tournament = Scheduler().generate(teams, TournamentFormat.ROUND_ROBIN)
    print_tournament(tournament)
    print()


def single_elimination_example():
    print("== Single elimination with 5 teams (builder + byes) ==")
    tournament = (
        TournamentBuilder()
        .add_teams(["Falcons", "Hawks", "Eagles", "Owls", "Ravens"])
        .with_format(TournamentFormat.SINGLE_ELIMINATION)
        .build()
    )
    print_tournament(tournament)

    print("\n  Playing round 1 to show winners advance into round 2...")
    first_round = tournament.rounds[0]
    real_match = next(m for m in first_round.matches if not m.is_bye)
    tournament.start_match(real_match)
    tournament.complete_match(real_match, 2, 1)
    print(f"  {real_match.team_a.name} beat {real_match.team_b.name}\n")
    print_tournament(tournament)
    print()


def swiss_example():
    print("== Swiss with 6 teams ==")
    teams = [Team(f"Team {i}") for i in range(1, 7)]
    tournament = Scheduler().generate(teams, TournamentFormat.SWISS)
    print_tournament(tournament)
    print()


def validation_example():
    print("== Validation: too few teams ==")
    try:
        Scheduler().generate([Team("Solo")], TournamentFormat.ROUND_ROBIN)
    except InvalidTournamentError as exc:
        print(f"  Rejected as expected: {exc}")


if __name__ == "__main__":
    round_robin_example()
    single_elimination_example()
    swiss_example()
    validation_example()
