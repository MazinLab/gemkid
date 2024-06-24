#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..beta2.layers import BTA, NB, AL, VIA
from ..layers import DrawingLayer

from ..geometry import FeedlineConfig
from .. import mecstyle


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorConfig):
    legs: int = 4
    leg_gap: float = 0.5
    leg_length: float = 24.0
    leg_width: float = 4.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 4
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = BTA


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 38
    leg_gap: float = 1.0
    leg_length: tuple[float, float] = (101, 55)
    leg_width: float = 1.5
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 12.0
    wiring_layer: DrawingLayer = BTA
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=NB, ground_layer=NB, a=4.5, b=2.0, c=2.0)
    coupler_width: float = 2.0
    coupler_gap: float = 1.0
    coupler_fill: bool = True
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = mecstyle.ViaWire(5.0, AL, True, 11.0, 9.0, NB, 8.0, 6.0, VIA)
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 150
    height: float = 150


if __name__ == "__main__":
    lib = gdstk.Library("b2vexample.gds")
    b = BoxConfig(InductorConfig(), CapacitorConfig())
    eb = BoxConfig(None, None)
    lib.add(b.draw(coupler_tunable=0.5, capacitor_tunable=0.5), eb.draw())
    lib.write_gds("b2example.gds")
