from dataclasses import dataclass
from .BaseObject import BaseObject

@dataclass
class Master(BaseObject):
  name: str
  id: str
  location: dict = None
  guides: list = None
  xHeight: int = None
  capHeight: int = None
  ascender: int = None
  descender: int = None
  kerning: dict = None

  _serialize_slots = __annotations__.keys()
  _separate_items = { "kerning": True }
