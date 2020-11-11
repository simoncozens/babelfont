from babelfont import Babelfont
from babelfont.glyph import Glyph
from fontTools.ttLib import TTFont
import pytest
import glob
import os


def test_load():
    font = Babelfont.load("tests/data/NewFont-Regular.ttf")
    a_layer = font["A"]
    assert isinstance(a_layer, Glyph)
    assert len(a_layer.contours) == 2
    assert len(a_layer.contours[0].points) == 8
    assert len(a_layer.contours[1].points) == 4
    assert a_layer.contours[0].points[0].x == 345
    assert a_layer.contours[0].points[0].y == 700
    assert a_layer.leftMargin == 25
    assert a_layer.rightMargin == 25
    assert a_layer.bounds == (25, 0, 505, 700)
    assert a_layer.width == 530

    dot = font["uni0307"]
    assert dot.category == "mark"
    assert font.glyphForCodepoint(ord("A")) == "A"

def test_round_trip():
    font = Babelfont.load("tests/data/Nunito-Regular.ttf")
    TTFont("tests/data/Nunito-Regular.ttf").saveXML("tests/data/Nunito-1.ttx")
    font.save("tests/data/Nunito-from-ttf.ttf")
    TTFont("tests/data/Nunito-from-ttf.ttf").saveXML("tests/data/Nunito-2.ttx")

# Torture test
tests = []
for testfile in glob.glob("tests/data/testotfs/*"):
    tests.append(pytest.param(testfile, id=os.path.basename(testfile)))
@pytest.mark.parametrize("fontname", tests)
def test_otfloader(fontname):
    font = Babelfont.load(fontname)

