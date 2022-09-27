from typing import IO, Iterator

from src.Analyzers.geode import Geode
from src.Enums.geode_enum import GeodeEnum
from src.cell import Cell


def geode_generator() -> Iterator[Geode]:
    geode = []
    row = 0
    with open('geodes.txt', 'r') as geode_file:
        while line := geode_file.readline():
            if line == '\n':
                yield Geode(geode)
                geode = []
                row = 0
            else:
                geode.append([Cell(row, col,
                                   GeodeEnum.OBSIDIAN if char == '#'
                                   else GeodeEnum.PUMPKIN if char == '.'
                                   else GeodeEnum.AIR)
                              for col, char in enumerate(line[:-1:2])])
                row += 1
