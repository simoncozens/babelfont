from .BaseObject import BaseObject
from dataclasses import dataclass
import uuid


@dataclass
class Axis(BaseObject):
    name: str
    tag: str
    id: str = None
    min: int = None
    max: int = None
    default: int = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid1())
        self._formatspecific = {}

    _serialize_slots = __annotations__.keys()
    _write_one_line = True
