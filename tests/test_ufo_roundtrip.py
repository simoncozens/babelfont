import pytest
from babelfont import Babelfont
import plistlib
import subprocess
from io import BytesIO
import defcon


def test_roundtrip():
  font = Babelfont.open("tests/data/Test1.ufo")
  Babelfont.save(font, "tests/data/Test1.roundtrip.ufo")
  dc1 = defcon.Font("tests/data/Test1.ufo")
  dc2 = defcon.Font("tests/data/Test1.roundtrip.ufo")
  assert (dc1.getDataForSerialization() == dc2.getDataForSerialization())
