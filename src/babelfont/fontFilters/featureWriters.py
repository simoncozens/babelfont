# from fontFeatures import Attachment, Routine, Positioning, ValueRecord
import logging
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otBase, otTables

logger = logging.getLogger(__name__)


def build_all_features(font, ttFont):
    logger.info("Generating opentype features")

    # build_cursive(font)
    # build_mark_mkmk(font)
    # build_mark_mkmk(font, "mkmk")
    # build_kern(font)

    features = font.features.to_fea()
    logger.info("Compiling opentype features")
    addOpenTypeFeaturesFromString(ttFont, features)
    add_gdef_classdef(font, ttFont)


CATMAP = {"base": 1, "ligature": 2, "mark": 3, "component": 4}


def add_gdef_classdef(font, ttFont):
    if not "GDEF" in ttFont:
        ttFont["GDEF"] = newTable("GDEF")
        gdef = otTables.GDEF()
        gdef.GlyphClassDef = otTables.GlyphClassDef()
        gdef.GlyphClassDef.classDefs = {}
        gdef.Version = 0x00010000
        ttFont["GDEF"].table = gdef
    else:
        gdef = ttFont["GDEF"].table
    classdeftable = gdef.GlyphClassDef.classDefs
    if not classdeftable:
        for glyph in font.glyphs:
            if glyph.category in CATMAP:
                classdeftable[glyph.name] = CATMAP[glyph.category]


def build_kern(font):
    def _expand_class(c):
        if c[0] != "@":
            return [c]
        if c[1:] not in font.features.namedClasses:
            logging.info("Attempted to use undefined kerning class %s" % c)
            return None
        return [x for x in font.features.namedClasses[c[1:]] if font.glyphs[x].exported]

    kernroutine = Routine()
    for (left, right), kern in font._all_kerning.items():
        left, right = _expand_class(left), _expand_class(right)
        if left is None or right is None:
            continue
        kernroutine.rules.append(
            Positioning(
                [left, right],
                [ValueRecord(xAdvance=kern), ValueRecord()],
            )
        )
    font.features.addFeature("kern", [kernroutine])


def build_cursive(font):
    anchors = font._all_anchors
    if "entry" in anchors and "exit" in anchors:
        attach = Attachment(
            "entry", "exit", anchors["entry"], anchors["exit"], flags=(0x8 | 0x1)
        )
        r = Routine(
            rules=[attach],
        )
        font.features.addFeature("curs", [r])


def build_mark_mkmk(font, which="mark", strict=False):
    # Find matching pairs of foo/_foo anchors
    anchors = font._all_anchors
    r = Routine(rules=[])
    if which == "mark":
        basecategory = "base"
    else:
        basecategory = "mark"
    for baseanchor in anchors:
        markanchor = "_" + baseanchor
        if markanchor not in anchors:
            continue
        # Filter glyphs to those which are baseanchors
        bases = {
            k: v
            for k, v in anchors[baseanchor].items()
            if font.glyphs[k].exported and (font.glyphs[k].category == basecategory)
        }
        marks = {
            k: v
            for k, v in anchors[markanchor].items()
            if font.glyphs[k].exported
            and (not strict or font.glyphs[k].category == "mark")
        }
        if not (bases and marks):
            continue
        attach = Attachment(baseanchor, markanchor, bases, marks)
        attach.fontfeatures = font.features  # THIS IS A TERRIBLE HACK
        r.rules.append(attach)
    if r.rules:
        font.features.addFeature(which, [r])
