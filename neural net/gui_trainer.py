# Created: 2026-02-23
"""
Kerne Neural Net GUI Trainer
=============================
A standalone GUI application for training the YRE Predictive Transformer.
Features:
  - Live GPU utilisation graph
  - Start / Stop controls
  - Throttle cap slider
  - Epoch counter & progress bar
  - Embedded console log
"""

import sys
import os
import time
import queue
import threading
from pathlib import Path
from datetime import datetime
from collections import deque

# ── stdlib tkinter ──────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ── matplotlib inside Tk ────────────────────────────────────────────────────
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

# ── add the neural net directory to the path ───────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from gpu_trainer import GPUTrainer, _get_gpu_utilization

# ── colour palette (Kerne dark theme) ──────────────────────────────────────
BG        = "#0d0f11"
PANEL     = "#13171c"
BORDER    = "#1e2530"
GREEN     = "#37d097"
RED       = "#ff5555"
YELLOW    = "#f1c40f"
TEXT      = "#e8ecf0"
MUTED     = "#6b7585"
FONT_MONO = ("Consolas", 10)
FONT_UI   = ("Segoe UI", 10)


# ───────────────────────────────────────────────────────────────────────────
# Redirect stdout / stderr into a queue so the GUI can read it
# ───────────────────────────────────────────────────────────────────────────
class _QueueWriter:
    def __init__(self, q: queue.Queue):
        self._q = q
    def write(self, msg: str):
        if msg:
            self._q.put(msg)
    def flush(self):
        pass


# ───────────────────────────────────────────────────────────────────────────
# GPU history buffer
# ───────────────────────────────────────────────────────────────────────────
class GPUHistory:
    MAX_POINTS = 120   # keep ~60 s at 0.5s poll

    def __init__(self):
        self.util  = deque([0.0] * self.MAX_POINTS, maxlen=self.MAX_POINTS)
        self.times = deque(range(-self.MAX_POINTS, 0), maxlen=self.MAX_POINTS)
        self._t0   = 0

    def push(self, val: float):
        self._t0 += 1
        self.util.append(val)
        self.times.append(self._t0)


