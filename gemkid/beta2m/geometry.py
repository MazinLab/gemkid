#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..beta2.layers import BTA, NB, AL, VIA
from ..layers import DrawingLayer

from .. import mecstyle
from .. import geometry


FB = 1.765


@dataclass(eq=True, frozen=True)
class FeedlineConfig(geometry.FeedlineConfig):
    a: float = 4.5
    b: float = FB
    c: float = 5.5 - FB
    feed_layer: tuple[int, int] | DrawingLayer = NB
    ground_layer: tuple[int, int] | DrawingLayer = NB


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorConfig):
    legs: int = 9
    leg_gap: float = 0.5
    leg_length: float = 16.0
    leg_width: float = 1.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 0.75
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = BTA


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 23
    leg_gap: float = 0.5
    leg_length: tuple[float, float] = (35, 35 // 2 + 1)
    leg_width: float = 0.75
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 0.75
    wiring_layer: DrawingLayer = BTA
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig()
    coupler_width: float = 0.5
    coupler_gap: float = 0.5
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = None
    box_width: float = 1.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 50
    height: float = 50


if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("Beta2MExamples")

    b = BoxConfig(InductorConfig(), CapacitorConfig())
    bd = b.draw(cellcache={}).copy("withcrossover")

    eb = BoxConfig(None, None)
    ebd = eb.draw(cellcache={}).copy("emptyboxcell")

    top = gdstk.Cell("top")
    top.add(gdstk.Reference(ebd, x_reflection=True, rotation=np.pi))
    top.add(gdstk.Reference(bd))

    lib.add(top, bd, ebd)
    lib.write_gds("b2mexample.gds")
