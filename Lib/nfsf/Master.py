from dataclasses import dataclass
from .BaseObject import BaseObject

@dataclass
class Master(BaseObject):
  _serialize_slots = ["name", "location", "guides", "metrics"]

  name: str
  location: dict = None
  guides: list = None

def __init__(self):
    super().__init__()
