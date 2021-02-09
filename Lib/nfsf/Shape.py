from dataclasses import dataclass
from .BaseObject import BaseObject
from .Node import Node


@dataclass
class _ShapeFields:
    ref: str = None
    transform: list = None
    nodes: [Node] = None
    closed: bool = True
    direction: int = 1

    _layer = None

@dataclass
class Shape(BaseObject, _ShapeFields):
    @property
    def _write_one_line(self):
        return self.is_component

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
