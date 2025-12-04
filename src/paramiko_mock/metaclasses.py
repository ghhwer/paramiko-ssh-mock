"""
Metaclasses simply define the behavior of classes. They are the classes of classes.
"""


# Singleton
class SingletonMeta(type):
    """
    SingletonMeta is a metaclass that ensures that only one instance of a class
    is created.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
