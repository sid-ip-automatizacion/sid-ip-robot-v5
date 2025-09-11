
"""
wo_timers.py
-------------
Manages countdown timers for Work Orders, updating a Tkinter-based table.
All GUI updates are executed via Tk 'after' callbacks to remain in the main thread.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Callable

@dataclass
class _TimerCtx:
    wo_id: str
    remaining_seconds: int
    after_id: Optional[str] = None

class WorkOrderTimers:
    """Manage multiple per-WO countdown timers using Tk's 'after'.
    - No threads are used for the countdown itself; everything runs through .after().
    - Thread-safe stop/start via a lock if external threads request timer changes.
    """
    def __init__(self, tk_root, table_adapter, on_expire: Optional[Callable[[str], None]] = None):
        """
        Args:
            tk_root: the Tk root or any widget supporting .after()
            table_adapter: an object exposing:
                - set_cell(wo_id, column, value)
                - set_state(wo_id, new_state)
                - has_row(wo_id) -> bool
            on_expire: optional callback(wo_id) called when a timer hits 0.
        """
        self.root = tk_root
        self.table = table_adapter
        self.on_expire = on_expire
        self._timers: Dict[str, _TimerCtx] = {}
        self._lock = threading.Lock()

    def start(self, wo_id: str, minutes: int):
        """Start or restart a timer for a WO.
        If a timer already exists, it is cancelled and restarted.
        """
        seconds = max(0, int(minutes)) * 60
        with self._lock:
            self._cancel_locked(wo_id)
            ctx = _TimerCtx(wo_id=wo_id, remaining_seconds=seconds)
            self._timers[wo_id] = ctx
        # Set initial visual time (in minutes)
        self._update_time_visual(wo_id, seconds)
        self._schedule_tick(wo_id)

    def cancel(self, wo_id: str):
        """Cancel an active timer (if any) for the given WO."""
        with self._lock:
            self._cancel_locked(wo_id)

        # Reset the visual time to 0 in GUI thread
        self.root.after(0, lambda: self.table.set_cell(wo_id, "time_min", "0"))

    def cancel_all(self):
        """Cancel all timers (used by Clear/reset)."""
        with self._lock:
            for wid in list(self._timers.keys()):
                self._cancel_locked(wid)
            self._timers.clear()

    # ---------------- internal ----------------

    def _cancel_locked(self, wo_id: str):
        ctx = self._timers.get(wo_id)
        if not ctx:
            return
        if ctx.after_id is not None:
            try:
                self.root.after_cancel(ctx.after_id)
            except Exception:
                pass
        self._timers.pop(wo_id, None)

    def _schedule_tick(self, wo_id: str):
        with self._lock:
            ctx = self._timers.get(wo_id)
            if not ctx:
                return  # cancelled
            # Schedule next tick (1s) in the mainloop
            ctx.after_id = self.root.after(1000, lambda: self._tick(wo_id))

    def _tick(self, wo_id: str):
        with self._lock:
            ctx = self._timers.get(wo_id)
            if not ctx:
                return  # cancelled

            # Decrease time
            ctx.remaining_seconds = max(0, ctx.remaining_seconds - 1)
            seconds = ctx.remaining_seconds

        # Update the GUI (main thread, via after)
        self._update_time_visual(wo_id, seconds)

        if seconds <= 0:
            # Expired: set state to WORKPENDING and cancel
            self.root.after(0, lambda: self.table.set_state(wo_id, "WORKPENDING"))
            # optional hook for server-side update, logging, etc.
            if self.on_expire:
                self.on_expire(wo_id)
            # Remove from dict in a locked section
            with self._lock:
                self._cancel_locked(wo_id)
            return

        # schedule next second
        self._schedule_tick(wo_id)

    def _update_time_visual(self, wo_id: str, seconds: int):
        # Convert seconds to remaining minutes (rounded up; so user sees "counting down")
        minutes = (seconds + 59) // 60  # ceiling to next minute
        self.root.after(0, lambda: self.table.set_cell(wo_id, "time_min", str(minutes)))
