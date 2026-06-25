"""
Emitter factory and registry.
"""

from .base import Emitter
from .playwright_emitter import PlaywrightEmitter
from .cypress_emitter import CypressEmitter
from .selenium_emitter import SeleniumEmitter

_emitter_registry = {
    "playwright": PlaywrightEmitter,
    "cypress": CypressEmitter,
    "selenium": SeleniumEmitter,
}


def register_emitter(name: str, emitter_class: type) -> None:
    """Register a new emitter."""
    _emitter_registry[name.lower()] = emitter_class


def get_emitter(name: str) -> Emitter:
    """Return an instance of the requested emitter."""
    cls = _emitter_registry.get(name.lower())
    if cls is None:
        available = ", ".join(_emitter_registry.keys())
        raise ValueError(f"Unknown emitter '{name}'. Available: {available}")
    return cls()
