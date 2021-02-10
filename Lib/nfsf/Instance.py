from dataclasses import dataclass, field
from .BaseObject import BaseObject, I18NDictionary


@dataclass
class _InstanceFields:
    name: I18NDictionary = field(metadata={"description": "The name of this instance."})
    location: dict = field(
        metadata={
            "description": """A dictionary mapping axis tags to coordinates in order to locate this instance in the design space."""
        }
    )


@dataclass
class Instance(BaseObject, _InstanceFields):
    """An object representing a named or static instance."""

    _write_one_line = True
