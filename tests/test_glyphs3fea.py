from babelfont.fontFilters.glyphs3fea import _translate
from babelfont import Font, Axis


def test_translate():
    testfont = Font()
    testfont.axes = [Axis(None, "wght", None, 400, 600, 900)]
    code = "sub a by b;\n#ifdef VARIABLE\ncondition 600 < wght < 900; sub dollar by dollar.alt;\n#endif"
    newcode = _translate(code, {"index": 0, "font": testfont, "tag": "rclt"})
    assert (
        newcode
        == "sub a by b;\n;} rclt;conditionset __condition_rclt_1 {wght 600 900;} __condition_rclt_1;variation rclt __condition_rclt_1 { sub dollar by dollar.alt;\n"
    )

    code = "sub a by b;\n#ifdef VARIABLE\ncondition wght < 900; sub dollar by dollar.alt;\n#endif"
    newcode = _translate(code, {"index": 0, "font": testfont, "tag": "rclt"})
    assert (
        newcode
        == "sub a by b;\n;} rclt;conditionset __condition_rclt_1 {wght 400 900;} __condition_rclt_1;variation rclt __condition_rclt_1 { sub dollar by dollar.alt;\n"
    )
