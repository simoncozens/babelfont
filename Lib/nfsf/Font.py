from dataclasses import dataclass, field
from datetime import datetime
from .BaseObject import BaseObject
from .Glyph import GlyphList
from .Axis import Axis
from .Instance import Instance
from .Master import Master
from pathlib import Path
from .Names import Names
import functools

@dataclass
class _FontFields:
    upm: int = 1000
    version: tuple = (1,0)
    axes: [Axis] = field(default_factory=list, metadata={"separate_items": True})
    instances: [Instance] = field(default_factory=list, metadata={"separate_items": True})
    masters: [Master] = field(default_factory=list, metadata={"separate_items": True})
    glyphs: GlyphList = field(default_factory=GlyphList, metadata={"skip_serialize": True})
    note: str = None
    date: datetime = None
    names: Names = field(default_factory=Names, metadata={"skip_serialize": True})


@dataclass
class Font(_FontFields, BaseObject):

    def __repr__(self):
        return "<Font '%s' (%i masters)>" % (self.names.familyName.get_default(), len(self.masters))

    def export(self, filename, **kwargs):
        from .convertors import Convert
        return Convert(filename).save(self, **kwargs)

    def save(self, pathname):
        path = Path(pathname)
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "info.json", "wb") as f:
            self.write(stream=f)

        with open(path / "names.json", "wb") as f:
            self._write_value(f, "glyphs", self.names)

        with open(path / "glyphs.json", "wb") as f:
            for g in self.glyphs:
                glyphpath = path / "glyphs"
                glyphpath.mkdir(parents=True, exist_ok=True)
                with open(
                    path / g.nfsf_filename, "wb"
                ) as f2:
                    g._write_value(f2, "layers", g.layers)
            self._write_value(f, "glyphs", self.glyphs)

    def master(self, mid):
        return self._master_map[mid]

    @property
    def default_master(self):
        default_loc = { a.name: a.default for a in self.axes }
        for m in self.masters:
            if m.location == default_loc:
                return m


    @functools.cached_property
    def _master_map(self):
        return { m.id: m for m in self.masters }

    @functools.cached_property
    def unicode_map(self):
        unicodes = {}
        for g in self.glyphs:
            if not g.codepoints:
                continue
            for u in g.codepoints:
                unicodes[u] = g.name
        return unicodes

