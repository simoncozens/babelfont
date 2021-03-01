from nfsf.Font import Font
from nfsf.Axis import Axis
from nfsf.Glyph import Glyph
from nfsf.Master import Master
from nfsf.Instance import Instance
from nfsf.Guide import Guide
from nfsf.Anchor import Anchor
from nfsf.Layer import Layer
from nfsf.Shape import Shape
from nfsf.Node import Node
from nfsf.Names import Names
from nfsf.BaseObject import Color, Position, OTValue, I18NDictionary
from nfsf.convertors import Convert


def load(filename):
    return Convert(filename).load()
