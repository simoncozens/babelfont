from collections import defaultdict
import logging

from fontTools.feaLib import ast
from fontTools.misc.visitor import Visitor

from babelfont.Font import Font
from babelfont.Features import as_ast

logger = logging.getLogger(__name__)


def drop_unexported_glyphs(font: Font, _args=None):
    unexported = set(glyph.name for glyph in font.glyphs if not glyph.exported)
    # Safety check one: look in components:
    appearances = defaultdict(set)
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for c in layer.components:
                if c.ref in unexported:
                    appearances[c.ref].add(glyph.name)
    if appearances:
        logger.warning(
            "Unexported glyphs are used in components, use decomposeMixed first:"
        )
        for glyph, refs in appearances.items():
            logger.warning(f"  {glyph} -> {', '.join(refs)}")
        logger.warning("Will not drop these glyphs.")
        unexported -= set(appearances.keys())
    # Safety check two: look in features
    for featurename, code in font.features.features:
        parsed = as_ast(code, font.features, featurename)
        visitor = FeaAppearsVisitor()
        visitor.visit(parsed)
        for glyph in visitor.appearances:
            if glyph in unexported:
                logger.warning(
                    f"Unexported glyph {glyph} is used in feature {featurename}, will not drop it."
                )
                unexported.remove(glyph)
    for classname, glyphs in font.features.classes.items():
        for glyph in glyphs:
            if glyph in unexported:
                logger.warning(
                    f"Unexported glyph {glyph} is used in class @{classname}, will not drop it."
                )
                unexported.remove(glyph)
    for prefix, code in font.features.prefixes.items():
        parsed = as_ast(code, font.features)
        visitor = FeaAppearsVisitor()
        visitor.visit(parsed)
        for glyph in visitor.appearances:
            if glyph in unexported:
                logger.warning(
                    f"Unexported glyph {glyph} is used in prefix {prefix}, will not drop it."
                )
                unexported.remove(glyph)

    # Now we are good to go
    for glyph in unexported:
        font.glyphs.pop(glyph)


class FeaAppearsVisitor(Visitor):
    def __init__(self):
        self.appearances = set()


@FeaAppearsVisitor.register(ast.GlyphName)
def visit(visitor, gn, *args, **kwargs):
    visitor.appearances.add(gn.glyph)
    return False


@FeaAppearsVisitor.register(ast.MarkClassDefinition)
def visit(visitor, mcd, *args, **kwargs):
    visitor.visitAttr(mcd, "glyphs", mcd.glyphs, *args, **kwargs)
    return False
