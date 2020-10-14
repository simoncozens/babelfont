from fontParts.base.layer import BaseLayer
from babelfont import addUnderscoreProperty
from babelfont.glyph import Glyph

@addUnderscoreProperty("name")
@addUnderscoreProperty("lib")
@addUnderscoreProperty("glyphs")
class Layer(BaseLayer):
    def keys(self):
        return self._glyphs.keys()
    pass
