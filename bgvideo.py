"""Compatibility bridge; implementation moved to :mod:`td2app.ui.bgvideo`."""
import sys as _sys
from td2app.ui import bgvideo as _implementation
_sys.modules[__name__] = _implementation
