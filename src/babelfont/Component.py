from dataclasses import dataclass
from .BaseObject import BaseObject


@dataclass
class _ComponentFields:
    name: str
    position: list = None
    transform: list = None


@dataclass
class Component(BaseObject, _ComponentFields):
    _serialize_slots = ["name", "transform"]
