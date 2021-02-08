from dataclasses import dataclass
from .BaseObject import BaseObject
from .Node import Node


@dataclass
class Shape(BaseObject):
    ref: str = None
    transform: list = None
    nodes: [Node] = None
    closed: bool = True
    direction: int = 1

    _serialize_slots = __annotations__.keys()

    _layer = None

    @property
    def is_path(self):
        return not bool(self.ref)

    @property
    def is_component(self):
        return bool(self.ref)

    @property
    def component_layer(self):
        if not self.is_component:
            return None
        return self._layer.master.get_glyph_layer(self.ref)
