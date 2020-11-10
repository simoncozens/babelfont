from fontTools.ttLib import TTFont
from babelfont.font import Font
from babelfont.layer import Layer
from babelfont.lib import Lib
from babelfont.glyph import Glyph
from babelfont.point import Point
from babelfont.contour import Contour
from babelfont.component import Component
from babelfont.anchor import Anchor
from babelfont.convertors.utils import _toFlagBits
from copy import copy
import math


def can_load(filename):
    if not (filename.endswith(".otf") or filename.endswith(".ttf")):
      return False
    font = TTFont(filename)
    return "glyf" in font

def can_save(filename):
    return filename.endswith(".ttf")

def load(filename, **kwargs):
    return _load_ttfont(TTFont(filename))

def save(font, filename):
    ttfont = _save_ttfont(font)
    ttfont.save(filename)

# TTFont -> babelfont

def _load_ttfont(ttfont):
    bbf = Font()
    _load_name_table(bbf, ttfont["name"])
    _load_other_info(bbf, ttfont)
    bbf.lib.glyphOrder = ttfont.getGlyphOrder()
    # Make a layer
    layer = bbf.newLayer("public.default")
    cmap = ttfont["cmap"].buildReversed()
    for glyph in ttfont.getGlyphOrder():
        layer._glyphs[glyph] = None
        layer._promised_glyphs[glyph] = lambda glyph=glyph,ttfont=ttfont,cmap=cmap : _load_ttglyph(glyph, ttfont, cmap)
    ff = _load_features(bbf, ttfont)
    _load_ttanchors(bbf, ttfont, ff)

    return bbf

_namesmap = [
("openTypeNameDesigner", 9),
("openTypeNameDesignerURL", 12),
("openTypeNameManufacturer", 8),
("openTypeNameManufacturerURL", 11),
("openTypeNameLicense", 13),
("openTypeNameLicenseURL", 14),
("openTypeNameVersion", 5),
("openTypeNameUniqueID", 3),
("openTypeNameDescription", 10),
("openTypeNamePreferredFamilyName", 16),
("openTypeNamePreferredSubfamilyName", 17),
("openTypeNameCompatibleFullName", 18),
("openTypeNameSampleText", 19),
("openTypeNameWWSFamilyName", 21),
("openTypeNameWWSSubfamilyName", 22),
("copyright", 0),
("styleMapFamilyName", 1),
("trademark", 7)
]

def _load_name_table(bbf, nametable):
    for (attr, nameId) in _namesmap:
        n = nametable.getDebugName(nameId)
        if n:
            setattr(bbf.info, attr, n)
    # Handle styleMapStyleName separately
    smsn = nametable.getDebugName(2)
    if smsn:
        smsn = smsn.lower()
        if smsn in ["regular", "italic", "bold", "bold italic"]:
            bbf.info.styleMapStyleName = smsn

    family = (nametable.getDebugName(16) or nametable.getDebugName(1))
    if family:
        bbf.info.familyName = family

    style = (nametable.getDebugName(17) or nametable.getDebugName(2))
    if style:
        bbf.info.styleName = style

    # For bonus points we should load all translations here too.

def _load_other_info(bbf, ttfont):
    bbf.info.unitsPerEm = ttfont["head"].unitsPerEm
    bbf.info.versionMajor, bbf.info.versionMinor = [int(x) for x in str(ttfont["head"].fontRevision).split(".")]
    bbf.info.openTypeHeadFlags = _toFlagBits(ttfont["head"].flags)
    # bbf.info.openTypeHeadCreated = ttfont["head"].created # XXX
    bbf.info.openTypeHeadLowestRecPPEM = ttfont["head"].lowestRecPPEM

    for k in ["ascender", "descender", "lineGap", "caretSlopeRise", \
              "caretSlopeRun", "caretOffset"]:
        key = "openTypeHhea" + k[0].upper() + k[1:]
        setattr(bbf.info, key, getattr(ttfont["hhea"], k))

    bbf.info.openTypeOS2WidthClass  = ttfont["OS/2"].usWidthClass
    bbf.info.openTypeOS2WeightClass = ttfont["OS/2"].usWeightClass
    selection = _toFlagBits(ttfont["OS/2"].fsSelection)
    bbf.info.openTypeOS2Selection = [x for x in selection if x not in [0,5,6]]
    bbf.info.openTypeOS2VendorID = ttfont["OS/2"].achVendID
    # panose is horrible
    bbf.info.openTypeOS2UnicodeRanges = _toFlagBits(
        ttfont["OS/2"].ulUnicodeRange1 + \
        (ttfont["OS/2"].ulUnicodeRange2 << 32) + \
        (ttfont["OS/2"].ulUnicodeRange3 << 64) + \
        (ttfont["OS/2"].ulUnicodeRange4 << 96)
    )

    bbf.info.openTypeOS2CodePageRanges = _toFlagBits(
        ttfont["OS/2"].ulCodePageRange1 + ttfont["OS/2"].ulCodePageRange2 << 32
    )

    # XXX vertical metrics...
    bbf.info.xHeight = ttfont["OS/2"].sxHeight
    bbf.info.capHeight = ttfont["OS/2"].sCapHeight
    bbf.info.ascender = ttfont["hhea"].ascender
    bbf.info.descender = ttfont["hhea"].descender

    for k in ["usWidthClass", "usWeightClass", "sTypoAscender", "sTypoDescender", \
        "sTypoLineGap", "usWinAscent", "usWinDescent", "ySubscriptXSize", \
        "ySubscriptYSize", "ySubscriptXOffset", "ySubscriptYOffset", \
        "ySuperscriptXSize", "ySuperscriptYSize", "ySuperscriptXOffset", \
        "ySuperscriptYOffset", "yStrikeoutSize", "yStrikeoutPosition"
        ]:
        val = getattr(ttfont["OS/2"], k)
        while not k[0].isupper():
            k = k[1:]
        setattr(bbf.info, "openTypeOS2"+k, val)

    # vhea
    # postscript

