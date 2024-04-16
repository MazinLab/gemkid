from typing import Optional
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

@dataclass(frozen=True, eq=True)
class SonnetPlanarGeneral:
    rdc: float # Ohm/sq
    rrf: float # Ohm*sqrt(Hz)/sq
    xdc: float # Ohm/sq
    ls: float  # pH/sq

@dataclass(frozen=True, eq=True)
class SonnetBrickCond:
    erel: float | tuple[float, float, float]
    tan: float | tuple[float, float, float]
    cond: float | tuple[float, float, float]

    def anisotropic(self):
        if type(erel) is tuple:
            if not (erel[0] == erel[1] and erel[0] == erel[2]):
                return True
        if type(tan) is tuple:
            if not (tan[0] == tan[1] and tan[0] == tan[2]):
                return True
        if type(cond) is tuple:
            if not (cond[0] == cond[1] and cond[0] == cond[2]):
                return True

        return False

@dataclass(frozen=True, eq=True)
class SonnetLayer(DrawingLayer):
    level: int
    properties: SonnetPlanarGeneral | SonnetBrickCond
    thickness: Optional[float] = None
    
