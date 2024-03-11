---
title: Font
---
Represents a font, with one or more masters.
## Font._formatspecific

* Python type: `dict`


Each object in Babelfont has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the Babelfont-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).



## Font.upm

* Python type: `int`

The font's units per em.
*If not provided, defaults to* `1000`.


## Font.version

* Python type: `(int, int)`

* Babelfont-JSON type: `[int,int]`

Font version number as a tuple of integers (major, minor).
*If not provided, defaults to* `(1, 0)`.


## Font.axes

* Python type: [[`Axis`](Axis.html)]

* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.

A list of axes, in the case of variable/multiple master font. May be empty.


## Font.instances

* Python type: [[`Instance`](Instance.html)]

* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.

A list of named/static instances.


## Font.masters

* Python type: [[`Master`](Master.html)]

* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.

A list of the font's masters.


## Font.glyphs

* Python type: `GlyphList`

* Babelfont-JSON type: `[dict]`

* When writing to Babelfont-JSON, this structure is stored under the separate file `glyphs.json`.

* When writing to Babelfont-JSON, each item in the list must be placed on a separate line.

A list of all glyphs supported in the font.

The `GlyphList` structure in the Python object is a dictionary with array-like
properties (or you might think of it as an array with dictionary-like properties)
containing [`Glyph`](Glyph.html) objects. The `GlyphList` may be iterated
directly, and may be appended to, but may also be used to index a `Glyph` by
its name. This is generally what you want:

```Python

for g in font.glyphs:
    assert isinstance(g, Glyph)

font.glyphs.append(newglyph)

glyph_ampersand = font.glyphs["ampersand"]
```
            


## Font.note

* Python type: `str`

Any user-defined textual note about this font.
*If not provided, defaults to* `None`.


## Font.date

* Python type: `datetime`

* Babelfont-JSON type: `str`

The font's date. When writing to Babelfont-JSON, this
should be stored in the format `%Y-%m-%d %H:%M:%S`. *If not provided, defaults
to the current date/time*.


## Font.names

* Python type: [`Names`](Names.html)




## Font.customOpenTypeValues

* Python type: [[`OTValue`](OTValue.html)]

Any values to be placed in OpenType tables on export to override defaults


## Font.features

* Python type: `FontFeatures`

A representation of the font's OpenType features