# ───────────────────────────────────────────────────────────────────────────
# Main Application Window
# ───────────────────────────────────────────────────────────────────────────
class TrainerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Kerne – YRE Neural Net Trainer")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("1100x720")
        self.minsize(900, 600)

        # state
        self._log_q: queue.Queue = queue.Queue()
        self._gpu_hist = GPUHistory()
        self._trainer_thread: threading.Thread | None = None
        self._training_active = False
        self._cap_var  = tk.IntVar(value=75)
        self._epoch_var = tk.IntVar(value=50)

        # redirect stdout → queue
        sys.stdout = _QueueWriter(self._log_q)
        sys.stderr = _QueueWriter(self._log_q)

        self._build_ui()
        self._start_gpu_poll()
        self._start_log_drain()

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # ── top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=(12, 4))

        tk.Label(top, text="KERNE", bg=BG, fg=GREEN,
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(top, text=" YRE Predictive Transformer Trainer", bg=BG,
                 fg=TEXT, font=("Segoe UI", 13)).pack(side="left")

        # ── main content area ─────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=4)

        # LEFT: graph + progress
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        self._build_graph(left)
        self._build_stats_bar(left)

        # RIGHT: controls + console
        right = tk.Frame(body, bg=BG, width=310)
        right.pack(side="right", fill="both", padx=(12, 0))
        right.pack_propagate(False)

        self._build_controls(right)
        self._build_console(right)

    def _build_graph(self, parent):
        panel = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                         highlightthickness=1)
        panel.pack(fill="both", expand=True, pady=(0, 6))

        header = tk.Frame(panel, bg=PANEL)
        header.pack(fill="x", padx=12, pady=(8, 0))
        tk.Label(header, text="GPU Utilisation", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        self._util_label = tk.Label(header, text="0%", bg=PANEL,
                                    fg=GREEN, font=("Segoe UI", 11, "bold"))
        self._util_label.pack(side="right")

        fig = Figure(figsize=(6.5, 3.2), dpi=96, facecolor=PANEL)
        self._ax = fig.add_subplot(111)
        self._ax.set_facecolor("#0a0c0f")
        fig.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.12)

        self._line_util, = self._ax.plot([], [], color=GREEN,  lw=2)
        self._line_cap,  = self._ax.plot([], [], color=YELLOW, lw=1,
                                          linestyle="--", alpha=0.7)
        self._ax.set_ylim(0, 105)
        self._ax.set_ylabel("%", color=MUTED, fontsize=8)
        self._ax.tick_params(colors=MUTED, labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_edgecolor(BORDER)
        self._ax.grid(True, color=BORDER, linewidth=0.5)

        self._canvas = FigureCanvasTkAgg(fig, master=panel)
        self._canvas.get_tk_widget().pack(fill="both", expand=True,
                                          padx=4, pady=4)

        # Start animation polling at 500 ms
        self._anim = animation.FuncAnimation(
            fig, self._update_graph, interval=500, blit=False,
            cache_frame_data=False
        )

    def _build_stats_bar(self, parent):
        bar = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                       highlightthickness=1)
        bar.pack(fill="x", pady=(0, 6))

        stats = [
            ("Epoch",     "_stat_epoch"),
            ("Train Loss","_stat_train"),
            ("Val Loss",  "_stat_val"),
            ("Throttle",  "_stat_throttle"),
            ("GPU Mem",   "_stat_mem"),
            ("Best Loss", "_stat_best"),
        ]
        for i, (label, attr) in enumerate(stats):
            col = tk.Frame(bar, bg=PANEL)
            col.pack(side="left", expand=True, padx=8, pady=6)
            tk.Label(col, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8)).pack()
            lbl = tk.Label(col, text="—", bg=PANEL, fg=TEXT,
                           font=("Segoe UI", 10, "bold"))
            lbl.pack()
            setattr(self, attr, lbl)

        self._progress_var = tk.DoubleVar(value=0)
        pb = ttk.Progressbar(bar, variable=self._progress_var,
                              maximum=100, length=180,
                              style="Kerne.Horizontal.TProgressbar")
        # ttk style
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Kerne.Horizontal.TProgressbar",
                        troughcolor=BG, background=GREEN,
                        bordercolor=BORDER, lightcolor=GREEN,
                        darkcolor=GREEN)
        pb.pack(side="right", padx=10, pady=6)

    def _build_controls(self, parent):
        panel = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                         highlightthickness=1)
        panel.pack(fill="x", pady=(0, 8))

        tk.Label(panel, text="TRAINING CONTROLS", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10,
                                                     pady=(8, 2))

        # Epochs
        row = tk.Frame(panel, bg=PANEL)
        row.pack(fill="x", padx=10, pady=3)
        tk.Label(row, text="Epochs:", bg=PANEL, fg=TEXT,
                 font=FONT_UI, width=14, anchor="w").pack(side="left")
        epochs_spin = tk.Spinbox(row, from_=10, to=500, increment=10,
                                  textvariable=self._epoch_var, width=7,
                                  bg=BORDER, fg=TEXT, insertbackground=TEXT,
                                  buttonbackground=BORDER,
                                  font=FONT_MONO)
        epochs_spin.pack(side="left")

        # GPU cap slider
        row2 = tk.Frame(panel, bg=PANEL)
        row2.pack(fill="x", padx=10, pady=3)
        tk.Label(row2, text="Max GPU Cap:", bg=PANEL, fg=TEXT,
                 font=FONT_UI, width=14, anchor="w").pack(side="left")
        self._cap_disp = tk.Label(row2, text="75%", bg=PANEL,
                                   fg=GREEN, font=FONT_UI)
        self._cap_disp.pack(side="right")
        cap_slider = tk.Scale(panel, from_=10, to=100, orient="horizontal",
                               variable=self._cap_var,
                               bg=PANEL, fg=TEXT, troughcolor=BORDER,
                               highlightthickness=0,
                               command=self._on_cap_change)
        cap_slider.pack(fill="x", padx=10, pady=(0, 6))

        # Start / Stop buttons
        btn_row = tk.Frame(panel, bg=PANEL)
        btn_row.pack(fill="x", padx=10, pady=(2, 10))

        self._btn_start = tk.Button(
            btn_row, text="▶  START TRAINING",
            bg=GREEN, fg="#000000",
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            command=self._start_training
        )
        self._btn_start.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self._btn_stop = tk.Button(
            btn_row, text="■  STOP",
            bg=BORDER, fg=RED,
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            state="disabled",
            command=self._stop_training
        )
        self._btn_stop.pack(side="right", expand=True, fill="x")

    def _build_console(self, parent):
        tk.Label(parent, text="CONSOLE OUTPUT", bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(2, 2))

        self._console = scrolledtext.ScrolledText(
            parent, bg="#090b0e", fg=TEXT,
            font=FONT_MONO, wrap="word",
            insertbackground=TEXT,
            borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER
        )
        self._console.pack(fill="both", expand=True)
        self._console.configure(state="disabled")

    # ── GPU background polling ─────────────────────────────────────────────

    def _start_gpu_poll(self):
        """Poll GPU util every 500ms in background, push to history."""
        def _poll():
            while True:
                util = _get_gpu_utilization()
                if util < 0:
                    util = 0
                self._gpu_hist.push(util)
                time.sleep(0.5)

        t = threading.Thread(target=_poll, daemon=True)
        t.start()

    # ── Graph update (called by FuncAnimation) ─────────────────────────────

    def _update_graph(self, _frame):
        xs = list(self._gpu_hist.times)
        ys = list(self._gpu_hist.util)
        cap = self._cap_var.get()

        self._line_util.set_data(xs, ys)
        self._line_cap.set_data(xs, [cap] * len(xs))

        # colour the line depending on whether we are above the cap
        current = ys[-1] if ys else 0
        self._line_util.set_color(RED if current > cap else GREEN)

        self._ax.set_xlim(xs[0], xs[-1] + 1)

        # update live label in header
        self._util_label.configure(
            text=f"{current:.0f}%",
            fg=(RED if current > cap else GREEN)
        )
        self._canvas.draw_idle()

    # ── Log drain ──────────────────────────────────────────────────────────

    def _start_log_drain(self):
        def _drain():
            try:
                while True:
                    msg = self._log_q.get_nowait()
                    self._console.configure(state="normal")
                    self._console.insert("end", msg)
                    self._console.see("end")
                    self._console.configure(state="disabled")
            except queue.Empty:
                pass
            # Also pull trainer stats if running
            if self._training_active and self._trainer:
                s = self._trainer.training_stats
                ep   = s.get("current_epoch", 0)
                tot  = self._epoch_var.get()
                loss = s.get("epoch_loss", 0)
                best = s.get("best_val_loss", float("inf"))
                thr  = s.get("throttle_sleep_ms", 0)
                mem  = s.get("gpu_memory_used", 0)

                self._stat_epoch.configure(
                    text=f"{ep}/{tot}")
                self._stat_val.configure(text=f"{loss:.4f}")
                self._stat_best.configure(
                    text=("—" if best == float("inf") else f"{best:.4f}"))
                self._stat_throttle.configure(text=f"{thr:.0f}ms")
                self._stat_mem.configure(text=f"{mem:.2f}GB")
                pct = (ep / tot * 100) if tot > 0 else 0
                self._progress_var.set(pct)

            self.after(300, _drain)

        self.after(300, _drain)

    # ── Controls ───────────────────────────────────────────────────────────

    def _on_cap_change(self, val):
        self._cap_disp.configure(text=f"{int(float(val))}%")

    def _start_training(self):
        if self._training_active:
            return

        self._training_active = True
        self._btn_start.configure(state="disabled", bg=BORDER, fg=MUTED)
        self._btn_stop.configure(state="normal")
        self._stat_train.configure(text="—")
        self._stat_val.configure(text="—")
        self._progress_var.set(0)

        epochs = self._epoch_var.get()
        cap    = self._cap_var.get()

        self._trainer = GPUTrainer(max_gpu_util=float(cap))

        def _run():
            try:
                self._trainer.run(epochs=epochs)
            except Exception as e:
                print(f"\n[ERROR] Training failed: {e}\n")
            finally:
                self._training_active = False
                # Re-enable start button from main thread
                self.after(0, self._on_training_done)

        self._trainer_thread = threading.Thread(target=_run, daemon=True)
        self._trainer_thread.start()

    def _stop_training(self):
        if self._trainer:
            self._trainer.stop_flag = True
            print("\n[GUI] Stop requested — finishing current epoch...\n")
        self._training_active = False
        self._on_training_done()

    def _on_training_done(self):
        self._btn_start.configure(state="normal", bg=GREEN, fg="#000000")
        self._btn_stop.configure(state="disabled")
        self._training_active = False
        self._progress_var.set(100 if not self._trainer or
                                self._trainer.training_stats.get(
                                    "current_epoch", 0) ==
                                self._epoch_var.get()
                                else self._progress_var.get())

    # ── On close ───────────────────────────────────────────────────────────
    def on_close(self):
        if self._training_active:
            if not messagebox.askyesno(
                    "Training in progress",
                    "Training is running. Quit anyway?"):
                return
        self.destroy()


# ───────────────────────────────────────────────────────────────────────────
# Entry point
# ───────────────────────────────────────────────────────────────────────────
def main():
    app = TrainerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()