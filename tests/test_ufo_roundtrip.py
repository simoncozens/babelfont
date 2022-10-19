from babelfont import load
import defcon


def test_ufo_load():
    font = load("tests/data/Test1.ufo")
    assert font.unicode_map[ord("A")] == "A"

# Can't save UFO right now
# def test_ufo_roundtrip():
#     font = load("tests/data/Test1.ufo")
#     font.save("tests/data/Test1.roundtrip.ufo")
#     dc1 = defcon.Font("tests/data/Test1.ufo")
#     dc2 = defcon.Font("tests/data/Test1.roundtrip.ufo")
#     assert dc1.getDataForSerialization() == dc2.getDataForSerialization()
