from typing import Optional, List

from dataclasses import dataclass, field
from .BaseObject import BaseObject
from .Layer import Layer
from fontTools.misc.filenames import userNameToFileName
import os


@dataclass
class _GlyphFields:
    name: str
    production_name: Optional[str] = None
    category: str = "base"
    codepoints: List[int] = field(default_factory=list)
    layers: List[Layer] = field(
        default_factory=list, repr=False, metadata={"skip_serialize": True}
    )
    exported: bool = field(default=True, metadata={"serialize_if_false": True})
    direction: str = field(default="LTR", repr=False)


@dataclass
class Glyph(BaseObject, _GlyphFields):
    _write_one_line = True

    @property
    def babelfont_filename(self):
        return os.path.join("glyphs", (userNameToFileName(self.name) + ".nfsglyph"))


class GlyphList(dict):
    def append(self, thing):
        self[thing.name] = thing

    def write(self, stream, indent):
        stream.write(b"[")
        for ix, item in enumerate(self):
            stream.write(b"\n")
            stream.write(b"  " * (indent + 2))
            item.write(stream, indent + 1)
            if ix < len(self) - 1:
                stream.write(b", ")
            else:
                stream.write(b"\n")
        stream.write(b"]")

    def __iter__(self) -> "GlyphList":
        self._n = 0
        self._values = list(self.values())
        return self

    def __next__(self) -> Glyph:
        if self._n < len(self._values):
            result = self._values[self._n]
            self._n += 1
            return result
        else:
            raise StopIteration

