from babelfont import load
from babelfont.fontFilters.rename import rename_glyphs


def test_rename():
    font = load("tests/data/NotoSerifMakasar-Regular.ufo")
    assert "uni11EF0" in font.features.to_fea()
    rename_glyphs(
        font, {"mapping": {"uni11EF0": "sa-makasar", "uni11EF3": "iVowel-makasar"}}
    )
    assert "sa-makasar" in font.features.to_fea()
    assert (
        "markClass iVowel-makasar <anchor -280 622> @_MARKCLASS_0_lookup_0;"
        in font.features.to_fea()
    )
    assert "sa-makasar" in font.glyphs
    assert "uni11EF0" not in font.glyphs


def test_rename_production():
    font = load("tests/data/GlyphsFileFormatv3.glyphs")
    rename_glyphs(font, {"production": True})
    assert "Smily" not in font.glyphs
    assert "someSmily" in font.glyphs
