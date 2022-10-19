import dataclasses
from babelfont import *
import babelfont
from babelfont.BaseObject import I18NDictionary
from graphviz import Digraph
import re

tocfile = open("site/_data/navigation.yml", "w")
tocfile.write("default:\n")


def maybelink(t):
    if "babelfont" in str(t) and dataclasses.is_dataclass(t):
        return "[`%s`](%s.html)" % (t.__name__, t.__name__)
    if isinstance(t, tuple):
        return "(" + ", ".join([e.__name__ for e in t]) + ")"
    return t.__name__


def describe_dataclass(cls):
    if not dataclasses.is_dataclass(cls):
        return

    name = cls.__name__
    f = open("site/%s.md" % name, "w")
    tocfile.write("  - title: %s\n    url: %s.html\n" % (name, name))
    f.write("---\ntitle: %s\n---\n" % name)

    f.write(cls.__doc__)
    f.write("\n")
    if cls._write_one_line:
        f.write(
            "* When writing to Babelfont-JSON, this class must be serialized without newlines\n"
        )
    for k in dataclasses.fields(cls):
        if k.name == "_":
            continue
        if isinstance(k.type, list):
            stringytype = "[%s]" % ", ".join([maybelink(t) for t in k.type])
        elif isinstance(k.type, tuple):
            stringytype = "(%s)" % ", ".join([maybelink(t) for t in k.type])
        else:
            stringytype = maybelink(k.type)
        if not "`" in stringytype:
            stringytype = "`%s`" % stringytype
        f.write("## %s.%s\n\n" % (name, k.name))
        f.write("* Python type: %s\n\n" % stringytype)
        if "json_type" in k.metadata:
            f.write("* Babelfont-JSON type: `%s`\n\n" % k.metadata["json_type"])
        if (
            k.default is dataclasses.MISSING
            and k.default_factory is dataclasses.MISSING
        ):
            f.write("* **Required field**\n\n")
        if "json_location" in k.metadata:
            f.write(
                "* When writing to Babelfont-JSON, this structure is stored under the separate file `%s`.\n\n"
                % k.metadata["json_location"]
            )

        if "separate_items" in k.metadata:
            f.write(
                "* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.\n\n"
            )
        if "python_only" in k.metadata:
            f.write(
                "* This field only exists as an attribute of the the Python object and should not be written to Babelfont-JSON.\n\n"
            )

        if "description" in k.metadata:
            f.write(k.metadata["description"])
        if k.type == I18NDictionary:
            f.write(" *Localizable.*")
        f.write("\n")
        if k.default is not dataclasses.MISSING:
            f.write("*If not provided, defaults to* `%s`.\n" % str(k.default))
        f.write("\n\n")
    f.close()


describe_dataclass(Font)
describe_dataclass(Axis)
describe_dataclass(Instance)
describe_dataclass(Master)
describe_dataclass(Names)
describe_dataclass(Glyph)
describe_dataclass(Layer)
describe_dataclass(Guide)
describe_dataclass(Shape)
describe_dataclass(Anchor)


dot = Digraph(comment="Neutral Font Source Format", format="svg")
dot.attr(rankdir="LR")
dot.attr(overlap="false")
donetypes = {}


def add_type_node(cls):
    def chktype(t, port):
        if "babelfont" in str(t) and dataclasses.is_dataclass(t):
            add_type_node(t)
            dot.edge(cls.__name__ + ":" + port, t.__name__)
        if isinstance(t, tuple):
            return "(" + ", ".join([e.__name__ for e in t]) + ")"
        return t.__name__

    if cls in donetypes:
        return
    if not dataclasses.is_dataclass(cls):
        return
    label = (
        """<<TABLE>
    <tr><td colspan="2" border="0"><b>%s</b></td></tr>
    """
        % cls.__name__
    )
    for k in dataclasses.fields(cls):
        if k.name == "_" or "python_only" in k.metadata:
            continue
        if isinstance(k.type, list):
            stringytype = "[%s]" % ", ".join([chktype(t, k.name) for t in k.type])
        elif isinstance(k.type, tuple):
            stringytype = "(%s)" % ", ".join([chktype(t, k.name) for t in k.type])
        else:
            stringytype = chktype(k.type, k.name)
        name = k.name
        if (
            k.default is dataclasses.MISSING
            and k.default_factory is dataclasses.MISSING
        ):
            name = "<b>%s</b>" % name
        label = label + '<tr><td>%s</td><td port="%s"><i>%s</i></td></tr>' % (
            name,
            k.name,
            stringytype,
        )

    label = label + "</TABLE>>"
    dot.node(
        cls.__name__,
        label,
        shape="none",
        fontname="Avenir",
        href="%s.html" % cls.__name__,
    )
    donetypes[cls] = True


add_type_node(Font)
add_type_node(Glyph)
dot.edge("Font:glyphs", "Glyph")
output = re.sub(r"(?s)^.*<svg", "<svg", dot.pipe().decode("utf-8"))
out = open("site/index.md", "w")
out.write(
    """---
title: Neutral Font Source Format
toc: false
---


"""
)
out.write(output + "\n")
