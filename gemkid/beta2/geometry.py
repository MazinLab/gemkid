#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from .layers import BTA, NB, AL, VIA
from ..layers import DrawingLayer

from .. import geometry
from .. import mecstyle

FB = 2.0


@dataclass(eq=True, frozen=True)
class FeedlineConfig(geometry.FeedlineConfig):
    a: float = 3.5
    b: float = FB
    c: float = 13.5 - FB
    feed_layer: tuple[int, int] | DrawingLayer = NB
    ground_layer: tuple[int, int] | DrawingLayer = NB


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
    wiring_width: float = 11.0
    wiring_layer: DrawingLayer = BTA
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=NB, ground_layer=NB)
    coupler_width: float = 1.5
    coupler_gap: float = 1.5
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = None
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 150
    height: float = 150
    crossover_via: mecstyle.ViaWire = mecstyle.ViaWire(8 - 3, AL, True, 9, 11, NB, 6, 8, VIA)

    def draw(
        self,
        coupler_tunable: float = 1,
        capacitor_tunable: float = 1,
        variation_layer=None,
        feedline_crossover: bool = False,
        flatten=True,
        cellcache={},
    ):
        drawres = super().draw(coupler_tunable, capacitor_tunable, variation_layer, flatten, cellcache)
        box = drawres if flatten else drawres[0]
        assert type(box) is gdstk.Cell
        r = self.regions()
        x = self.feedline.a + self.feedline.b + self.crossover_via.landing_width / 2
        ya = sum(r[1][:2]) - self.crossover_via.landing_length
        yb = sum(r[1][:3]) + self.crossover_via.landing_length
        box.add(*self.crossover_via.draw_polys((x, ya), (x, yb)))
        if feedline_crossover:
            flvia = mecstyle.ViaWire(
                self.crossover_via.bridge_width,
                AL,
                True,
                self.crossover_via.landing_width,
                self.crossover_via.landing_length,
                NB,
                self.crossover_via.via_width,
                self.crossover_via.via_length,
                VIA,
            )
            y = ya + flvia.landing_width / 2
            xa = self.feedline.a + self.feedline.b
            xb = -xa
            box.add(*flvia.draw_polys((xa, y), (xb, y)))

        return drawres


if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("Beta2Examples")
    b = BoxConfig(InductorConfig(), CapacitorConfig())
    bd = b.draw(feedline_crossover=True, cellcache={}).copy("withcrossover")
    bdnc = b.draw(feedline_crossover=False, cellcache={}).copy("withoutcrossover")

    eb = BoxConfig(None, None)
    ebd = eb.draw(feedline_crossover=True, cellcache={}).copy("emptyboxcell")
    ebdnc = eb.draw(feedline_crossover=False, cellcache={}).copy("emptyboxnocrossover")

    top = gdstk.Cell("top")
    top.add(gdstk.Reference(ebd, x_reflection=True, rotation=np.pi))
    top.add(gdstk.Reference(bd))

    top.add(gdstk.Reference(ebdnc, (0, 150), x_reflection=True, rotation=np.pi))
    top.add(gdstk.Reference(bdnc, (0, 150)))

    lib.add(top, bd, bdnc, ebd, ebdnc)
    lib.write_gds("b2example.gds")
