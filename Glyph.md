---
title: Glyph
---
Glyph(name: str, production_name: str = None, category: str = 'base', codepoints: [<class 'int'>] = <factory>, layers: [<class 'babelfont.Layer.Layer'>] = <factory>, exported: bool = True, direction: str = 'LTR', _formatspecific: dict = <factory>, _: dict = None)
* When writing to NFSF-JSON, this class must be serialized without newlines
## Glyph.name

* Python type: `str`

* **Required field**




## Glyph.production_name

* Python type: `str`


*If not provided, defaults to* `None`.


## Glyph.category

* Python type: `str`


*If not provided, defaults to* `base`.


## Glyph.codepoints

* Python type: `[int]`




## Glyph.layers

* Python type: [[`Layer`](Layer.html)]




## Glyph.exported

* Python type: `bool`


*If not provided, defaults to* `True`.


## Glyph.direction

* Python type: `str`


*If not provided, defaults to* `LTR`.


## Glyph._formatspecific

* Python type: `dict`


Each object in NFSF has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the NFSF-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).



