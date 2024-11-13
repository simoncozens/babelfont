from collections import defaultdict
import logging
from typing import Set

from ufomerge.layout import LayoutSubsetter

from fontTools.feaLib import ast
from fontTools.misc.visitor import Visitor

from babelfont.Font import Font
from .rename import _drop_wrapper

logger = logging.getLogger(__name__)


def drop_unexported_glyphs(font: Font, args=None):
    logger.info("Dropping unexported glyphs")
    unexported = set(glyph.name for glyph in font.glyphs if not glyph.exported)
    if "force" in args:
        fixup_used_glyphs(font, unexported)
    else:
        warn_about_used_glyphs(font, unexported)

    # Now we are good to go
    for glyph in unexported:
        font.glyphs.pop(glyph)


def warn_about_used_glyphs(font: Font, unexported: Set[str]):
    # This is a safe version which will not drop glyphs that are used in components or features

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
    parsed_features = font.features.as_ast(font)

    for featurename, parsed in parsed_features["features"]:
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
    for prefix, parsed in parsed_features["prefixes"].items():
        visitor = FeaAppearsVisitor()
        visitor.visit(parsed)
        for glyph in visitor.appearances:
            if glyph in unexported:
                logger.warning(
                    f"Unexported glyph {glyph} is used in prefix {prefix}, will not drop it."
                )
                unexported.remove(glyph)


def fixup_used_glyphs(font: Font, unexported: Set[str]):
    # Drop glyphs by tidying up features and components
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for c in layer.components:
                if c.ref in unexported:
                    layer.decompose()
    for classname, glyphs in font.features.classes.items():
        font.features.classes[classname] = [g for g in glyphs if g not in unexported]
    parsed_features = font.features.as_ast(font)
    newfeatures = []
    for feature, parsed in parsed_features["features"]:
        subsetter = LayoutSubsetter(
            [g.name for g in font.glyphs if g.name not in unexported]
        )
        subsetter.subset(parsed)
        if parsed.statements:
            newfeatures.append((feature, _drop_wrapper(parsed).asFea()))
    font.features.features = newfeatures
    for prefix, parsed in parsed_features["prefixes"].items():
        subsetter = LayoutSubsetter(
            [g.name for g in font.glyphs if g.name not in unexported]
        )
        subsetter.subset(parsed)
        parsed.statements[:0] = [
            ast.LanguageSystemStatement(*pair)
            for pair in subsetter.incoming_language_systems
        ]

        font.features.prefixes[prefix] = parsed.asFea()


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
