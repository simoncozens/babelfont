from fontParts.base.glyph import BaseGlyph
from babelfont import addUnderscoreProperty


# @addUnderscoreProperty(["name", "unicodes", "width", "height", "lib"])
@addUnderscoreProperty("name")
@addUnderscoreProperty("unicodes")
@addUnderscoreProperty("width")
@addUnderscoreProperty("height")
@addUnderscoreProperty("lib")
class Glyph(BaseGlyph):

    def _autoUnicodes(self):
        # Maybe someday
        self.raiseNotImplementedError()

    def _lenContours(self):
        return len(self._contours)

    def _getContour(self, index, **kwargs):
        return self._contours[index]

    def _appendContour(self, contour, offset=None, **kwargs):
        copy = contour.copy()
        if offset != (0, 0):
            copy.moveBy(offset)
        copy._glyph = self
        self._contours.append(copy)

    def _removeContour(self, index, **kwargs):
        del(self._contours[index])


    def _lenComponents(self):
        return len(self._components)

    def _getComponent(self, index, **kwargs):
        return self._components[index]

    def _removeComponent(self, index, **kwargs):
        del(self._components[index])


    def _lenAnchors(self):
        return len(self._anchors)

    def _getAnchor(self, index, **kwargs):
        return self._anchors[index]

    def _removeAnchor(self, index, **kwargs):
        del(self._anchors[index])

    # Babelfont glyphs have a category, even if fontParts ones don't
    @property
    def category(self):
        return self._category

    def set_category(self, caterory):
        self._category = category
