from dataclasses import dataclass, field
from datetime import datetime
from .BaseObject import BaseObject, OTValue
from .Glyph import GlyphList
from .Axis import Axis
from .Instance import Instance
from .Master import Master
from pathlib import Path
from .Names import Names
import functools
from fontTools.varLib.models import VariationModel
from fontFeatures import FontFeatures
import fontFeatures


@dataclass
class _FontFields:
    upm: int = field(default=1000, metadata={"description": "The font's units per em."})
    version: (int, int) = field(
        default=(1, 0),
        metadata={
            "description": "Font version number as a tuple of integers (major, minor).",
            "json_type": "[int,int]",
        },
    )
    axes: [Axis] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of axes, in the case of variable/multiple master font. May be empty.",
        },
    )
    instances: [Instance] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of named/static instances.",
        },
    )
    masters: [Master] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of the font's masters.",
        },
    )
    glyphs: GlyphList = field(
        default_factory=GlyphList,
        metadata={
            "skip_serialize": True,
            "separate_items": True,
            "json_type": "[dict]",
            "json_location": "glyphs.json",
            "description": """A list of all glyphs supported in the font.

The `GlyphList` structure in the Python object is a dictionary with array-like
properties (or you might think of it as an array with dictionary-like properties)
containing [`Glyph`](Glyph.html) objects. The `GlyphList` may be iterated
directly, and may be appended to, but may also be used to index a `Glyph` by
its name. This is generally what you want:

```Python

for g in font.glyphs:
    assert isinstance(g, Glyph)

font.glyphs.append(newglyph)

glyph_ampersand = font.glyphs["ampersand"]
```
            """,
        },
    )
    note: str = field(
        default=None,
        metadata={"description": "Any user-defined textual note about this font."},
    )
    date: datetime = field(
        default_factory=datetime.now,
        metadata={
            "description": """The font's date. When writing to NFSF-JSON, this
should be stored in the format `%Y-%m-%d %H:%M:%S`. *If not provided, defaults
to the current date/time*.""",
            "json_type": "str",
        },
    )
    names: Names = field(default_factory=Names, metadata={"skip_serialize": True})
    customOpenTypeValues: [OTValue] = field(
        default_factory=list,
        metadata={
            "description": "Any values to be placed in OpenType tables on export to override defaults"
        },
    )
    features: FontFeatures = field(default_factory=FontFeatures, metadata={
        "skip_serialize": True,
        "description": "A representation of the font's OpenType features"
        })


@dataclass
class Font(_FontFields, BaseObject):
    """Represents a font, with one or more masters."""

    def __repr__(self):
        return "<Font '%s' (%i masters)>" % (
            self.names.familyName.get_default(),
            len(self.masters),
        )

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
                with open(path / g.nfsf_filename, "wb") as f2:
                    g._write_value(f2, "layers", g.layers)
            self._write_value(f, "glyphs", self.glyphs)

    def master(self, mid):
        return self._master_map[mid]

    @functools.cached_property
    def default_master(self):
        default_loc = {a.tag: a.map_forward(a.default) for a in self.axes}
        for m in self.masters:
            if m.location == default_loc:
                return m

    @functools.cached_property
    def _master_map(self):
        return {m.id: m for m in self.masters}

    @functools.cached_property
    def unicode_map(self):
        unicodes = {}
        for g in self.glyphs:
            if not g.codepoints:
                continue
            for u in g.codepoints:
                if u:
                    unicodes[u] = g.name
        return unicodes

    def variation_model(self):
        return VariationModel(
            [m.normalized_location for m in self.masters],
            axisOrder=[a.tag for a in self.axes],
        )
