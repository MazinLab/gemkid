#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..ue1.layers import HF_LL, ATA_NB, HF_CONTACT
from ..layers import DrawingLayer

from . import geometry
from . import array    

@dataclass(eq=True, frozen=True)
class ViaWire(geometry.ViaWire):
    bridge_width: float = 4
    bridge_layer: tuple[int, int] | DrawingLayer = HF_LL
    bridge_land: bool = True
    landing_width: float = 4
    landing_length: float = 18
    landing_layer: tuple[int, int] | DrawingLayer = ATA_NB
    via_width: float = 3
    via_length: float = 15
    via_layer: tuple[int, int] | DrawingLayer = HF_CONTACT
    liftoff_width: float = 5
    asi_width: float = 6


@dataclass(eq=True, frozen=True)
class InductorConfig(geometry.InductorConfig):
    legs: int = 4
    leg_gap: float = 2.0
    leg_length: float = 40.0
    leg_width: float = 4.0
    leg_landing: float = 8
    leg_layer: DrawingLayer = HF_LL
    wiring_width: float = 4.0
    wiring_gap: float = 2.0
    wiring_layer: DrawingLayer = ATA_NB
    wiring_extra: float = 8.0
    wiring_extra_height: float = 10.0
    via_over: Optional[float] = None
    via_width: float = 5.0
    via_inset: float = 5
    via_gap: float = 3
    via_layer: DrawingLayer = HF_CONTACT
    litho_vias: Optional[int] = 2

@dataclass(eq=True, frozen=True)
class CapacitorConfig(geometry.CapacitorConfig):
    legs: int = 66
    leg_gap: float = 1
    leg_length: tuple[float, float] = (222 - 33 + 212, 220)
    leg_width: float = 1
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = ATA_NB
    wiring_width: float = 4.0
    wiring_layer: DrawingLayer = ATA_NB
    extra_height: float = 0.0

@dataclass(eq=True, frozen=True)
class BoxConfig(geometry.BoxConfig):
  inductor: Optional[InductorConfig]
  capacitor: Optional[CapacitorConfig]
  feedline: geometry.UEFeedlineConfig = geometry.UEFeedlineConfig(feed_layer=ATA_NB, ground_layer=ATA_NB)
  coupler_width: float = 2.0
  coupler_gap: float = 4.0
  coupler_fill: bool = False
  coupler_layer: DrawingLayer = ATA_NB
  coupler_via: Optional[geometry.mecstyle.ViaWire] = (
      None  # mecstyle.ViaWire(2.0, HF, False, 2.0, 2.0, ATA_NB, 2.0, 2.0, HF_CONTACT)
  )
  box_width: float = 2.0
  box_gap: float = 1.0
  box_layer: DrawingLayer = ATA_NB
  width: float = 444
  height: float = 222
  extended_coupler_pullback: bool = False
  double_coupler: bool = True

if __name__ == "__main__":
    import numpy as np

    variants = [
        (3, 0),
        (3, 5),
        (3, 10),
        (3, 21.5),
    ]

    lib = gdstk.Library("ue2-ll")

    for i in range(4):
        b = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            geometry.UEFeedlineConfig(),
        )

        bhqc = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            geometry.UEFeedlineConfig(),
            double_coupler=False,
            extended_coupler_pullback=True,
        )
        geometry.make_tm_variant(lib, i, b, bhqc, geometry.UEFeedlineConfig, ViaWire, "UE2 LL 20pH", variants, "ll-8ph")
        array.make_array_variant(lib, i, b, geometry.UEFeedlineConfig, ViaWire, "ll-8ph")

    lib.write_gds("ue2-ll.gds")
