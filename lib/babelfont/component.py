from fontParts.base.component import BaseComponent
from babelfont import addUnderscoreProperty
from babelfont.glyph import Glyph


@addUnderscoreProperty("baseGlyph")
@addUnderscoreProperty("transformation")
class Component(BaseComponent):
    pass
    # XXX _set_index
