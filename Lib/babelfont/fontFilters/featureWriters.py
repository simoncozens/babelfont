from fontFeatures import Attachment, Routine


def build_cursive(font):
    anchors = font._all_anchors
    if "entry" in anchors and "exit" in anchors:
        attach = Attachment(
            "entry", "exit", anchors["entry"], anchors["exit"]
        )
        r = Routine(rules=[attach], flags=(0x8 | 0x1))
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
            if font.glyphs[k].exported and (not strict or font.glyphs[k].category == "mark")
        }
        if not (bases and marks):
            continue
        attach = Attachment(baseanchor, markanchor, bases, marks)
        attach.fontfeatures = font.features  # THIS IS A TERRIBLE HACK
        r.rules.append(attach)
    if r.rules:
        font.features.addFeature(which, [r])
