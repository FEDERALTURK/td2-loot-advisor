"""Compatibility bridge; implementation moved to :mod:`td2app.ui.ui_theme`."""
import sys as _sys
from td2app.ui import ui_theme as _implementation
_sys.modules[__name__] = _implementation
