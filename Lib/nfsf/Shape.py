from dataclasses import dataclass
from .BaseObject import BaseObject, Node


@dataclass
class Shape(BaseObject):
  ref: str = None
  transform: list = None
  nodes: [Node] = None
  closed: bool = True
  direction: int = 1

  _serialize_slots = __annotations__.keys()
