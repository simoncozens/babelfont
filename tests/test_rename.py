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


def test_rename_nested():
    font = load("tests/data/NotoSerifMakasar-Regular.ufo")
    font.features.features = [("ccmp", "lookup foo { sub uni11EF0 by uni11EF3; } foo;")]
    rename_glyphs(
        font, {"mapping": {"uni11EF0": "sa-makasar", "uni11EF3": "iVowel-makasar"}}
    )
    assert "sub sa-makasar by iVowel-makasar;" in font.features.to_fea()


def test_rename_contextual():
    font = load("tests/data/NotoSerifMakasar-Regular.ufo")

    font.features.features = [
        (
            "kern",
            """
    pos uni11EF0 [uni11EF3]' 50;
    """,
        )
    ]
    rename_glyphs(
        font, {"mapping": {"uni11EF0": "sa-makasar", "uni11EF3": "iVowel-makasar"}}
    )
    assert "pos sa-makasar [iVowel-makasar]' 50" in font.features.features[0][1]
