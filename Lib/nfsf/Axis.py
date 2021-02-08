from .BaseObject import BaseObject
from dataclasses import dataclass,field
import uuid
from fontTools.varLib.models import normalizeValue



@dataclass
class Axis(BaseObject):
    name: str
    tag: str
    id: str = field(default_factory = lambda : str(uuid.uuid1()), repr=False)
    min: int = None
    max: int = None
    default: int = None

    _write_one_line = True

    def normalize_value(self, value):
        return normalizeValue(value, (self.min, self.default, self.max))
