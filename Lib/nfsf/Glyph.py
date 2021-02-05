from dataclasses import dataclass
from .BaseObject import BaseObject
from .Layer import Layer


@dataclass
class Glyph(BaseObject):
    name: str
    category: str = "base"
    codepoint: int = None
    layers: [Layer] = None

    _serialize_slots = ["name", "category", "codepoint"]
    _write_one_line = True

    def __post_init__(self):
        self.layers = []
        self._formatspecific = {}
