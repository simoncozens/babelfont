from io import StringIO

from fontTools.feaLib.parser import Parser
from fontTools.feaLib import ast
from fontTools.misc.visitor import Visitor

from babelfont.Font import Font

from babelfont.Glyph import GlyphList


def rename_glyphs(font: Font, args: dict):
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
            font.features.prefixes[prefix], mapping
        )
    # 1c) features
    font.features.features = [
        (feature, _rename_fea(code, mapping, wrap=feature))
        for feature, code in font.features.features
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


@FeaRenameVisitor.register(ast.MarkClassDefinition)
def visit(visitor, mcd, *args, **kwargs):
    visitor.visitAttr(mcd, "anchor", mcd.anchor, *args, **kwargs)
    visitor.visitAttr(mcd, "glyphs", mcd.glyphs, *args, **kwargs)
    return False


def _rename_fea(code, mapping, wrap=None):
    # Parse to AST
    if wrap is not None and not code.startswith("feature"):
        code = f"feature {wrap} {{\n{code}\n}} {wrap};"
    parsed = Parser(StringIO(code), followIncludes=False).parse()
    FeaRenameVisitor(mapping).visit(parsed)
    if wrap:
        return "\n".join(st.asFea() for st in parsed.statements[0].statements)
    return parsed.asFea()
