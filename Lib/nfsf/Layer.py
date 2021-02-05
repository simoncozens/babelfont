from dataclasses import dataclass

from fontTools.ufoLib.pointPen import PointToSegmentPen

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
    shapes: list = None
    anchors: [Anchor] = None
    color: Color = None
    layerIndex: int = 0
    # hints: [Hint]
    _background: str = None
    isBackground: bool = False
    location: [float] = None
    lsb: int = None
    rsb: int = None

    _serialize_slots = __annotations__.keys()
    _separate_items = {"shapes": True}

    @property
    def paths(self):
        return [x for x in self.shapes if x.is_path]

    @property
    def components(self):
        return [x for x in self.shapes if x.is_component]

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
            pen.addComponent(component.ref, component.transformation)
