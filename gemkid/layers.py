import abc
from io import UnsupportedOperation

from typing import Optional, Any
from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class DrawingLayer:
    gds_layer: tuple[int, int]
    name: str

    def __iter__(self):
        return iter(self.gds_layer)

    def __str__(self):
        return self.name


@dataclass(frozen=True, eq=True)
class FabLayer:
    invert: bool = False
