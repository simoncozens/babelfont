from babelfont import Babelfont


def test_load():
    _ = Babelfont.open("tests/data/NewFont-Regular.ttf")


def test_load2():
    font = Babelfont.open("tests/data/Nunito-Regular.ttf")
    font.save("tests/data/Nunito-from-ttf.ufo")


def test_load_otf():
    font = Babelfont.open("tests/data/Nunito-Regular.otf")
    font.save("tests/data/Nunito-from-otf.ufo")
