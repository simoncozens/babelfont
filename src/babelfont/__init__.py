from babelfont.Anchor import Anchor
from babelfont.Axis import Axis
from babelfont.BaseObject import Color, I18NDictionary, Position
from babelfont.convertors import BaseConvertor, Convert
from babelfont.Features import Features
from babelfont.Font import Font
from babelfont.Glyph import Glyph
from babelfont.Guide import Guide
from babelfont.Instance import Instance
from babelfont.Layer import Layer
from babelfont.Master import Master
from babelfont.Names import Names
from babelfont.Node import Node
from babelfont.Shape import Shape, Transform

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
    "I18NDictionary",
    "Convert",
    "BaseConvertor",
    "Features",
    "load",
]


def load(filename):
    return Convert(filename).load()
