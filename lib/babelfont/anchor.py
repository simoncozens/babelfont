from fontParts.base.anchor import BaseAnchor
from babelfont import addUnderscoreProperty


@addUnderscoreProperty("name")
@addUnderscoreProperty("color")
@addUnderscoreProperty("x")
@addUnderscoreProperty("y")
class Anchor(BaseAnchor):
    pass
