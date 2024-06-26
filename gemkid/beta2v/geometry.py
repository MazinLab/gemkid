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
    wiring_width: float = 10.0
    wiring_layer: DrawingLayer = BTA
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig()
    coupler_width: float = 2.0
    coupler_gap: float = 4.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = mecstyle.ViaWire(5.0, AL, True, 11.0, 9.0, NB, 8.0, 6.0, VIA)
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 150
    height: float = 150
    crossover_via: mecstyle.ViaWire = mecstyle.ViaWire(5.0, AL, True, 9.0, 11.0, NB, 6.0, 8.0, VIA)

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
        xa = self.feedline.a + self.feedline.b
        xb = -xa
        y = self.crossover_via.landing_width / 2
        if feedline_crossover:
            box.add(*self.crossover_via.draw_polys((xa, y), (xb, y)))

        return drawres


if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("Beta2VExamples")

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
    lib.write_gds("b2vexample.gds")
