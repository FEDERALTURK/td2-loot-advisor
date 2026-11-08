"""Safe runtime plan for the desktop helper.

The plan only receives UI/game-window focus already discovered by the app.  It
does not inspect processes, game memory, files, GPU state, or network traffic.
"""
from dataclasses import dataclass
from collections.abc import Mapping


@dataclass(frozen=True)
class RuntimePlan:
    """Read-only policy consumed by passive OCR and translation loops."""

    state: str
    passive_capture: bool
    passive_translation: bool
    wait_s: float


def plan(settings, *, game_focused=False, app_hidden=False):
    """Return a bounded passive-work policy without modifying saved settings."""
    settings = settings if isinstance(settings, Mapping) else {}
    focused = bool(game_focused)
    only_game_active = bool(settings.get("only_game_active", True))

    if focused:
        return RuntimePlan(
            "game_focus_tray" if app_hidden else "game_focus",
            passive_capture=True,
            passive_translation=True,
            wait_s=0.0,
        )
    if only_game_active:
        # A bounded wait avoids busy polling while another application is focused.
        return RuntimePlan("background", passive_capture=False, passive_translation=False, wait_s=1.5)
    return RuntimePlan("desktop", passive_capture=True, passive_translation=True, wait_s=0.0)
