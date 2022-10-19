
from babelfont import load, Layer
from fontTools.ttLib import TTFont
import pytest
import glob
import os


def test_load():
    font = load("tests/data/NewFont-Regular.ttf")
    a_layer = font.default_master.get_glyph_layer("A")
    assert isinstance(a_layer, Layer)
    assert len(a_layer.shapes) == 2
    assert len(a_layer.shapes[0].nodes) == 8
    assert len(a_layer.shapes[1].nodes) == 4
    assert a_layer.shapes[0].nodes[0].x == 345
    assert a_layer.shapes[0].nodes[0].y == 700
    assert a_layer.lsb == 25
    assert a_layer.rsb == 25
    assert a_layer.bounds == (25, 0, 505, 700)
    assert a_layer.width == 530

    dot = font.glyphs["uni0307"]
    assert dot.category == "mark"

    assert font.unicode_map[ord("A")] == "A"

    i_layer = font.default_master.get_glyph_layer("i")
    assert isinstance(i_layer, Layer)
    assert len(i_layer.shapes) == 2
    assert i_layer.shapes[0].is_component
    assert i_layer.shapes[0].pos == (0,0)

