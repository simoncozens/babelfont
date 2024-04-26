from fontTools.feaLib import ast
from fontTools.misc.visitor import Visitor

from babelfont.Font import Font
from babelfont.Features import as_ast

from babelfont.Glyph import GlyphList


def rename_glyphs(font: Font, args: dict = {}):
    if "mapping" in args:
        mapping = args["mapping"]
    elif "production" in args:
        mapping = {
            glyph.name: glyph.production_name
            for glyph in font.glyphs
            if glyph.production_name is not None
        }
    else:
        raise ValueError(
            "rename_glyphs requires either a 'mapping' or 'production' argument"
        )

    # Step 1: features
    # 1a) classes
    for cls in font.features.classes.keys():
        font.features.classes[cls] = [
            mapping.get(glyph, glyph) for glyph in font.features.classes[cls]
        ]
    # 1b) prefixes
    for prefix in font.features.prefixes.keys():
        font.features.prefixes[prefix] = _rename_fea(
            as_ast(font.features.prefixes[prefix], font.features), mapping
        ).asFea()
    # 1c) features
    font.features.features = [
        (
            featurename,
            _drop_wrapper(
                _rename_fea(as_ast(code, font.features, featurename), mapping)
            ).asFea(),
        )
        for featurename, code in font.features.features
    ]

    for glyph in font.glyphs:
        # Step 2: components
        for layer in glyph.layers:
            for component in layer.components:
                component.ref = mapping.get(component.ref, component.ref)
        # Step 3: glyphs
        glyph.name = mapping.get(glyph.name, glyph.name)
    font.glyphs = GlyphList({glyph.name: glyph for glyph in font.glyphs})


class FeaRenameVisitor(Visitor):
    def __init__(self, mapping):
        self.mapping = mapping


@FeaRenameVisitor.register(ast.GlyphName)
def visit(visitor, gn, *args, **kwargs):
    gn.glyph = visitor.mapping.get(gn.glyph, gn.glyph)
    return False


@FeaRenameVisitor.register(ast.GlyphClass)
def visit(visitor, gcd, *args, **kwargs):
    gcd.glyphs = [visitor.mapping.get(glyph, glyph) for glyph in gcd.glyphs]
    return False


@FeaRenameVisitor.register(ast.MarkClassDefinition)
def visit(visitor, mcd, *args, **kwargs):
    visitor.visitAttr(mcd, "anchor", mcd.anchor, *args, **kwargs)
    visitor.visitAttr(mcd, "glyphs", mcd.glyphs, *args, **kwargs)
    return False


def _rename_fea(parsed: ast.Block, mapping, wrap=None):
    FeaRenameVisitor(mapping).visit(parsed)
    return parsed


def _drop_wrapper(parsed: ast.FeatureFile):
    block = ast.Block()
    block.statements = parsed.statements[0].statements
    return block