def _load_ttglyph(g, ttfont, cmap):
    glyph = Glyph()
    glyph._name = g

    if g in cmap:
        glyph._unicodes = list(cmap[g])
    else:
        glyph._unicodes = []

    if "GDEF" in ttfont and hasattr(ttfont["GDEF"].table, "GlyphClassDef"):
        classdefs = ttfont["GDEF"].table.GlyphClassDef.classDefs
        if g in classdefs:
            if classdefs[g] == 1: glyph._lib["public.openTypeCategory"] = "base"
            if classdefs[g] == 2: glyph._lib["public.openTypeCategory"] = "ligature"
            if classdefs[g] == 3: glyph._lib["public.openTypeCategory"] = "mark"
            if classdefs[g] == 4: glyph._lib["public.openTypeCategory"] = "component"

    glyph._contours = []

    _load_ttcategory(glyph, ttfont, g)

    ttglyph = ttfont.getGlyphSet()[g]._glyph # _TTGlyphGlyf object
    for i in range (0, max(ttglyph.numberOfContours, 0)):
        c = _load_contour(ttglyph, i)
        c._glyph = glyph
        glyph._contours.append(c)

    glyph._width       = ttfont["hmtx"][g][0]
    glyph._leftMargin  = ttfont["hmtx"][g][1]
    glyph._height      = ttfont["hhea"].ascent
    if glyph.bounds:
        glyph._rightMargin = glyph._width - glyph.bounds[2]

    if hasattr(ttglyph, "components"):
        for c in ttglyph.components:
            comp = _load_component(c)
            comp._glyph = glyph
            glyph._components.append(comp)

    return glyph

def _load_ttcategory(glyph, ttfont, g):
    if not "GDEF" in ttfont or not hasattr(ttfont["GDEF"].table, "GlyphClassDef"):
        return
    classdefs = ttfont["GDEF"].table.GlyphClassDef.classDefs
    if not g in classdefs:
        return
    if classdefs[g] == 1: glyph._lib["public.openTypeCategory"] = "base"
    if classdefs[g] == 2: glyph._lib["public.openTypeCategory"] = "ligature"
    if classdefs[g] == 3: glyph._lib["public.openTypeCategory"] = "mark"
    if classdefs[g] == 4: glyph._lib["public.openTypeCategory"] = "component"

def _load_features(font, ttfont):
    try:
        from fontFeatures.ttLib import unparse
    except Exception as e:
        return None
    ff = unparse(ttfont)
    font.features.text = ff.asFea()
    return ff

def _load_ttanchors(font, ttfont, ff=None):
    if not "GPOS" in ttfont:
        return
    t = ttfont["GPOS"].table

    # Do cursive first
    cursives = filter(lambda x: x.LookupType == 3, t.LookupList.Lookup)
    for c in cursives:
        for s in c.SubTable:
            for glyph, record in zip(s.Coverage.glyphs, s.EntryExitRecord):
                if record.EntryAnchor:
                    entryAnchor = Anchor()
                    entryAnchor._glyph = glyph
                    entryAnchor.x = record.EntryAnchor.XCoordinate
                    entryAnchor.y = record.EntryAnchor.YCoordinate
                    entryAnchor.name = "entry"
                    font[glyph]._anchors.append(entryAnchor)
                if record.ExitAnchor:
                    exitAnchor = Anchor()
                    exitAnchor._glyph = glyph
                    exitAnchor.x = record.ExitAnchor.XCoordinate
                    exitAnchor.y = record.ExitAnchor.YCoordinate
                    exitAnchor.name = "exit"
                    font[glyph]._anchors.append(exitAnchor)

    # Now do others, synthesizing names
    # XXX

def _load_contour(ttglyph, index):
    endPt = ttglyph.endPtsOfContours[index]
    if index > 0:
        startPt = ttglyph.endPtsOfContours[index-1] + 1
    else:
        startPt = 0
    points = []
    for j in range(startPt, endPt+1):
        coords = (ttglyph.coordinates[j][0], ttglyph.coordinates[j][1])
        flags = ttglyph.flags[j] == 1
        t = "offcurve"
        if flags == 1:
            if (j == startPt and ttglyph.flags[endPt] == 1) or (j != startPt and points[-1].type != "offcurve"):
                t = "line"
            else:
                t = "qcurve"
        else:
            if len(points) > 1 and points[-1].type == "offcurve":
                # Double offcurve. Insert implicit oncurve.
                prevpoint = points[-1]
                intermediate = Point()
                intermediate.x = (coords[0] + prevpoint.x) / 2
                intermediate.y = (coords[1] + prevpoint.y) / 2
                intermediate.smooth = False # XXX
                intermediate.type = "qcurve"
                points.append(intermediate)
        p = Point()
        p.x, p.y = coords
        p.type = t
        p.smooth = False # for testing
        points.append(p)
    c = Contour()
    c._points = points
    c._correct_direction()
    return c

def _load_component(c):
    component = Component()
    component._baseGlyph, component.transformation = c.getComponentInfo()
    return component

# babelfont -> TTFont
