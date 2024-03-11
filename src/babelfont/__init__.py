from babelfont.Font import Font
from babelfont.Axis import Axis
from babelfont.Glyph import Glyph
from babelfont.Master import Master
from babelfont.Instance import Instance
from babelfont.Guide import Guide
from babelfont.Anchor import Anchor
from babelfont.Layer import Layer
from babelfont.Shape import Shape, Transform
from babelfont.Node import Node
from babelfont.Names import Names
from babelfont.BaseObject import Color, Position, OTValue, I18NDictionary
from babelfont.convertors import Convert, BaseConvertor

__all__ = [
    "Font",
    "Axis",
    "Glyph",
    "Master",
    "Instance",
    "Guide",
    "Anchor",
    "Layer",
    "Shape",
    "Transform",
    "Node",
    "Names",
    "Color",
    "Position",
    "OTValue",
    "I18NDictionary",
    "Convert",
    "BaseConvertor",
    "load",
]


def load(filename):
    return Convert(filename).load()
