from nfsf import load
import pytest
import os

def data_path(filename):
    path, _ = os.path.split(__file__)
    return os.path.join(path, "data", filename)

def check_equal(one, two):
    with open(one) as f:
        expected = f.read()
    with open(two) as f:
        got = f.read()
    assert expected == got

def test_glyphs3_nfsf_glyphs3(tmp_path):
    original_file = data_path("SimpleTwoAxis3.glyphs")
    tmp_file = os.path.join(tmp_path, "SimpleTwoAxis3.nfsf")
    roundtrip_file = os.path.join(tmp_path, "SimpleTwoAxis3.glyphs")
    f = load(original_file)
    f.save(tmp_file)

    f2 = load(tmp_file)
    f2.export(roundtrip_file, format=3)
    check_equal(original_file, roundtrip_file)

