from dataclasses import dataclass
from .BaseObject import BaseObject


@dataclass
class Instance(BaseObject):
    _serialize_slots = ["name", "location"]
    _write_one_line = True

    name: str
    location: dict = None
    # guides: Guide[]
