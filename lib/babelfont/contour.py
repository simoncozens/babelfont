from fontParts.base.contour import BaseContour
from babelfont import addUnderscoreProperty


@addUnderscoreProperty("clockwise")
class Contour(BaseContour):
    def _lenPoints(self):
        return len(self._points)

    def _getPoint(self, index, **kwargs):
        return self._points[index]

    def _get_glyph(self):
        return self._glyph

    def _correct_direction(self):
        signedArea = 0
        for ix, p in enumerate(self._points):
            if ix + 1 >= len(self._points):
                nextPt = self._points[0]
            else:
                nextPt = self._points[ix+1]
            signedArea = signedArea + (p.x * nextPt.y - nextPt.x * p.y)
        if signedArea > 0:
            self.clockwise = False
        else:
            self.clockwise = True

    @property
    def identifier(self):
        return None

