from fontParts.base.contour import BaseContour


class Contour(BaseContour):
    def _lenPoints(self):
        return len(self._points)

    def _getPoint(self, index, **kwargs):
        return self._points[index]

    def _get_glyph(self):
        return self._glyph

    @property
    def identifier(self):
        return None

