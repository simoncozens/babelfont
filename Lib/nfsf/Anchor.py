from dataclasses import dataclass
from .BaseObject import BaseObject

@dataclass
class Anchor(BaseObject):
  _serialize_slots = ["x", "y", "name"]

  x: int
  y: int
  name: str
