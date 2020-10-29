from fontTools.ttLib import TTFont
from babelfont.font import Font
from babelfont.layer import Layer
from babelfont.lib import Lib
from babelfont.glyph import Glyph
from babelfont.point import Point
from babelfont.contour import Contour
from babelfont.component import Component
from babelfont.anchor import Anchor
from copy import copy


def can_handle(filename):
    if not (filename.endswith(".otf") or filename.endswith(".ttf")):
      return False
    font = TTFont(filename)
    return "CFF " in font
