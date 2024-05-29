import logging
import re

from babelfont import Font

logger = logging.getLogger(__name__)


class NibbleParser:
    def __init__(self, target):
        self.string = target

    def __call__(self, regex):
        if m := re.match(regex, self.string):
            self.string = re.sub(regex, "", self.string)
            return m
        return None


def translate_glyphs3_fea(font: Font, args=None):
    font.features.features = [
        (key, _translate(code, {"index": 0, "font": font, "tag": key}))
        for key, code in font.features.features
    ]


def _translate(code, state):
    return re.sub(
        "#ifdef VARIABLE(.*)#endif",
        lambda m: __translate(m, state),
        code,
        flags=re.DOTALL,
    ).replace("{;", "{")


def __translate(match, state):
    newstatements = []

    def name():
        return f"__condition_{state['tag']}_{state['index']}"

    axis_map = {a.tag: a for a in state["font"].axes}

    for statement in match.group(1).split(";"):
        p = NibbleParser(statement)
        if p(r"^\s*condition\s+"):
            axes = []
            while axis := p(
                r"""(?x)
                    (?:([\d.]+)\s*<)? # Axis minimum value
                    \s*(\w+)\s*    # Axis tag
                    (?:<\s*([\d.]+))? # Axis maximum value
                    ,?\s*             # Optional comma
            """
            ):
                min_v, tag, max_v = axis.groups()
                if tag not in axis_map:
                    raise ValueError(f"Axis {tag} not found in condition statement")
                if min_v is None:
                    min_v = axis_map[tag].minimum
                if max_v is None:
                    max_v = axis_map[tag].maximum
                axes.append(f"{tag} {min_v} {max_v}")
            if not axes:
                raise ValueError("No axis definition found for condition")

            if not newstatements:
                newstatements.append("")
            newstatements.append(f"}} {state['tag']}")
            state["index"] += 1
            newstatements.append(f"conditionset {name()} {{")
            newstatements.extend(axes)
            newstatements.append(f"}} {name()}")
            newstatements.append(f"variation {state['tag']} {name()} {{")
        else:
            newstatements.append(statement)
    return ";".join(newstatements)
