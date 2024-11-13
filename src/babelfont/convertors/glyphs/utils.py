from babelfont.BaseObject import I18NDictionary
import re

from babelfont.Master import CORE_METRICS


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


_glyphs_instance_names_to_ours = {
    "familyNames": "familyName",
    "preferredFamilyNames": "typographicFamily",
    "preferredSubfamilyNames": "typographicSubfamily",
    "styleMapFamilyNames": "styleMapFamilyName",
    "styleMapStyleNames": "styleMapStyleName",
    "styleNames": "styleName",
}
# These are things which are core metrics both for us and glyphs; other
# metrics which we believe to be metrics are stored by Glyphs as custom
# parameters
shared_core_metrics = ["xHeight", "capHeight", "ascender", "descender", "italicAngle"]
custom_parameter_metrics = [x for x in CORE_METRICS if x not in shared_core_metrics]

_rename_metrics = {
    "x-height": "xHeight",
    "cap height": "capHeight",
    "italic angle": "italicAngle",
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


# Taken from glyphsLib
LANGUAGE_MAPPING = {
    "dflt": None,
    "AFK": 0x0436,
    "ARA": 0x0C01,
    "ASM": 0x044D,
    "AZE": 0x042C,
    "BEL": 0x0423,
    "BEN": 0x0845,
    "BGR": 0x0402,
    "BRE": 0x047E,
    "CAT": 0x0403,
    "CSY": 0x0405,
    "DAN": 0x0406,
    "DEU": 0x0407,
    "ELL": 0x0408,
    "ENG": 0x0409,
    "ESP": 0x0C0A,
    "ETI": 0x0425,
    "EUQ": 0x042D,
    "FIN": 0x040B,
    "FLE": 0x0813,
    "FOS": 0x0438,
    "FRA": 0x040C,
    "FRI": 0x0462,
    "GRN": 0x046F,
    "GUJ": 0x0447,
    "HAU": 0x0468,
    "HIN": 0x0439,
    "HRV": 0x041A,
    "HUN": 0x040E,
    "HVE": 0x042B,
    "IRI": 0x083C,
    "ISL": 0x040F,
    "ITA": 0x0410,
    "ITA": 0x0410,
    "IWR": 0x040D,
    "JPN": 0x0411,
    "KAN": 0x044B,
    "KAT": 0x0437,
    "KAZ": 0x043F,
    "KHM": 0x0453,
    "KOK": 0x0457,
    "LAO": 0x0454,
    "LSB": 0x082E,
    "LTH": 0x0427,
    "LVI": 0x0426,
    "MAR": 0x044E,
    "MKD": 0x042F,
    "MLR": 0x044C,
    "MLY": 0x043E,
    "MNG": 0x0352,
    "MTS": 0x043A,
    "NEP": 0x0461,
    "NLD": 0x0413,
    "NOB": 0x0414,
    "ORI": 0x0448,
    "PAN": 0x0446,
    "PAS": 0x0463,
    "PLK": 0x0415,
    "PTG": 0x0816,
    "PTG-BR": 0x0416,
    "RMS": 0x0417,
    "ROM": 0x0418,
    "RUS": 0x0419,
    "SAN": 0x044F,
    "SKY": 0x041B,
    "SLV": 0x0424,
    "SQI": 0x041C,
    "SRB": 0x081A,
    "SVE": 0x041D,
    "TAM": 0x0449,
    "TAT": 0x0444,
    "TEL": 0x044A,
    "THA": 0x041E,
    "TIB": 0x0451,
    "TRK": 0x041F,
    "UKR": 0x0422,
    "URD": 0x0420,
    "USB": 0x042E,
    "UYG": 0x0480,
    "UZB": 0x0443,
    "VIT": 0x042A,
    "WEL": 0x0452,
    "ZHH": 0x0C04,
    "ZHS": 0x0804,
    "ZHT": 0x0404,
}

REVERSE_LANGUAGE_MAPPING = {v: k for v, k in LANGUAGE_MAPPING.items()}


def _to_name_langID(language):
    if language not in LANGUAGE_MAPPING:
        raise ValueError(f"Unknown name language: {language}")
    return LANGUAGE_MAPPING[language]


def _to_glyphs_language(langID):
    if langID not in REVERSE_LANGUAGE_MAPPING:
        raise ValueError(f"Unknown name langID: {langID}")
    return REVERSE_LANGUAGE_MAPPING[langID]


def labels_to_feature(labels):
    feature_names = []
    for label in labels:
        langID = _to_name_langID(label["language"])
        name = label["value"]
        if name == "":
            continue
        name = name.replace("\\", r"\005c").replace('"', r"\0022")
        if langID is None:
            feature_names.append(f'  name "{name}";')
        else:
            feature_names.append(f'  name 3 1 0x{langID:X} "{name}";')
    if feature_names:
        feature_names.insert(0, "featureNames {")
        feature_names.append("};")
    return feature_names
