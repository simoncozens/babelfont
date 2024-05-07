from io import StringIO
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from babelfont import Font
from fontTools.feaLib import ast
from fontTools.feaLib.parser import Parser, SymbolTable

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
            fea += f"feature {name} {{\n{code}\n}} {name};\n"
        return fea

    def as_ast(self, font: Font) -> Dict[str, Any]:
        rv = {
            "prefixes": {},
            "features": [],
        }
        glyphnames = font.glyphs.keys()
        lookups = SymbolTable()
        glyphclasses = SymbolTable()
        for name, glyphs in self.classes.items():
            glyphcls = ast.GlyphClass(glyphs=[ast.GlyphName(g) for g in glyphs])
            glyphclass = ast.GlyphClassDefinition(name, glyphcls)
            glyphclasses.define(name, glyphclass)

        for prefix, code in self.prefixes.items():
            parser = Parser(StringIO(code), followIncludes=False, glyphNames=glyphnames)
            parser.lookups_ = lookups
            parser.glyphclasses_ = glyphclasses
            try:
                file = parser.parse()
            except Exception as e:
                raise ValueError(f"Error parsing feature code: {e}\n\nCode was: {code}")
            rv["prefixes"][prefix] = file

        for name, code in self.features:
            if name is not None and not code.startswith("feature " + name):
                code = f"feature {name} {{\n{code}\n}} {name};"
            parser = Parser(StringIO(code), followIncludes=False, glyphNames=glyphnames)
            parser.lookups_ = lookups
            parser.glyphclasses_ = glyphclasses
            try:
                file = parser.parse()
            except Exception as e:
                raise ValueError(f"Error parsing feature code: {e}\n\nCode was: {code}")
            rv["features"].append((name, file))

        return rv
