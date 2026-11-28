"""Regression tests for focus-ring state restoration on wrapped controls."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from td2app.ui import ctk_compat


class FakeWidget:
    def __init__(self, border_color="#334455", border_width=3, children=()):
        self.options = {
            "border_color": border_color,
            "border_width": border_width,
        }
        self.children = list(children)
        self.bindings = {}

    def cget(self, key):
        return self.options[key]

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def bind(self, sequence, callback, add=None):
        self.bindings[sequence] = (callback, add)

    def winfo_children(self):
        return self.children


class FocusRingTests(unittest.TestCase):
    def test_focus_ring_covers_children_and_restores_original_border(self):
        child = FakeWidget()
        widget = FakeWidget(border_color="#123456", border_width=4, children=[child])
        with patch.object(ctk_compat, "CTK_AVAILABLE", True), patch.dict(
            ctk_compat._THEME, {"accent": "#ff8a00", "border": "#334455"}
        ):
            ctk_compat._focus_ring(widget)
            for target in (widget, child):
                focus_in, add_in = target.bindings["<FocusIn>"]
                focus_out, add_out = target.bindings["<FocusOut>"]
                self.assertEqual(add_in, "+")
                self.assertEqual(add_out, "+")
                focus_in()
                self.assertEqual(widget.options["border_color"], "#ff8a00")
                self.assertEqual(widget.options["border_width"], 4)
                focus_out()
                self.assertEqual(widget.options["border_color"], "#123456")
                self.assertEqual(widget.options["border_width"], 4)

    def test_focus_ring_is_noop_without_customtkinter(self):
        widget = FakeWidget()
        with patch.object(ctk_compat, "CTK_AVAILABLE", False):
            ctk_compat._focus_ring(widget)
        self.assertEqual(widget.bindings, {})


if __name__ == "__main__":
    unittest.main()
