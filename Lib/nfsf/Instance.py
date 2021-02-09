from dataclasses import dataclass
from .BaseObject import BaseObject


@dataclass
class _InstanceFields:
    name: str
    location: dict = None

@dataclass
class Instance(BaseObject, _InstanceFields):
    _write_one_line = True
