import tkinter as tk
from tkinter import ttk

from bracketforge import InvalidTournamentError, Scheduler, Team, TournamentFormat

from app.views import render_tournament


class BracketForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BracketForge")
        self.geometry("640x600")
        self.minsize(560, 480)

        self._teams: list[str] = []
        self._scheduler = Scheduler()
        self._tournament = None

        self._build_input_section()
        self._build_result_section()

    def _build_input_section(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        entry_row = ttk.Frame(top)
        entry_row.pack(fill="x")
        self._team_entry = ttk.Entry(entry_row)
        self._team_entry.pack(side="left", fill="x", expand=True)
        self._team_entry.bind("<Return>", lambda _event: self._add_team())
        ttk.Button(entry_row, text="Add Team", command=self._add_team).pack(side="left", padx=(6, 0))

        list_row = ttk.Frame(top)
        list_row.pack(fill="x", pady=(6, 0))
        self._team_listbox = tk.Listbox(list_row, height=5)
        self._team_listbox.pack(side="left", fill="x", expand=True)
        ttk.Button(list_row, text="Remove Selected", command=self._remove_selected_team).pack(
            side="left", padx=(6, 0)
        )

        format_row = ttk.Frame(top)
        format_row.pack(fill="x", pady=(10, 0))
        ttk.Label(format_row, text="Format:").pack(side="left")
        self._format_var = tk.StringVar(value=TournamentFormat.ROUND_ROBIN.value)
        format_menu = ttk.Combobox(
            format_row,
            textvariable=self._format_var,
            values=[fmt.value for fmt in TournamentFormat],
            state="readonly",
        )
        format_menu.pack(side="left", padx=(6, 0))
        ttk.Button(format_row, text="Generate Schedule", command=self._generate).pack(
            side="left", padx=(12, 0)
        )

        self._error_label = ttk.Label(top, foreground="red")
        self._error_label.pack(fill="x", pady=(6, 0))

    def _build_result_section(self):
        container = ttk.Frame(self, padding=(10, 0, 10, 10))
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self._result_frame = ttk.Frame(canvas)

        self._result_frame.bind(
            "<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._result_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _add_team(self):
        name = self._team_entry.get().strip()
        if not name:
            return
        self._teams.append(name)
        self._team_listbox.insert("end", name)
        self._team_entry.delete(0, "end")

    def _remove_selected_team(self):
        selection = self._team_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self._team_listbox.delete(index)
        del self._teams[index]

    def _generate(self):
        self._error_label.configure(text="")
        try:
            teams = [Team(name) for name in self._teams]
            format_ = TournamentFormat(self._format_var.get())
            self._tournament = self._scheduler.generate(teams, format_)
        except InvalidTournamentError as exc:
            self._error_label.configure(text=str(exc))
            return

        self._render()

    def _render(self):
        render_tournament(self._result_frame, self._tournament, on_update=self._render)


def main():
    app = BracketForgeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
