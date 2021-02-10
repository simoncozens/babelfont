from dataclasses import dataclass, field
from .BaseObject import BaseObject
from .Guide import Guide

@dataclass
class _MasterFields:
    name: str
    id: str = field(repr=False)
    location: dict = None
    guides: [Guide] = field(default_factory=list, repr=False, metadata={"separate_items": True})
    metrics: dict = field(default_factory=dict, repr=False)
    kerning: dict = field(default=None, repr=False, metadata={"separate_items": True})
    font: object = field(default=None, repr=False, metadata={"python_only": True})

@dataclass
class Master(BaseObject, _MasterFields):
    """A font master.

    Attributes:
        name (str): The user-facing master name.
        id (str): An internal identifier for the master.
        location (dict): A dictionary locating this master by mapping axis
            name to designspace location.
        guides ([Guide]): A list of master-level guidelines
        metrics (dict): The master's metrics.
        font (Font): The font that this master belongs to.
    """

    CORE_METRICS = ["xHeight", "capHeight", "ascender", "descender"]

    def get_glyph_layer(self, glyphname):
        g = self.font.glyphs[glyphname]
        for layer in g.layers:
            if layer._master == self.id:
                return layer

    @property
    def normalized_location(self):
        return { a.tag: a.normalize_value(self.location[a.name]) for a in self.font.axes }

    @property
    def xHeight(self):
        return self.metrics.get("xHeight", 0)

    @property
    def capHeight(self):
        return self.metrics.get("capHeight", 0)

    @property
    def ascender(self):
        return self.metrics.get("ascender", 0)

    @property
    def descender(self):
        return self.metrics.get("descender", 0)
