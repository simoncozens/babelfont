from dataclasses import dataclass, field
from functools import cached_property
from typing import List, Optional

from fontTools.ufoLib.pointPen import (
    PointToSegmentPen,
    SegmentToPointPen,
    AbstractPointPen,
)
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen

from .BaseObject import BaseObject, Color
from .Guide import Guide
from .Anchor import Anchor
from .Node import Node
from .Shape import Shape
import uuid


@dataclass
class _LayerFields:
    width: int = 0
    height: int = 0
    name: str = None
    _master: str = None
    id: str = field(default_factory=lambda: str(uuid.uuid1()))
    guides: [Guide] = field(default_factory=list, repr=False)
    shapes: [Shape] = field(
        default_factory=list, repr=False, metadata={"separate_items": True}
    )
    anchors: [Anchor] = field(default_factory=list, repr=False)
    color: Color = None
    layerIndex: int = 0
    # hints: [Hint]
    background: Optional[str] = field(default=None, repr=False)
    isBackground: bool = field(default=False, repr=False)
    location: [float] = None
    _font: Optional["Font"] = field(
        default=None, repr=False, metadata={"python_only": True}
    )
    _glyph: Optional["Glyph"] = field(
        default=None, repr=False, metadata={"python_only": True}
    )


@dataclass
class Layer(BaseObject, _LayerFields):
    @property
    def master(self):
        assert self._font
        return self._font.master(self._master)

    @property
    def paths(self) -> List[Shape]:
        return [x for x in self.shapes if x.is_path]

    @property
    def components(self) -> List[Shape]:
        return [x for x in self.shapes if x.is_component]

    def recursive_component_set(self):
        mine = set([x.ref for x in self.components])
        theirs = set()
        for c in mine:
            other_layer = self.master.get_glyph_layer(c)
            theirs |= other_layer.recursive_component_set()
        return mine | theirs

    def _background_of(self) -> Optional["Layer"]:
        for layer in self._glyph.layers:
            if layer.background == self.id:
                return layer

    def _background_layer(self) -> Optional["Layer"]:
        if not self.background:
            return
        for layer in self._glyph.layers:
            if layer.id == self.background:
                return layer

    def _nested_component_dict(self) -> dict[str, "Layer"]:
        result = {}
        todo = [x.ref for x in self.components]
        while todo:
            current = todo.pop()
            if current in result:
                continue
            if self.master:
                result[current] = self.master.get_glyph_layer(current)
            else:
                # Find a glyph with same layerid?
                for layer in self._font.glyphs[current].layers:
                    if layer.id == self.id:
                        result[current] = layer
                        break
                if current not in result and self.isBackground:
                    master_layer = self._background_of()
                    if master_layer:
                        master = master_layer._font.master(master_layer._master)
                        result[current] = master.get_glyph_layer(current)
                        if result[current] and result[current]._background_layer():
                            result[current] = result[current]._background_layer()

                if current not in result or not result[current]:
                    raise ValueError("Could not find layer")
            todo.extend([x.ref for x in result[current].components])
        return result

    @cached_property
    def bounds(self):
        glyphset = {}
        for c in list(self.recursive_component_set()):
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

    @property
    def valid(self):
        if not self._font or not self._glyph:
            return False
        return True

    @property
    def anchors_dict(self):
        return {a.name: a for a in self.anchors}

    # Pen protocol support...

    def draw(self, pen):
        pen = PointToSegmentPen(pen)
        return self.drawPoints(pen)

    def drawPoints(self, pen):
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

    def clearContours(self):
        self.shapes = []

    def getPen(self):
        return SegmentToPointPen(LayerPen(self))

    def decompose(self):
        pen = DecomposingRecordingPen(self._nested_component_dict())
        self.draw(pen)
        self.clearContours()
        pen.replay(self.getPen())


class LayerPen(AbstractPointPen):
    def __init__(self, target):
        self.target = target
        self.curPath = []

    def beginPath(self, identifier=None, **kwargs):
        self.curPath = []

    def endPath(self):
        """End the current sub path."""
        self.target.shapes.append(Shape(nodes=self.curPath))

    def addPoint(
        self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs
    ):
        if segmentType == "move":
            return
        ourtype = Node._from_pen_type[segmentType]
        if smooth:
            ourtype = ourtype + "s"
        self.curPath.append(Node(pt[0], pt[1], ourtype))

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        self.target.shapes.append(Shape(ref=baseGlyphName, transform=transformation))
