#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..beta2.layers import BTA, NB
from ..layers import DrawingLayer

from ..geometry import FeedlineConfig
from .. import mecstyle


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorConfig):
    legs: int = 2
    leg_gap: float = 0.5
    leg_length: float = 32.0
    leg_width: float = 8.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 8
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = BTA


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 46
    leg_gap: float = 1.0
    leg_length: tuple[float, float] = (114, 62)
    leg_width: float = 1.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 5.0
    wiring_layer: DrawingLayer = BTA
    extra_height: float = 2.3


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=NB, ground_layer=NB)
    coupler_width: float = 1.5
    coupler_gap: float = 2.0
    coupler_fill: bool = True
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = None
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 150
    height: float = 150


if __name__ == "__main__":
    lib = gdstk.Library("b1example.gds")
    b = BoxConfig(InductorConfig(), CapacitorConfig(), FeedlineConfig())
    eb = BoxConfig(None, None, FeedlineConfig())
    lib.add(b.draw(coupler_tunable=0.5, capacitor_tunable=0.5), eb.draw())
    lib.write_gds("b1example.gds")
