from dataclasses import dataclass
from .BaseObject import BaseObject, Color, Position

@dataclass
class Guide(BaseObject):
  _serialize_slots = ["pos", "name", "color"]

  pos: Position
  name: str = None
  color: Color = None
