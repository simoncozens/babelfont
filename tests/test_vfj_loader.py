from babelfont import load

def test_load_glyph():
    filename = "tests/data/Castoro Roman.vfj"
    font = load(filename)

    assert len(font.default_master.get_glyph_layer("A").paths[0].nodes) == 50
    assert len(font.default_master.get_glyph_layer("A").paths[1].nodes) == 4

