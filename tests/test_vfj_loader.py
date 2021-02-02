from babelfont import Babelfont

def test_load_glyph():
    filename = "tests/data/Castoro Roman.vfj"
    font = Babelfont.open(filename)

    assert len(font["A"].contours[0]) == 20
    assert len(font["A"].contours[1]) == 4

