---
title: Layer
---
Layer(id: str, width: int, name: str = None, _master: str = None, guides: [<class 'nfsf.Guide.Guide'>] = <factory>, shapes: [<class 'nfsf.Shape.Shape'>] = <factory>, anchors: [<class 'nfsf.Anchor.Anchor'>] = <factory>, color: nfsf.BaseObject.Color = None, layerIndex: int = 0, _background: str = None, isBackground: bool = False, location: [<class 'float'>] = None, _font: object = None, _formatspecific: dict = <factory>, _: dict = None)
## Layer.id

* Python type: `str`

* **Required field**




## Layer.width

* Python type: `int`

* **Required field**




## Layer.name

* Python type: `str`


*If not provided, defaults to* `None`.


## Layer._master

* Python type: `str`


*If not provided, defaults to* `None`.


## Layer.guides

* Python type: [[`Guide`](Guide.html)]




## Layer.shapes

* Python type: [[`Shape`](Shape.html)]

* When writing to NFSF-JSON, each item in the list must be placed on a separate line.




## Layer.anchors

* Python type: [[`Anchor`](Anchor.html)]




## Layer.color

* Python type: `Color`


*If not provided, defaults to* `None`.


## Layer.layerIndex

* Python type: `int`


*If not provided, defaults to* `0`.


## Layer._background

* Python type: `str`


*If not provided, defaults to* `None`.


## Layer.isBackground

* Python type: `bool`


*If not provided, defaults to* `False`.


## Layer.location

* Python type: `[float]`


*If not provided, defaults to* `None`.


## Layer._font

* Python type: `object`

* This field only exists as an attribute of the the Python object and should not be written to NFSF-JSON.


*If not provided, defaults to* `None`.


## Layer._formatspecific

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



