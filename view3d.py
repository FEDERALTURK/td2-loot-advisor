"""Compatibility bridge; implementation moved to :mod:`td2app.ui.view3d`."""
import sys as _sys
from td2app.ui import view3d as _implementation
_sys.modules[__name__] = _implementation
