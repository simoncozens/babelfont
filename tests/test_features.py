from babelfont import Features


def test_parse():
    features = Features.from_fea("""
lookup foobar { 
    sub a by b;                                 
} foobar;
@group_one = [a b c];
@group_two = [@group_one d e f];
feature test {
    sub X by Y;
} test;
lookup foobar2 { sub c by d; } foobar2;
# Prefix: namedPrefix
lookup foobar3 {
    sub e by f;                                 
} foobar3;
feature test {
    pos X Y -150;
} test;
""")
    assert "group_one" in features.classes
    assert features.classes["group_one"] == ["a", "b", "c"]
    assert features.classes["group_two"] == ["@group_one", "d", "e", "f"]
    assert features.prefixes["anonymous"] == "lookup foobar {\n    sub a by b;\n} foobar;\nlookup foobar2 {\n    sub c by d;\n} foobar2;\n"
    assert len(features.features) == 2
    assert features.prefixes["namedPrefix"] == "lookup foobar3 {\n    sub e by f;\n} foobar3;\n"
    assert features.features[0] == ("test", "    sub X by Y;\n")
    assert features.features[1] == ("test", "    pos X Y -150;\n")
