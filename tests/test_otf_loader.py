from babelfont import Babelfont
from babelfont.glyph import Glyph


def test_load():
    font = Babelfont.open("tests/data/NewFont-Regular.ttf")
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

def test_load2():
    font = Babelfont.open("tests/data/Nunito-Regular.ttf")
    # font.save("tests/data/Nunito-from-ttf.ufo")


def test_load_otf():
    font = Babelfont.open("tests/data/Nunito-Regular.otf")
    # font.save("tests/data/Nunito-from-otf.ufo")
