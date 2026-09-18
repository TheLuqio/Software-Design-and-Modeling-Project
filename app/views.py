import tkinter as tk
from tkinter import messagebox, ttk

from bracketforge import InvalidMatchTransitionError, MatchStatus

MATCH_CLOCK_SECONDS = 60

_STATUS_TEXT = {
    MatchStatus.SCHEDULED: "Scheduled",
    MatchStatus.IN_PROGRESS: "In Progress",
    MatchStatus.COMPLETED: "Completed",
}

_STATUS_COLOR = {
    MatchStatus.SCHEDULED: "#666666",
    MatchStatus.IN_PROGRESS: "#b8860b",
    MatchStatus.COMPLETED: "#1a7a1a",
}


def render_tournament(parent, tournament, on_update):
    for child in parent.winfo_children():
        child.destroy()

    for round_ in tournament.rounds:
        round_frame = ttk.LabelFrame(parent, text=f"Round {round_.number}", padding=8)
        round_frame.pack(fill="x", pady=(0, 8))
        for match in round_.matches:
            _render_match(round_frame, tournament, match, on_update)


def _team_label(team):
    return team.name if team is not None else "TBD"


def _render_match(parent, tournament, match, on_update):
    row = ttk.Frame(parent)
    row.pack(fill="x", pady=2)

    if match.is_bye:
        text = f"{_team_label(match.team_a or match.team_b)}  (bye)"
    else:
        text = f"{_team_label(match.team_a)}  vs  {_team_label(match.team_b)}"
        if match.status == MatchStatus.COMPLETED:
            text += f"   [{match.score_a} - {match.score_b}]"
    ttk.Label(row, text=text, width=36, anchor="w").pack(side="left")

    ttk.Label(
        row, text=_STATUS_TEXT[match.status], foreground=_STATUS_COLOR[match.status], width=12
    ).pack(side="left", padx=(0, 10))

    if match.is_bye:
        return

    if match.status == MatchStatus.SCHEDULED:
        ttk.Button(
            row,
            text="Start",
            state="normal" if match.is_ready else "disabled",
            command=lambda: _start(tournament, match, on_update),
        ).pack(side="left")
    elif match.status == MatchStatus.IN_PROGRESS:
        _render_scoreboard(row, tournament, match, on_update)


def _start(tournament, match, on_update):
    tournament.start_match(match)
    on_update()


def _render_scoreboard(row, tournament, match, on_update):
    """Live score entry, open for MATCH_CLOCK_SECONDS before it locks."""
    score_var = tk.StringVar(value=f"{match.score_a} - {match.score_b}")
    clock_var = tk.StringVar()

    def bump(side, delta):
        tournament.adjust_score(match, side, delta)
        score_var.set(f"{match.score_a} - {match.score_b}")

    a_minus = ttk.Button(row, text="A-1", width=4, command=lambda: bump("a", -1))
    a_plus = ttk.Button(row, text="A+1", width=4, command=lambda: bump("a", 1))
    a_minus.pack(side="left")
    a_plus.pack(side="left")
    ttk.Label(row, textvariable=score_var, width=7, anchor="center").pack(side="left", padx=4)
    b_minus = ttk.Button(row, text="B-1", width=4, command=lambda: bump("b", -1))
    b_plus = ttk.Button(row, text="B+1", width=4, command=lambda: bump("b", 1))
    b_minus.pack(side="left")
    b_plus.pack(side="left")
    adjust_buttons = [a_minus, a_plus, b_minus, b_plus]

    ttk.Label(row, textvariable=clock_var, foreground="#b8860b", width=5).pack(
        side="left", padx=(10, 4)
    )
    finish_button = ttk.Button(row, text="Finish")
    finish_button.pack(side="left")

    def finish():
        try:
            tournament.complete_match(match)
        except InvalidMatchTransitionError:
            messagebox.showerror("Scores tied", "Scores are tied; adjust one team before finishing.")
            for button in adjust_buttons:
                button.state(["!disabled"])
            return
        on_update()

    finish_button.configure(command=finish)
    _run_clock(row, adjust_buttons, clock_var, MATCH_CLOCK_SECONDS)


def _run_clock(row, adjust_buttons, clock_var, seconds_left):
    if not row.winfo_exists():
        return
    minutes, seconds = divmod(seconds_left, 60)
    clock_var.set(f"{minutes}:{seconds:02d}")
    if seconds_left <= 0:
        for button in adjust_buttons:
            button.state(["disabled"])
        return
    row.after(1000, lambda: _run_clock(row, adjust_buttons, clock_var, seconds_left - 1))
