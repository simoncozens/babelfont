from .BaseObject import BaseObject
from dataclasses import dataclass


@dataclass
class Axis(BaseObject):
    name: str
    tag: str
    min: int = None
    max: int = None
    default: int = None
    _write_one_line = True

    _serialize_slots = ["name", "tag"]
