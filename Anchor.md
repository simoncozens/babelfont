---
title: Anchor
---
Anchor(x: int, y: int, name: str, _formatspecific: dict = <factory>, _: dict = None)
## Anchor.x

* Python type: `int`

* **Required field**




## Anchor.y

* Python type: `int`

* **Required field**




## Anchor.name

* Python type: `str`

* **Required field**




## Anchor._formatspecific

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



