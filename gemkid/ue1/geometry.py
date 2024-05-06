#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from .layers import ATA_NB, HF, HF_CONTACT
from ..layers import DrawingLayer

from ..geometry import FeedlineConfig
from .. import mecstyle


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorConfig):
    legs: int = 15
    leg_gap: float = 0.5
    leg_length: float = 30.0
    leg_width: float = 2.0
    leg_landing: float = 1.5
    leg_layer: DrawingLayer = HF
    wiring_width: float = 2
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = ATA_NB
    via_over: float = 1.0
    via_inset: tuple[float, float] = (0, 0.25)
    via_layer: DrawingLayer = HF_CONTACT

    def draw(self, port_offset=0, cellcache=...):
        c = super().draw(port_offset, cellcache)
        r = self.regions()
        c.add(
            gdstk.rectangle(
                (r[0][0] - self.leg_landing + self.via_inset[0], r[1][0] - self.via_over),
                (r[0][0] - self.via_inset[1], sum(r[1][:2]) + self.via_over),
                *self.via_layer,
            ),
            gdstk.rectangle(
                (sum(r[0][:2]) + self.via_inset[1], r[1][0] - self.via_over),
                (sum(r[0][:2]) + self.leg_landing - self.via_inset[1], sum(r[1][:2]) + self.via_over),
                *self.via_layer,
            ),
        )
        return c


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 48
    leg_gap: float = 1.0
    leg_length: tuple[float, float] = (122, 68)
    leg_width: float = 1.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = ATA_NB
    wiring_width: float = 2.0
    wiring_layer: DrawingLayer = ATA_NB


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=ATA_NB, ground_layer=ATA_NB)
    coupler_width: float = 2.0
    coupler_gap: float = 0.5
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
