from babelfont.ttf.font import TTFont,TTLayer
from babelfont.otf.glyph import OTGlyph

class OTLayer(TTLayer):
    glyphClass = OTGlyph

class OTFont(TTFont):
    layerClass = OTLayer
