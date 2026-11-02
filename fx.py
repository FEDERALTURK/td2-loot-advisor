"""Compatibility bridge; implementation moved to :mod:`td2app.ui.fx`."""
import sys as _sys
from td2app.ui import fx as _implementation
_sys.modules[__name__] = _implementation
