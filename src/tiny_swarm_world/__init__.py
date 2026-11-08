"""Compatibility import; implementation lives in the physical core module."""
import importlib.util as _util
from pathlib import Path as _Path
import sys as _sys
_impl = _Path(__file__).resolve().parents[2] / "modules/tsw_core/src" / __name__
_spec = _util.spec_from_file_location(__name__, _impl / "__init__.py", submodule_search_locations=[str(_impl)])
if _spec is None or _spec.loader is None:
    raise ImportError("Physical Tiny Swarm World core package is unavailable.")
_module = _sys.modules[__name__]
_module.__file__ = str(_impl / "__init__.py")
_module.__path__ = [str(_impl)]
_module.__spec__ = _spec
_module.__loader__ = _spec.loader
_spec.loader.exec_module(_module)
