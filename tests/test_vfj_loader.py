from munch import munchify
import json
from babelfont.layer import Layer
from babelfont.convertors.fontlab import _load_glyph
from babelfont import Babelfont

def test_load_glyph():
    filename = "tests/data/Castoro Roman.vfj"
    vfj = munchify(json.load(open(filename, "r"))).font
    master = vfj.masters[0].fontMaster
    l = Layer()
    a = _load_glyph(vfj.glyphs[5], l, master)
    assert len(a.contours[0]) == 20
    assert len(a.contours[1]) == 4

def test_loader():
    filename = "tests/data/Castoro Roman.vfj"
    font = Babelfont.open(filename)
