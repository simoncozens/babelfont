from babelfont import Axis, Glyph
from io import BytesIO

def test_propagate_format_specific():
    a = Axis(name="Weight", tag="wght", _="Hello")
    assert a._ == "Hello"
    assert a._formatspecific == "Hello"

def test_write_a_negative():
    g = Glyph(name="_test", exported=False)
    s = BytesIO()
    g.write(s)
    assert "exported" in s.getvalue().decode()

