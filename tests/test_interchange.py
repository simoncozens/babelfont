from babelfont import Babelfont


# Just testing that it works at all.


def test_ufo_to_glyphs():
    font = Babelfont.open("tests/data/Test1.ufo")
    Babelfont.save(font, "tests/data/Test1-from-ufo.glyphs")


def test_glyphs_to_ufo():
    font = Babelfont.open("tests/data/Test1.glyphs")
    Babelfont.save(font, "tests/data/Test1-from-glyphs.ufo")
