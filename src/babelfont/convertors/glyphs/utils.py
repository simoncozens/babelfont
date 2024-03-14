from babelfont.BaseObject import I18NDictionary
import re


def _stash(item, glyphs, include=None, exclude=None):
    if include:
        keys = include
    else:
        keys = glyphs.keys()
    if exclude:
        keys = [k for k in keys if k not in exclude]

    for key in keys:
        if glyphs.get(key):
            if "com.glyphsapp" not in item._formatspecific:
                item._formatspecific["com.glyphsapp"] = {}
            item._formatspecific["com.glyphsapp"][key] = glyphs.get(key)


def _g(item, key, default=None, pop=False):
    if "com.glyphsapp" in item._formatspecific:
        if pop:
            return item._formatspecific["com.glyphsapp"].pop(key, default)
        return item._formatspecific["com.glyphsapp"].get(key, default)
    return default


def _stashed_cp(thing, name):
    return _custom_parameter(thing._formatspecific.get("com.glyphsapp", []), name)


def _custom_parameter(thing, name):
    for param in thing.get("customParameters", []):
        if param["name"] == name:
            return param["value"]
    return None


def _moveformatspecific(item):
    rv = {}
    if "com.glyphsapp" in item._formatspecific:
        rv = {**item._formatspecific.get("com.glyphsapp", {})}
    return rv


def _copyattrs(src, dst, attrs, convertor=lambda x: x):
    for a in attrs:
        v = getattr(src, a)
        if isinstance(v, I18NDictionary):
            v = v.get_default()
        if v:
            dst[a] = convertor(v)


opentype_custom_parameters = {
}

_rename_metrics = {
    "x-height": "xHeight",
    "cap height": "capHeight",
    "italic angle": "italicAngle"
}
_reverse_rename_metrics = {v: k for k, v in _rename_metrics.items()}


def _glyphs_metrics_to_ours(k):
    return _rename_metrics.get(k, k)


def _our_metrics_to_glyphs(k):
    return _reverse_rename_metrics.get(k, k)


def _metrics_name_to_dict(k):
    m = re.match(r"(.*) \[filter (.*)\]$", k)
    if m:
        return {"type": _our_metrics_to_glyphs(m[1]), "filter": m[2]}
    if k in _reverse_rename_metrics:
        return {"type": _reverse_rename_metrics[k]}
    return {"type": k}


def _metrics_dict_to_name(k):
    name = _glyphs_metrics_to_ours(k.get("type"))
    if "filter" in k:
        name += " [filter " + k.get("filter") + "]"
    return name


def glyphs_i18ndict(i):
    return [{"language": k, "value": v} for k, v in i.items()]


def to_bitfield(flags):
    # Convert an integer flag to an array of bit indices
    return [i for i in range(8) if flags & (1 << i)]
