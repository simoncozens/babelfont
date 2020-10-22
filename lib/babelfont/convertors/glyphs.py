import glyphsLib
from datetime import datetime
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

def save(font, filename):
    gsfont = _save_gsfont(font)
    gsfont.save(filename)

# glyphsLib -> babelfont


def _load_gsfont(gsfontmaster):
    bbf = Font(gsfontmaster)

    # XXX Create: info, groups, kerning, features, lib

    bbf.info.familyName = gsfontmaster.font.familyName
    bbf.info.styleName = gsfontmaster.name
    bbf.lib.glyphOrder = [x.name for x in gsfontmaster.font.glyphs]
    bbf.lib["com.schriftgestaltung.appVersion"] = gsfontmaster.font.appVersion
    bbf.lib["com.schriftgestaltung.DisplayStrings"] = gsfontmaster.font.DisplayStrings
    bbf.lib["com.schriftgestaltung.fontMasterID"] = gsfontmaster.id

    bbf.info.openTypeHeadCreated = _glyphs_date_to_ufo(gsfontmaster.font.date)
    bbf.info.unitsPerEm = gsfontmaster.font.upm

    # Only support one layer for now
    layer = Layer()
    layer._lib = Lib()
    layer._name = gsfontmaster.name
    layer._glyphs = {}

    bbf.info.ascender = gsfontmaster.ascender
    bbf.info.capHeight = gsfontmaster.capHeight
    bbf.info.descender = gsfontmaster.descender

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
    glyph._lib["com.schriftgestaltung.lastChange"] = gslayer.parent.lastChange

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


def _save_point(point):
    p = glyphsLib.GSNode ((point.x, point.y), point.type)
    p.smooth = point.smooth
    return p


def _save_contour(contour):
    path = glyphsLib.GSPath()
    path.nodes = [_save_point(p) for p in contour._points]
    # Check node order
    # XXX closed, direction
    return path


def _save_component(component):
    c = glyphsLib.GSComponent(component.glyph)
    # XXX
    return c

def _save_glyph(glyph, gsfont):
    # This needs to go into a layer and a glyph
    masterId = gsfont.masters[0].id
    gslayer = glyphsLib.GSLayer()
    gsglyph = glyphsLib.GSGlyph()
    gslayer.layerId = masterId
    gsglyph.layers.append(gslayer)
    gsglyph.unicode = glyph._unicodes[0]
    gsglyph.lastChange = glyph.lib["com.schriftgestaltung.lastChange"]

    gslayer.paths = [_save_contour(c) for c in glyph.contours]
    gslayer.components = [_save_component(c) for c in glyph.components]
    gslayer.name = glyph.name
    gslayer.RSB = glyph.rightMargin
    gslayer.LSB = glyph.leftMargin
    gslayer.width = glyph.width
    # Attach to master ID
    gsglyph.name = glyph.name
    gsfont.glyphs.append(gsglyph)

def _save_gsfont(font):
    f = glyphsLib.GSFont()
    f.familyName = font.info.familyName
    f.appVersion = font.lib["com.schriftgestaltung.appVersion"]
    f.DisplayStrings = font.lib["com.schriftgestaltung.DisplayStrings"]
    f.date = _ufo_date_to_glyphs(font.info.openTypeHeadCreated)
    f.upm = font.info.unitsPerEm
    fontmaster = glyphsLib.GSFontMaster()
    fontmaster.id = font.lib["com.schriftgestaltung.fontMasterID"]

    f.masters = [fontmaster]
    fontmaster.ascender = font.info.ascender
    fontmaster.capHeight = font.info.capHeight
    fontmaster.descender = font.info.descender
    for glyph in font.defaultLayer:
        _save_glyph(glyph, f)
    return f

# Random stuff

def _glyphs_date_to_ufo(d):
    return d.strftime('%Y/%m/%d %H:%M:%S')

def _ufo_date_to_glyphs(d):
    return datetime.strptime(d, '%Y/%m/%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S +0000')
