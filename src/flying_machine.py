from enum import Enum

from src.Enums.data_annotations import DataPrimitive


class _FlyingMachineDP(DataPrimitive):

    @staticmethod
    def new(footprint: list[list[bool]], *,
            pretty_print: str):
        return ()


class FlyingMachineEnum(Enum):
    @_FlyingMachineDP
    def __new__(cls, footprint: list[list[bool]], pretty_print: str):
        obj = object.__new__(cls)
        obj._value_ = name
        obj.canon_name = name
        obj.footprint =
        obj.int_value = int_value
        obj.pretty_print = pretty_print
        return obj

    MANGO_MACHINE = _FlyingMachineDP(
        footprint = [[True, True,]],
        pushed_blocks
    )


class Axis(Enum):
    Horizontal = 0,
    Vertical = 1,


class FlyingMachine:

    def __init__(self,
                 name: str,
                 axes: list[Axis],
                 uses_qc: bool,
                 tileable: bool,
                 length: int,
                 trigger_delay: int,
                 engine_footprint: list[list[bool]],
                 pushed_blocks_footprints: dict[int, list[list[bool]]] = None,
                 pushed_blocks: dict[int, int] = None,
                 attached_blocks_footprints: dict[int, list[list[bool]]] = None,
                 attached_blocks: dict[int, int] = None,
                 pulled_blocks_footprints: dict[int, list[list[bool]]] = None,
                 pulled_blocks: dict[int, int] = None):
        # Deal with mutable default arguments
        if pushed_blocks_footprints is None: pushed_blocks_footprints = {}
        if attached_blocks_footprints is None: attached_blocks_footprints = {}
        if pulled_blocks_footprints is None: pulled_blocks_footprints = {}
        if pushed_blocks is None: pushed_blocks = {}
        if attached_blocks is None: attached_blocks = {}
        if pulled_blocks is None: pulled_blocks = {}

        self.name = name
        self.axes = axes
        self.uses_qc = uses_qc
        self.tileable = tileable
        self.length = length
        self.trigger_delay = trigger_delay
        self.engine_footprint = engine_footprint
        self.pushed_blocks_footprints: dict[int, list[list[bool]]] = pushed_blocks_footprints
        self.attached_blocks_footprints: dict[int, list[list[bool]]] = attached_blocks_footprints
        self.pulled_blocks_footprints: dict[int, list[list[bool]]] = pulled_blocks_footprints
        self.pushed_blocks: dict[int, int] = pushed_blocks
        self.attached_blocks: dict[int, int] = attached_blocks
        self.pulled_blocks: dict[int, int] = pulled_blocks


FlyingMachine(
    name = 'MangoMachine',
    axes = [Axis.Horizontal, Axis.Vertical],
    uses_qc = False,
    tileable = True,
    length = 8,
    trigger_delay = 0,
    engine_footprint = [[True, True]],
    pushed_blocks_footprints = {1: [[True, True]]},
    pushed_blocks = {1: 2},
    attached_blocks_footprints = {1: [[False, True]]},
    attached_blocks = {1: 6},
    )

FlyingMachine(
    name = 'MangoMachineAttached',
    axes = [Axis.Horizontal, Axis.Vertical],
    uses_qc = False,
    tileable = True,
    length = 8,
    trigger_delay = 0,
    engine_footprint = [[True, True]],
    attached_blocks_footprints = {1: [[True, False]],
                                  2: [[False, True]]},
    attached_blocks = {1: 2, 2: 6},
)

FlyingMachine(
    name = 'LShapeDoublePusher',
    axes = [Axis.Horizontal, Axis.Vertical],
    uses_qc = True,
    tileable = False,
    length = 9,
    trigger_delay = 0,
    engine_footprint = [[True, True],
                       [False, True]],
    pushed_blocks_footprints = {1: [[False, True],
                                    [False, False]],
                                2: [[False, False],
                                    [False, True]]},
    pushed_blocks = {1: 11, 2: 11},
    attached_blocks_footprints = {1: [[True, False],
                                      [False, False]],
                                  2: [[False, True],
                                      [False, True]]},
    attached_blocks = {1: 6, 2: 1},
)

FlyingMachine(
    name = 'SingleColumnPusher',
    axes = [Axis.Horizontal],
    uses_qc = True,
    tileable = False,  # Technically it is tileable, but it's beyond stupid to use the machine in that scenario
    length = 10,
    engine_footprint = [[True],
                        [True],
                        [False],
                        [True]],
    attached_blocks_footprints = {1: [[True],
                                      [False],
                                      [False],
                                      [False]]},  # It can technically have attachments here, but doing so is stupid
    attached_blocks = {1: 2},
)

FlyingMachine(
    name='SingleColumnPusherSideways',
    axes = [Axis.Horizontal],
    uses_qc = True,
    tileable = True,  # For this machine, if you mirror it, there are scenarios where tiling is not stupid
    length = 10,
    engine_footprint = [[False, True, True],
                        [True, False, False]],
    attached_blocks_footprints = {1: [[False, False, True],
                                     [False, False, False]]},
    attached_blocks = {1: 2},
)
