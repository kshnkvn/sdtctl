from typing import Any, Self

from dbus_next.signature import Variant
from pydantic import BaseModel, Field


class DBusVariantValue(BaseModel):
    """Wrapper for D-Bus variant values.
    """
    model_config = {'frozen': True, 'arbitrary_types_allowed': True}

    value: Any = Field(..., description='The wrapped D-Bus variant value')

    @classmethod
    def from_dbus_variant(cls, variant: Variant | Any | None) -> Self:
        """Create instance from D-Bus variant.

        Args:
            variant: The D-Bus variant to extract value from

        Returns:
            DBusVariantValue instance with extracted value
        """
        if variant and hasattr(variant, 'value'):
            return cls(value=variant.value)
        return cls(value=variant if variant is not None else 0)

    @staticmethod
    def to_dbus_variant(value: Any, signature: str = 'v') -> Variant:
        """Convert a Python value to a D-Bus variant.

        Args:
            value: The Python value to convert
            signature: The D-Bus signature (default: 'v' for variant)

        Returns:
            D-Bus Variant object
        """
        if signature == 'v':
            return Variant('v', value)
        return Variant(signature, value)
