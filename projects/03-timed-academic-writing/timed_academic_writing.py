"""A small Tkinter timed writing practice tool.

"""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


TOTAL_SECONDS = 10 * 60
WARNING_SECONDS = 2 * 60
WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")


def count_words(text: str) -> int:
    """Count English practice-writing tokens without creating a GUI window."""
    return len(WORD_PATTERN.findall(text))


def format_seconds(seconds: int) -> str:
    """Format a non-negative countdown value as minutes and seconds."""
    minutes, remaining_seconds = divmod(max(0, seconds), 60)
    return f"{minutes}:{remaining_seconds:02d}"


class TimedWritingApp(tk.Tk):
    """Desktop interface for a focused academic writing practice session."""

    COLORS = {
        "navy": "#17366f",
        "blue": "#244c9f",
        "blue_light": "#eef3fb",
        "border": "#c8d0dc",
        "panel": "#f5f7fa",
        "text": "#172033",
        "muted": "#596579",
        "danger": "#b42318",
        "white": "#ffffff",
    }

    PROMPT = (
        "Some people believe that universities should require students to take "
        "at least one course outside their major. Others think students should "
        "focus only on their major requirements. Which view do you agree with? "
        "Explain your opinion using reasons and examples."
    )

    def __init__(self) -> None:
        super().__init__()
        self.remaining = TOTAL_SECONDS
        self.timer_job: str | None = None
        self.is_running = False

        self.title("Timed Academic Writing Practice")
        self.geometry("1100x760")
        self.minsize(760, 600)
        self.configure(background=self.COLORS["panel"])
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._configure_styles()
        self._build_interface()
        self._render_timer()
        self._start_timer()
        self.response.focus_set()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background=self.COLORS["panel"])
        style.configure("White.TFrame", background=self.COLORS["white"])
        style.configure(
            "Top.TFrame", background=self.COLORS["navy"]
        )
        style.configure(
            "Brand.TLabel",
            background=self.COLORS["navy"],
            foreground=self.COLORS["white"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Header.TLabel",
            background=self.COLORS["navy"],
            foreground=self.COLORS["white"],
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "MutedTop.TLabel",
            background=self.COLORS["navy"],
            foreground="#dbe6fb",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Section.TLabel",
            background=self.COLORS["white"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Small.TLabel",
            background=self.COLORS["white"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "TimerLabel.TLabel",
            background=self.COLORS["blue_light"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "Timer.TLabel",
            background=self.COLORS["white"],
            foreground=self.COLORS["text"],
            font=("Consolas", 18, "bold"),
            padding=(12, 4),
        )
        style.configure(
            "Status.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Count.TLabel",
            background=self.COLORS["white"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            padding=(10, 3),
        )
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 6),
        )
        style.configure(
            "Primary.TButton",
            background=self.COLORS["blue"],
            foreground=self.COLORS["white"],
            font=("Segoe UI", 9, "bold"),
            padding=(14, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1d438d"), ("disabled", "#9aa7bd")],
            foreground=[("disabled", "#edf1f7")],
        )

    def _build_interface(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top = ttk.Frame(self, style="Top.TFrame", padding=(22, 14))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="ACADEMIC PRACTICE", style="Brand.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(top, text="Timed Academic Writing", style="Header.TLabel").grid(
            row=0, column=1, padx=28, sticky="w"
        )
        ttk.Label(top, text="Practice session", style="MutedTop.TLabel").grid(
            row=0, column=2, sticky="e"
        )

        status = ttk.Frame(self, style="White.TFrame", padding=(22, 12, 22, 10))
        status.grid(row=1, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Label(
            status,
            text="Write a response to the prompt below.",
            style="Section.TLabel",
        ).grid(row=0, column=0, sticky="w")

        timer_frame = ttk.Frame(status, style="White.TFrame")
        timer_frame.grid(row=0, column=1, sticky="e")
        ttk.Label(timer_frame, text="TIME", style="TimerLabel.TLabel").pack(
            side="left", padx=(0, 6)
        )
        self.timer_value = ttk.Label(timer_frame, text="10:00", style="Timer.TLabel")
        self.timer_value.pack(side="left")

        content = ttk.Frame(self, style="App.TFrame", padding=(22, 0, 22, 0))
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        prompt_panel = ttk.Frame(content, style="White.TFrame", padding=(16, 14))
        prompt_panel.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        prompt_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(prompt_panel, text="Practice Prompt", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            prompt_panel,
            text="Academic Discussion",
            style="Small.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))
        prompt_text = tk.Text(
            prompt_panel,
            height=4,
            wrap="word",
            padx=10,
            pady=8,
            bd=1,
            relief="solid",
            highlightthickness=0,
            background="#fbfcfe",
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10),
        )
        prompt_text.grid(row=2, column=0, sticky="ew")
        prompt_text.insert("1.0", self.PROMPT)
        prompt_text.configure(state="disabled")

        response_panel = ttk.Frame(content, style="White.TFrame", padding=(16, 14))
        response_panel.grid(row=1, column=0, sticky="nsew")
        response_panel.grid_rowconfigure(1, weight=1)
        response_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(response_panel, text="Response", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        editor_frame = ttk.Frame(response_panel, style="White.TFrame")
        editor_frame.grid(row=1, column=0, sticky="nsew")
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        self.response = tk.Text(
            editor_frame,
            wrap="word",
            undo=True,
            padx=12,
            pady=12,
            bd=1,
            relief="solid",
            highlightthickness=0,
            background=self.COLORS["white"],
            foreground=self.COLORS["text"],
            insertbackground=self.COLORS["blue"],
            font=("Segoe UI", 11),
        )
        self.response.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            editor_frame, orient="vertical", command=self.response.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.response.configure(yscrollcommand=scrollbar.set)
        self.response.bind("<KeyRelease>", self._on_response_changed)

        footer = ttk.Frame(self, style="App.TFrame", padding=(22, 12))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(1, weight=1)
        actions = ttk.Frame(footer, style="App.TFrame")
        actions.grid(row=0, column=0, sticky="w")
        ttk.Button(
            actions,
            text="Restart Timer",
            style="Action.TButton",
            command=self._restart_timer,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions,
            text="Save Draft",
            style="Action.TButton",
            command=self._save_draft,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions,
            text="Copy Response",
            style="Action.TButton",
            command=self._copy_response,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions,
            text="Clear",
            style="Action.TButton",
            command=self._clear_response,
        ).pack(side="left")

        self.status_text = tk.StringVar(value="Practice screen ready")
        ttk.Label(footer, textvariable=self.status_text, style="Status.TLabel").grid(
            row=0, column=1, padx=18, sticky="w"
        )
        count_frame = ttk.Frame(footer, style="App.TFrame")
        count_frame.grid(row=0, column=2, sticky="e")
        ttk.Label(count_frame, text="Words", style="Status.TLabel").pack(
            side="left", padx=(0, 8)
        )
        self.word_count = ttk.Label(count_frame, text="0", style="Count.TLabel")
        self.word_count.pack(side="left")

    def _format_time(self) -> str:
        return format_seconds(self.remaining)

    def _render_timer(self) -> None:
        self.timer_value.configure(text=self._format_time())
        if 0 < self.remaining <= WARNING_SECONDS:
            self.timer_value.configure(foreground=self.COLORS["danger"])
        else:
            self.timer_value.configure(foreground=self.COLORS["text"])

    def _start_timer(self) -> None:
        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
        self.is_running = True
        self.timer_job = self.after(1000, self._tick)

    def _tick(self) -> None:
        if not self.is_running:
            return

        self.remaining = max(0, self.remaining - 1)
        self._render_timer()
        if self.remaining == 0:
            self.is_running = False
            self.timer_job = None
            self.response.configure(state="disabled")
            self.status_text.set("Time expired - response locked")
            return

        if self.remaining == WARNING_SECONDS:
            self.status_text.set("Two minutes remaining")
        self.timer_job = self.after(1000, self._tick)

    def _restart_timer(self) -> None:
        self.remaining = TOTAL_SECONDS
        self.response.configure(state="normal")
        self._render_timer()
        self.status_text.set("Timer restarted")
        self._start_timer()
        self.response.focus_set()

    def _on_response_changed(self, _event: tk.Event) -> None:
        self._update_word_count()

    def _update_word_count(self) -> None:
        response = self.response.get("1.0", "end-1c")
        count = count_words(response)
        self.word_count.configure(text=str(count))

    def _clear_response(self) -> None:
        response = self.response.get("1.0", "end-1c")
        if response.strip() and not messagebox.askyesno(
            "Clear response", "Clear the current response?"
        ):
            return
        was_disabled = str(self.response.cget("state")) == "disabled"
        self.response.configure(state="normal")
        self.response.delete("1.0", "end")
        if was_disabled:
            self.response.configure(state="disabled")
        self._update_word_count()
        self.status_text.set("Response cleared")

    def _copy_response(self) -> None:
        response = self.response.get("1.0", "end-1c")
        if not response.strip():
            self.status_text.set("Nothing to copy")
            return
        self.clipboard_clear()
        self.clipboard_append(response)
        self.update()
        self.status_text.set("Response copied to clipboard")

    def _save_draft(self) -> None:
        response = self.response.get("1.0", "end-1c")
        if not response.strip():
            self.status_text.set("Nothing to save")
            return

        path = filedialog.asksaveasfilename(
            title="Save writing draft",
            defaultextension=".txt",
            initialfile="timed_writing_draft.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            Path(path).write_text(response, encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Save failed", str(error))
            return
        self.status_text.set(f"Draft saved: {Path(path).name}")


def main() -> None:
    app = TimedWritingApp()
    app.mainloop()


if __name__ == "__main__":
    main()
