#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from .layers import ATA_NB, HF
from ..layers import DrawingLayer

from ..geometry import FeedlineConfig
from .. import mecstyle


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorConfig):
    legs: int = 15
    leg_gap: float = 0.5
    leg_length: float = 102.5
    leg_width: float = 1.5
    leg_landing: float = 1.5
    leg_layer: DrawingLayer = HF
    wiring_width: float = 2
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = ATA_NB


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 46
    leg_gap: float = 1
    leg_length: tuple[float, float] = (114, 62)
    leg_width: float = 1
    leg_landing: float = 0
    leg_layer: DrawingLayer = ATA_NB
    wiring_width: float = 5
    wiring_layer: DrawingLayer = ATA_NB


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=ATA_NB, ground_layer=ATA_NB)
    coupler_width: float = 1.5
    coupler_gap: float = 2.0
    coupler_layer: DrawingLayer = ATA_NB
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = ATA_NB
    width: float = 150
    height: float = 150


if __name__ == "__main__":
    lib = gdstk.Library("ue1example.gds")
    b = BoxConfig(InductorConfig(), CapacitorConfig(), FeedlineConfig())
    eb = BoxConfig(None, None, FeedlineConfig())
    lib.add(b.draw(coupler_tunable=0.5, capacitor_tunable=0.5), eb.draw())
    lib.write_gds("ue1example.gds")
