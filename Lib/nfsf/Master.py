from dataclasses import dataclass, field
from .BaseObject import BaseObject
from .Guide import Guide


@dataclass
class Master(BaseObject):
    """A font master.

    Attributes:
        name (str): The user-facing master name.
        id (str): An internal identifier for the master.
        location (dict): A dictionary locating this master by mapping axis
            name to designspace location.
        guides ([Guide]): A list of master-level guidelines
        xHeight (int): The x height of this master, in font units.
        capHeight (int): The cap height of this master, in font units.
        ascender (int): The ascender of this master, in font units.
        descender (int): The descender of this master, in font units.
        font (Font): The font that this master belongs to.
    """

    name: str
    id: str
    location: dict = None
    guides: [Guide] = None
    xHeight: int = None
    capHeight: int = None
    ascender: int = None
    descender: int = None
    kerning: dict = field(default=None, metadata={"separate_items": True})
    font: object = field(default=None, repr=False, metadata={"skip_serialize": True})

    def get_glyph_layer(self, glyphname):
        g = self.font.glyphs[glyphname]
        for layer in g.layers:
            if layer._master == self.id:
                return layer
