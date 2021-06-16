from babelfont import load


def test_load_open_shape():
    font = load("tests/data/GlyphsFileFormatv3.glyphs")
    assert font.glyphs["A"].layers[1].shapes[0].closed == False
