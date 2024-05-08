import functools
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fontTools.feaLib.variableScalar import VariableScalar
from fontTools.varLib.models import VariationModel

from .Axis import Axis, Tag
from .BaseObject import BaseObject, IncompatibleMastersError, Number
from .Features import Features
from .Glyph import GlyphList
from .Instance import Instance
from .Master import Master
from .Names import Names

log = logging.getLogger(__name__)


@dataclass
class _FontFields:
    upm: int = field(default=1000, metadata={"description": "The font's units per em."})
    version: Tuple[int, int] = field(
        default=(1, 0),
        metadata={
            "description": "Font version number as a tuple of integers (major, minor).",
            "json_type": "[int,int]",
        },
    )
    axes: List[Axis] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of axes, in the case of variable/multiple master font. May be empty.",
        },
    )
    instances: List[Instance] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of named/static instances.",
        },
    )
    masters: List[Master] = field(
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
            "description": """The font's date. When writing to Babelfont-JSON, this
should be stored in the format `%Y-%m-%d %H:%M:%S`. *If not provided, defaults
to the current date/time*.""",
            "json_type": "str",
        },
    )
    names: Names = field(default_factory=Names, metadata={"skip_serialize": True})
    custom_opentype_values: Dict[Tuple[str, str], Any] = field(
        default_factory=dict,
        metadata={
            "description": "Any values to be placed in OpenType tables on export to override defaults; these must be font-wide. Metrics which may vary by master should be placed in the `metrics` field of a Master."
        },
    )
    features: Features = field(
        default_factory=Features,
        metadata={
            "description": "A representation of the font's OpenType features",
        },
    )
    first_kern_groups: Dict[str, List[str]] = field(
        default_factory=dict,
        metadata={
            "description": "A dictionary of kerning groups, where the key is the group name and the value is a list of glyph names in the group."
        },
    )
    second_kern_groups: Dict[str, List[str]] = field(
        default_factory=dict,
        metadata={
            "description": "A dictionary of kerning groups, where the key is the group name and the value is a list of glyph names in the group."
        },
    )


@dataclass
class Font(_FontFields, BaseObject):
    """Represents a font, with one or more masters."""

    def __repr__(self):
        return "<Font '%s' (%i masters)>" % (
            self.names.familyName.get_default(),
            len(self.masters),
        )

    def save(self, filename: str, **kwargs):
        """Save the font to a file. The file type is determined by the extension.
        Any additional keyword arguments are passed to the save method of the
        appropriate converter."""
        from .convertors import Convert

        return Convert(filename).save(self, **kwargs)

    def master(self, mid: str) -> Optional[Master]:
        """Locates a master by its ID. Returns `None` if not found."""
        return self._master_map[mid]

    def map_forward(self, location: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from userspace to designspace."""
        location2 = dict(location)
        for a in self.axes:
            if a.tag in location2:
                location2[a.tag] = a.map_forward(location2[a.tag])
        return location2

    def map_backward(self, location: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from designspace to userspace."""
        location2 = dict(location)
        for a in self.axes:
            if a.tag in location2:
                location2[a.tag] = a.map_backward(location2[a.tag])
        return location2

    def userspace_to_designspace(self, v: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from userspace to designspace."""
        return self.map_forward(v)

    def designspace_to_userspace(self, v: dict[Tag, Number]) -> dict[Tag, Number]:
        """Map a location (dictionary of `tag: number`) from designspace to userspace."""
        return self.map_backward(v)

    @functools.cached_property
    def default_master(self) -> Master:
        """Return the default master. If there is only one master, return it.
        If there are multiple masters, return the one with the default location.
        If there is no default location, raise an error."""
        default_loc = {a.tag: a.userspace_to_designspace(a.default) for a in self.axes}
        for m in self.masters:
            if m.location == default_loc:
                return m
        if len(self.masters) == 1:
            return self.masters[0]
        raise ValueError("Could not determine default master")

    @functools.cached_property
    def _master_map(self):
        return {m.id: m for m in self.masters}

    @functools.cached_property
    def unicode_map(self) -> Dict[int, str]:
        """Return a dictionary mapping Unicode codepoints to glyph names."""
        unicodes = {}
        for g in self.glyphs:
            for u in g.codepoints:
                if u is not None:
                    unicodes[u] = g.name
        return unicodes

    def variation_model(self) -> VariationModel:
        """Return a `fontTools.varLib.models.VariationModel` object representing
        the font's axes and masters. This is used for generating variable fonts."""
        return VariationModel(
            [m.normalized_location for m in self.masters],
            axisOrder=[a.tag for a in self.axes],
        )

    @functools.cached_property
    def _all_kerning(self):
        all_keys = [set(m.kerning.keys()) for m in self.masters]
        kerndict = {}
        for left, right in list(set().union(*all_keys)):
            kern = VariableScalar()
            kern.axes = self.axes
            for m in self.masters:
                thiskern = m.kerning.get((left, right), 0)
                if (left, right) not in m.kerning:
                    log.debug(
                        "Master %s did not define a kern pair for (%s, %s), using 0"
                        % (m.name.get_default(), left, right)
                    )
                kern.add_value(m.location, thiskern)
            kerndict[(left, right)] = kern
        return kerndict

    @functools.cached_property
    def _all_anchors(self):
        _all_anchors_dict = {}
        for g in sorted(self.glyphs.keys()):
            default_layer = self.default_master.get_glyph_layer(g)
            has_mark = None
            for a in default_layer.anchors_dict.keys():
                if a[0] == "_":
                    if has_mark:
                        log.warning(
                            "Glyph %s tried to be in two mark classes (%s, %s). The first one will win."
                            % (g, has_mark, a)
                        )
                        continue
                    has_mark = a
                if a not in _all_anchors_dict:
                    _all_anchors_dict[a] = {}
                _all_anchors_dict[a][g] = self.get_variable_anchor(g, a)
        return _all_anchors_dict

    def get_variable_anchor(
        self, glyph, anchorname
    ) -> Tuple[VariableScalar, VariableScalar]:
        """Return a tuple of `VariableScalar` objects representing the x and y
        coordinates of the anchor on the given glyph. The `VariableScalar` objects
        are indexed by master location. If the anchor is not found on some master,
        raise an `IncompatibleMastersError`."""
        x_vs = VariableScalar()
        x_vs.axes = self.axes
        y_vs = VariableScalar()
        y_vs.axes = self.axes
        for ix, m in enumerate(self.masters):
            layer = m.get_glyph_layer(glyph)
            if anchorname not in layer.anchors_dict:
                raise IncompatibleMastersError(
                    "Anchor %s not found on glyph %s in master %s"
                    % (anchorname, glyph, m)
                )
            anchor = m.get_glyph_layer(glyph).anchors_dict[anchorname]
            x_vs.add_value(self.map_forward(m.location), anchor.x)
            y_vs.add_value(self.map_forward(m.location), anchor.y)
        return (x_vs, y_vs)

    def exported_glyphs(self) -> List[str]:
        """Return a list of glyph names that are marked for export."""
        return [g.name for g in self.glyphs if g.exported]
