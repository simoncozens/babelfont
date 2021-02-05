from dataclasses import dataclass
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
