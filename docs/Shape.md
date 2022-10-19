---
title: Shape
---
Shape(ref: str = None, transform: fontTools.misc.transform.Transform = None, nodes: [<class 'babelfont.Node.Node'>] = None, closed: bool = True, direction: int = 1, _formatspecific: dict = <factory>, _: dict = None)
* When writing to Babelfont-JSON, this class must be serialized without newlines
## Shape.ref

* Python type: `str`


*If not provided, defaults to* `None`.


## Shape.transform

* Python type: `Transform`


*If not provided, defaults to* `None`.


## Shape.nodes

* Python type: `[Node]`


*If not provided, defaults to* `None`.


## Shape.closed

* Python type: `bool`


*If not provided, defaults to* `True`.


## Shape.direction

* Python type: `int`


*If not provided, defaults to* `1`.


## Shape._formatspecific

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



