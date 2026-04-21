#!/usr/bin/env python3
import gdstk
import numpy as np

from dataclasses import dataclass
from typing import Optional

from .layers import NB
from ..layers import DrawingLayer

from .. import mecstyle
from .. import geometry


def unionize(polys, layer, datatype):
    members = [p for p in polys if p.layer == layer and p.datatype == datatype]
    return gdstk.boolean(members, [], "or", 0.0001, layer, datatype)


@dataclass(eq=True, frozen=True)
class ViaWire(mecstyle.ViaWire):
    bridge_width: float = 4
    bridge_layer: tuple[int, int] | DrawingLayer = NB
    bridge_land: bool = True
    landing_width: float = 4
    landing_length: float = 18
    landing_layer: tuple[int, int] | DrawingLayer = NB
    via_width: float = 3
    via_length: float = 15
    via_layer: tuple[int, int] | DrawingLayer = NB

@dataclass(eq=True, frozen=True)
class UEFeedlineConfig(geometry.FeedlineConfig):
    a: float = 30.5
    b: float = 13.5
    c: float = 10.0
    feed_layer: tuple[int, int] | DrawingLayer = NB
    ground_layer: tuple[int, int] | DrawingLayer = NB


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorDoubledConfig):
    legs: int = 8
    leg_gap: float = 2.0
    leg_length: float = 62.
    leg_width: float = 4.0
    leg_landing: float = 8
    leg_layer: DrawingLayer = NB
    wiring_width: float = 4.0
    wiring_gap: float = 2.0
    wiring_layer: DrawingLayer = NB
    wiring_extra: float = 8.0
    wiring_extra_height: float = 0

@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 80
    leg_gap: float = 2
    leg_length: tuple[float, float] = (270, 360)
    leg_width: float = 2
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = NB
    wiring_width: float = 8.0
    wiring_layer: DrawingLayer = NB
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: UEFeedlineConfig = UEFeedlineConfig(feed_layer=NB, ground_layer=NB)
    coupler_width: float = 2.0
    coupler_gap: float = 3.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = None
    box_width: float = 2.0
    box_gap: float = 2.0
    box_layer: DrawingLayer = NB
    width: float = 444
    height: float = 444
    extended_coupler_pullback: bool = False
    double_coupler: bool = True

if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("nbkid")
    b = BoxConfig(InductorConfig(), CapacitorConfig())
    bd = b.draw(coupler_tunable=0, capacitor_tunable=0, cellcache={}).copy(name="5GHzKID")

    top = gdstk.Cell("top")
    top.add(gdstk.Reference(bd))


    lib.add(top, bd)
    lib.write_gds("nbkid.gds")
