from __future__ import annotations

from aenum import Enum
from colorama import Fore, Back, Style

from src.Enums.data_annotations import DataPrimitive

class _GeodeDP(DataPrimitive):

    @staticmethod
    def new(int_value: int, *,
            pretty_print: str):
        return ()


class GeodeEnum(Enum):
    @_GeodeDP
    def __new__(cls, int_value: int, pretty_print: str):
        obj = object.__new__(cls)
        obj._value_ = int_value
        obj.int_value = int_value
        obj.pretty_print = pretty_print
        return obj

    AIR = _GeodeDP.new(
        int_value=0,
        pretty_print=f'{Style.RESET_ALL}  ')
    PUMPKIN = _GeodeDP.new(
        int_value=1,
        pretty_print=f'{Back.YELLOW}..{Style.RESET_ALL}')
    OBSIDIAN = _GeodeDP.new(
        int_value=2,
        pretty_print=f'{Back.BLACK}##{Style.RESET_ALL}')

    BRIDGE = _GeodeDP.new(
        int_value=3,
        pretty_print=f'{Back.LIGHTBLACK_EX}++{Style.RESET_ALL}')

    def __str__(self):
        return self.pretty_print
