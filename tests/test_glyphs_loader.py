import pytest
from babelfont.glyph import Glyph
from babelfont.layer import Layer
from babelfont.font import Font
import babelfont.convertors.glyphs as glyphs
import glyphsLib


def test_gslayer_load():
  testfile = glyphsLib.GSFont("tests/data/Test1.glyphs")
  a = testfile.glyphs[0].layers[0]
  a_layer = glyphs._load_gslayer(a,None)
  assert(isinstance(a_layer, Glyph))
  assert(len(a_layer.contours) == 2)
  assert(len(a_layer.contours[0].points) == 8)
  assert(len(a_layer.contours[1].points) == 4)
  assert(a_layer.contours[0].points[0].x == 345)
  assert(a_layer.contours[0].points[0].y == 700)
  assert(a_layer.leftMargin == 25)
  assert(a_layer.rightMargin == 25)
  assert(a_layer.bounds == (25, 0, 505, 700))
  assert(a_layer.width == 530)

  b = testfile.glyphs[1].layers[0]
  b_layer = glyphs._load_gslayer(b, None)
  assert(isinstance(b_layer, Glyph))
  assert(len(b_layer.contours) == 3)
  assert(b_layer.leftMargin == 65)
  assert(b_layer.rightMargin == 35)

def test_font_load():
  font = glyphs.open("tests/data/Test1.glyphs")
  assert(isinstance(font, Font))
  assert(isinstance(font.defaultLayer, Layer))
  assert(font.defaultLayer.keys() == {"A":1,"B":1, "i":1, "idotless": 1, "dotaccentcomb": 1}.keys())
