import importlib
import pkgutil
from typing import Dict, List

from modes.base import ModeDefinition

_registry: Dict[str, ModeDefinition] = {}
_loaded = False


def _load_all() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    import modes as _pkg
    for _finder, name, _ispkg in pkgutil.iter_modules(_pkg.__path__):
        if name not in ("base", "registry"):
            importlib.import_module(f"modes.{name}")


def register(mode: ModeDefinition) -> None:
    _registry[mode.crew_type] = mode


def get(crew_type: str) -> ModeDefinition:
    _load_all()
    return _registry[crew_type]


def all_modes() -> List[ModeDefinition]:
    _load_all()
    return sorted(_registry.values(), key=lambda m: m.order)


def by_display_name(name: str) -> ModeDefinition:
    _load_all()
    for mode in _registry.values():
        if mode.display_name == name:
            return mode
    raise KeyError(f"No mode with display_name={name!r}")
