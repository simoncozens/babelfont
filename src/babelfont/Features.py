from io import StringIO
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from fontTools.feaLib import ast
from fontTools.feaLib.parser import Parser

from .BaseObject import BaseObject

PREFIX_MARKER = "# Prefix: "
PREFIX_RE = re.compile(r"# Prefix: (.*)")


@dataclass
class Features(BaseObject):
    """A representation of the OpenType feature code."""

    classes: Dict[str, List[str]] = field(
        default_factory=dict,
        metadata={
            "separate_items": True,
            "description": "A dictionary of classes. Each group is a list of glyph names or class names. The key should not start with @.",
        },
    )
    prefixes: Dict[str, str] = field(
        default_factory=dict,
        metadata={
            "separate_items": True,
            "description": "A dictionary of OpenType lookups and other feature code to be placed before features are defined. The keys are user-defined names, the values are AFDKO feature code.",
        },
    )
    features: List[Tuple[str, str]] = field(
        default_factory=list,
        metadata={
            "separate_items": True,
            "description": "A list of OpenType feature code, expressed as a tuple (feature tag, code).",
        },
    )

    @classmethod
    def from_fea(cls, fea: str, glyphNames=()) -> "Features":
        """Load features from a .fea file."""
        parsed = Parser(
            StringIO(fea), followIncludes=False, glyphNames=glyphNames
        ).parse()
        features = Features()
        currentPrefix = "anonymous"
        for statement in parsed.statements:
            if isinstance(statement, ast.GlyphClassDefinition):
                statement.glyphs.asFea()  # This builds .original
                if statement.glyphs.original:
                    features.classes[statement.name] = [
                        ast.asFea(x) for x in statement.glyphs.original
                    ]
                else:
                    features.classes[statement.name] = list(statement.glyphs.glyphs)
            elif isinstance(statement, ast.FeatureBlock):
                features.features.append((statement.name, ast.Block.asFea(statement)))
            elif isinstance(statement, ast.Comment) and (
                m := re.match(PREFIX_RE, statement.text)
            ):
                currentPrefix = m.group(1)
            else:
                if currentPrefix not in features.prefixes:
                    features.prefixes[currentPrefix] = ""
                features.prefixes[currentPrefix] += statement.asFea()
        return features

    def to_fea(self) -> str:
        """Dump features to a .fea file."""
        fea = ""
        for name, glyphs in self.classes.items():
            fea += f"@{name} = [{' '.join(glyphs)}];\n"
        for prefix, code in self.prefixes.items():
            if prefix != "anonymous":
                fea += f"# Prefix: {prefix}\n"
            fea += code + "\n"
        for name, code in self.features:
            fea += f"feature {name} {{\n{code}}} {name};\n"
        return fea


def as_ast(code, features, featurename=None, glyphNames=()):
    if featurename is not None and not code.startswith("feature"):
        code = f"feature {featurename} {{\n{code}\n}} {featurename};"
    parser = Parser(StringIO(code), followIncludes=False, glyphNames=glyphNames)
    # Set up classes
    for classname, glyphs in features.classes.items():
        glyphcls = ast.GlyphClass(glyphs=[ast.GlyphName(g) for g in glyphs])
        glyphclass = ast.GlyphClassDefinition(classname, glyphcls)
        parser.glyphclasses_.define(classname, glyphclass)
    return parser.parse()
