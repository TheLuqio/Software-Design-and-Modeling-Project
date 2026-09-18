# BracketForge

A tournament fixture scheduling library with a small Tkinter desktop app
built on top of it, for entering teams and watching the schedule play out.

## Elevator pitch

Give BracketForge a list of team names and a format, and it hands back a
full, valid match schedule. It supports round robin, single elimination
(byes get handled automatically when the team count isn't a power of two),
and Swiss pairing. All of that scheduling logic sits in a standalone,
pip-installable library that doesn't know anything about GUIs — it's built
around the Strategy, Factory, Facade, and Builder patterns. The desktop app
just calls into the library's facade and renders whatever comes back,
including matches moving live through scheduled, in progress, and completed.

## Installing and running the app

Needs Python 3.11+. Tkinter comes bundled with the standard Windows/macOS
installers; on Linux you'll probably need your distro's `python3-tk` package
separately.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -e ".[dev]"         # installs bracketforge + pytest

python -m app.main              # launches the desktop app
```

Type a team name and hit Enter (or click Add Team), repeat for however many
teams you have, pick a format from the dropdown, then click Generate
Schedule. Clicking Start on a match opens a live scoreboard with A±1/B±1
buttons and a 60-second clock. You can bump either score up or down while
the clock is running; once it hits 0:00 the +/- buttons lock and Finish is
the only thing left to click. Finishing records whatever score is showing
(a tie gets rejected, so nudge one side first), and in single elimination
the winner gets pushed into the next round automatically.

## Using the library standalone

`app/` is the only thing that depends on `bracketforge/` — the reverse isn't
true, so you can install and use the library completely on its own:

```python
from bracketforge import Scheduler, Team, TournamentFormat

teams = [Team("Falcons"), Team("Hawks"), Team("Eagles"), Team("Owls")]
tournament = Scheduler().generate(teams, TournamentFormat.ROUND_ROBIN)

for round_ in tournament.rounds:
    print(f"Round {round_.number}")
    for match in round_.matches:
        print(f"  {match.team_a.name} vs {match.team_b.name}")
```

[`examples/use_library.py`](examples/use_library.py) is a longer runnable
version of this that walks through all three formats, byes, and a match
being played out from start to finish:

```bash
python examples/use_library.py
```

## Architecture overview

Two packages, one dependency direction:

```
bracketforge/   the library: domain model, strategies, facade — zero GUI code
app/            the desktop client: Tkinter only — zero scheduling logic
```

`app/` imports from `bracketforge/`; nothing in `bracketforge/` ever imports
from `app/`. The reasoning behind each class, plus the UML diagrams (class,
sequence, activity, state — they're embedded as Mermaid and render right on
GitHub), lives in [`docs/DESIGN.md`](docs/DESIGN.md).

## Design patterns used

Four patterns show up in the library:

- **Strategy** splits each format's pairing logic into its own class
  (`RoundRobinStrategy`, `SingleEliminationStrategy`, `SwissStrategy`) behind
  a common `SchedulingStrategy` interface, so a new format can be added
  without touching the existing ones.
- **Factory** (`StrategyFactory.create(format)`) is the one place that knows
  which format maps to which strategy class, instead of that mapping being
  duplicated as `if/elif` chains wherever a strategy gets used.
- **Facade** (`Scheduler.generate(teams, format) -> Tournament`) gives
  callers a single entry point that takes care of validation, picking a
  strategy, and putting the `Tournament` together.
- **Builder** (`TournamentBuilder`) wraps the facade for callers that start
  from plain team-name strings rather than `Team` objects — which is exactly
  what the GUI's text entry does.

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

43 tests, covering the match state machine, live score adjustment, all three
scheduling strategies (odd team counts, non-power-of-two brackets, bye
propagation), and input validation in the facade and builder.
