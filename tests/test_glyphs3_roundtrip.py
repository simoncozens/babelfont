from babelfont import load
import pytest
import os
import re

def data_path(filename):
    path, _ = os.path.split(__file__)
    return os.path.join(path, "data", filename)

def check_equal(one, two):
    with open(one) as f:
        expected = f.read()
    with open(two) as f:
        got = f.read()
    expected_trimmed = re.sub(r"[\s\n]+", "", expected)
    got_trimmed = re.sub(r"[\s\n]+", "", got)
    expected_trimmed = re.sub(r"},{", "},\n{", expected_trimmed)
    got_trimmed = re.sub(r"},{", "},\n{", got_trimmed)

    if expected_trimmed == got_trimmed:
        assert True
    else:
        assert got == expected

@pytest.mark.xfail(reason="Still working on a few things")
@pytest.mark.parametrize("filename", ["SimpleTwoAxis3.glyphs", "GlyphsFileFormatv3.glyphs"])
def test_glyphs3_babelfont_glyphs3(tmp_path, filename):
    original_file = data_path(filename)
    tmp_file = os.path.join(tmp_path, "Roundtrip.babelfont")
    roundtrip_file = os.path.join(tmp_path, "Roundtrip.glyphs")
    f = load(original_file)
    f.save(tmp_file)
    f2 = load(tmp_file)
    # Remove the metrics, reconstruct them
    del(f2._formatspecific["com.glyphsapp"]["metrics"])
    f2.save(roundtrip_file, format=3)
    check_equal(original_file, roundtrip_file)
