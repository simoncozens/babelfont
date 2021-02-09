from dataclasses import dataclass
from .BaseObject import BaseObject


@dataclass
class _AnchorFields():
    x: int
    y: int
    name: str

@dataclass
class Anchor(BaseObject, _AnchorFields):
    pass
