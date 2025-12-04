"""
Metaclasses simply define the behavior of classes. They are the classes of classes.
"""

from typing import Any, Dict, Type


# Singleton
class SingletonMeta(type):
    """
    SingletonMeta is a metaclass that ensures that only one instance of a class
    is created.
    """
    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
