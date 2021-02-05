from dataclasses import dataclass
from .BaseObject import BaseObject
from .Layer import Layer


class GlyphList(dict):
    def append(self, thing):
        self[thing.name] = thing

    def write(self, stream, indent):
        stream.write(b"[")
        for ix, l in enumerate(self):
            stream.write(b"\n")
            stream.write(b"  " * (indent + 2))
            l.write(stream, indent + 1)
            if ix < len(self) - 1:
                stream.write(b", ")
            else:
                stream.write(b"\n")
        stream.write(b"]")

    def __iter__(self):
        self._n = 0
        self._values = list(self.values())
        return self

    def __next__(self):
        if self._n < len(self._values):
            result = self._values[self._n]
            self._n += 1
            return result
        else:
            raise StopIteration


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
