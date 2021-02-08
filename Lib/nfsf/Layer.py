from dataclasses import dataclass, field
from functools import cached_property

from fontTools.ufoLib.pointPen import PointToSegmentPen
from fontTools.pens.boundsPen import BoundsPen

from .BaseObject import BaseObject, Color
from .Guide import Guide
from .Anchor import Anchor


@dataclass
class Layer(BaseObject):

    id: str
    width: int
    name: str = None
    _master: str = None
    guides: [Guide] = None
    shapes: list = field(default=None, repr=False)
    anchors: [Anchor] = None
    color: Color = None
    layerIndex: int = 0
    # hints: [Hint]
    _background: str = None
    isBackground: bool = False
    location: [float] = None
    _font: object = None  # Can't type Font because of circularity

    _serialize_slots = [
        "id",
        "width",
        "name",
        "_master",
        "guides",
        "shapes",
        "anchors",
        "color",
        "layerIndex",
        "_background",
        "isBackground",
        "location",
        "bounds",
    ]
    _separate_items = {"shapes": True}

    @property
    def master(self):
        assert self._font
        return self._font.master(self._master)

    @property
    def paths(self):
        return [x for x in self.shapes if x.is_path]

    @property
    def components(self):
        return [x for x in self.shapes if x.is_component]

    def recursiveComponentSet(self):
        mine = set([x.ref for x in self.components])
        theirs = set()
        for c in mine:
            theirs |= self.master.get_glyph_layer(c).recursiveComponentSet()
        return mine | theirs

    def draw(self, pen):
        pen = PointToSegmentPen(pen)
        for path in self.paths:
            pen.beginPath()
            for node in path.nodes:
                pen.addPoint(
                    pt=(node.x, node.y),
                    segmentType=node.pen_type,
                    smooth=node.is_smooth,
                )
            pen.endPath()
        for component in self.components:
            pen.addComponent(component.ref, component.transform)

    @cached_property
    def bounds(self):
        glyphset = {}
        for c in list(self.recursiveComponentSet()):
            glyphset[c] = self.master.get_glyph_layer(c)
        pen = BoundsPen(glyphset)
        self.draw(pen)
        return pen.bounds

    @property
    def lsb(self):
        if not self.bounds:  # Space glyph
            return 0
        return self.bounds[0]

    @property
    def rsb(self):
        if not self.bounds:  # Space glyph
            return 0
        return self.width - self.bounds[2]
