"""Compatibility bridge; implementation moved to :mod:`td2app.ui.splash`."""
import sys as _sys
from td2app.ui import splash as _implementation
_sys.modules[__name__] = _implementation
