import glyphsLib
from babelfont.font import Font
from babelfont.layer import Layer
from babelfont.lib import Lib
from babelfont.glyph import Glyph
from babelfont.point import Point
from babelfont.contour import Contour
from babelfont.component import Component
from babelfont.anchor import Anchor


def can_handle(filename):
    return filename.endswith(".glyphs")


def open(filename, master=None):
    gsfont = glyphsLib.GSFont(filename)
    gsmaster = None
    if master is None:
        gsmaster = gsfont.masters[0]
    else:
        for m in gsfont.masters:
            if m.name == master:
                gsmaster = m
                break
        if not gsmaster:
            raise ValueError(f"Master {master} not found in {filename}")
    return _load_gsfont(gsmaster)


# glyphsLib -> babelfont


def _load_gsfont(gsfontmaster):
    bbf = Font(gsfontmaster)

    # XXX Create: info, groups, kerning, features, lib

    bbf.info.familyName = gsfontmaster.font.familyName
    bbf.info.styleName = gsfontmaster.name
    bbf.lib.glyphOrder = [x.name for x in gsfontmaster.font.glyphs]
    # Only support one layer for now
    layer = Layer()
    layer._lib = Lib()
    layer._name = gsfontmaster.name
    layer._glyphs = {}
    bbf._layers.append(layer)
    bbf._layerOrder.append(gsfontmaster.name)

    for g in gsfontmaster.font.glyphs:
        layer._glyphs[g.name] = _load_gslayer(g.layers[gsfontmaster.id], layer)

    return bbf


def _load_gslayer(gslayer, layer):  # -> Glyph
    glyph = Glyph()
    glyph._layer = layer
    glyph._name = gslayer.parent.name
    glyph._unicodes = [gslayer.parent.unicode]
    glyph._width = gslayer.width
    glyph._height = gslayer.master.ascender - gslayer.master.descender  # ?
    glyph._lib = Lib()
    glyph._lib.glyph = glyph

    c = gslayer.parent.category
    sc = gslayer.parent.subCategory
    if sc == "Ligature":
        glyph._category = "ligature"
    if c == "Mark":
        glyph._category = "mark"
    else:
        glyph._category = "base"

    # components, anchors, guidelines, image
    glyph._components = [_load_gscomponent(c, glyph) for c in gslayer.components]
    glyph._contours = [_load_gspath(p, glyph) for p in gslayer.paths]
    return glyph


def _load_gspath(gspath, glyph):
    contour = Contour()
    contour._glyph = glyph
    contour._points = [_load_gspoint(p, contour) for p in gspath.nodes]
    return contour


def _load_gscomponent(gscomponent, glyph):
    component = Component()
    component._glyph = glyph
    # XXX
    return component


def _load_gsanchor(gsanchor, glyph):
    anchor = Anchor()
    anchor._glyph = glyph
    # XXX
    return anchor


def _load_gspoint(gspoint, contour):
    point = Point()
    point._contour = contour
    point._x = gspoint.position.x
    point._y = gspoint.position.y
    point.type = gspoint.type
    point.smooth = gspoint.smooth
    return point


# babelfont -> glyphsLib
