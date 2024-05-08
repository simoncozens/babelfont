from babelfont import load


def test_load_open_shape():
    font = load("tests/data/GlyphsFileFormatv3.glyphs")
    assert font.glyphs["A"].layers[1].shapes[0].closed == False


def test_designspace():
    font = load("tests/data/Designspace.glyphs")
    assert len(font.axes) == 1
    assert font.axes[0].name.get_default() == "Weight"
    assert font.axes[0].tag == "wght"
    # Axes values are in userspace units
    assert font.axes[0].minimum == 100
    assert font.axes[0].maximum == 600
    # Master locations are in designspace units
    assert font.masters[0].location == {"wght": 1}
    assert font.masters[1].location == {"wght": 199}
    # Instance locations are in designspace units
    assert font.instances[0].location == {"wght": 1}
    assert font.instances[1].location == {"wght": 7}
