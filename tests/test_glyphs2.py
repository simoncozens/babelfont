from babelfont import load


def test_load_many_axes():
    font = load("tests/data/Glyphs2ManyAxes.glyphs")
    assert font.masters[0].location == {'wght': 100, 'wdth': 100, 'opsz': 12, 'ital': 0}
    assert font.masters[1].location == {'wght': 100, 'wdth': 100, 'opsz': 12, 'ital': 1}
