import inspect
from abc import ABC, abstractmethod, ABCMeta
from collections import OrderedDict
from functools import wraps
from typing import Callable


class DPMeta(ABCMeta):

    def __new__(mcs, classname, bases, classdict, **kwargs):
        cls = super().__new__(mcs, classname, bases, classdict, **kwargs)
        if func_new := classdict.get('new'):
            # Store the parameters of the new function defined in the data primitive for use in __calL__
            cls._parameters = OrderedDict((name, param.annotation)
                                          for name, param
                                          in inspect.signature(func_new).parameters.items())

            signature = inspect.signature(func_new)

            # Create a replacement function for `new` that outputs the arguments as a tuple, which allows it to be
            # used to create a new enum with the enum's __new__ function:
            @wraps(func_new)
            def new(*args_, **kwargs_):
                bound = signature.bind(*args_, **kwargs_)
                bound.apply_defaults()
                return tuple(bound.arguments.values())

            # Instantiate the class with the modified `new` function.
            cls.new = new
        return cls

    def __call__(cls, func: Callable):
        # Only keep parameter name and type annotation information.
        enum_new = OrderedDict((name, param.annotation) for name, param in inspect.signature(func).parameters.items())
        head = dict([enum_new.popitem(last=False)])  # Get rid of cls, store it for a potential print
        if cls._parameters != enum_new:
            longest_name = max(len(cls.new.__qualname__), len(func.__qualname__)) + 1  # +1 is for the colon
            raise TypeError(
                f'The arguments of `{cls.new.__qualname__}` should match the arguments of `{func.__qualname__}`. '
                f'The arguments are as follows:\n'
                f'{cls.new.__qualname__ + ":":{longest_name}}\t{"":{len(str(head))}}{dict(cls._parameters)}\n'
                f'{func.__qualname__ + ":":{longest_name}}\t{head | dict(enum_new)}\n'
                f'Note that while `{func.__qualname__}` is meant to have a `cls` parameter as its first argument, '
                f'the rest of the functions\' arguments should be identical.'
            )
        return func


class DataPrimitive(ABC, metaclass=DPMeta):
    @staticmethod
    @abstractmethod
    def new(*args): ...
