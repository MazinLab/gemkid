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
    legs: int = 16
    leg_gap: float = 0.5
    leg_length: float = 24.0
    leg_width: float = 1.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = BTA
    wiring_width: float = 1
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = BTA


@dataclass(eq=True, frozen=True)
class CapacitorPPConfig(geometry.GeomConfigMarker):
    legs: int = 3
    leg_via: mecstyle.ViaWire = mecstyle.ViaWire(10, AL, True, 13, 14, NB, 10, 11, VIA)
    leg_length: float = 32.0 + 2 * 14.0
    leg_space: float = 0.0
    wiring_width: float = 4
    wiring_gap: float = 0.5
    wiring_layer: tuple[int, int] | DrawingLayer = NB

    @property
    def dimensions(self):
        return (
            self.leg_length,
            self.leg_via.landing_width * self.legs
            + (self.legs - 1) * self.leg_space
            + self.wiring_width
            + self.wiring_gap,
        )

    def draw(self, tunable: float, port: tuple[float, float], cellcache={}):
        assert (
            tunable >= 0 and tunable <= 1
        ), "The capacitor tunable should be a fraction of the total possible in the [0, 1]"

        dim = self.dimensions

        h = hex(abs(hash((hash(self), hash(port), hash(tunable)))))
        cellname = "CapacitorPP-{:s}".format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c

        for i in range(self.legs):
            y = dim[1] - self.leg_via.landing_width / 2 - (self.leg_via.landing_width + self.leg_space) * i
            c.add(*self.leg_via.draw_polys((0, y), (self.leg_length, y)))
        c.add(
            gdstk.rectangle((0, 0), (self.leg_via.landing_length, dim[1]), *self.wiring_layer),
            gdstk.rectangle(
                (dim[0] - self.leg_via.landing_length, self.wiring_width + self.wiring_gap),
                (dim[0], dim[1]),
                *self.wiring_layer,
            ),
        )
        c.add(
            gdstk.rectangle(
                (self.leg_via.landing_length, dim[1]),
                (dim[0] - self.leg_via.landing_length, dim[1] - self.wiring_width),
                *self.wiring_layer,
            )
        )

        plate_start = self.wiring_width + self.wiring_gap
        plate_length = (dim[1] - 2 * (self.wiring_width + self.wiring_gap)) * tunable
        c.add(
            gdstk.rectangle(
                (self.leg_via.landing_length + self.wiring_gap, plate_start),
                (dim[0] - self.leg_via.landing_length - self.wiring_gap, plate_start + plate_length),
            )
        )
        c.add(
            gdstk.rectangle(
                (self.leg_via.landing_length, 0), (port[0], self.wiring_width), *self.wiring_layer
            )
        )
        c.add(
            gdstk.rectangle(
                (port[0] + port[1], 0),
                (dim[0] - self.leg_via.landing_length - self.wiring_gap, self.wiring_width + self.wiring_gap),
                *self.wiring_layer,
            )
        )

        return c


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorPPConfig]
    feedline: FeedlineConfig = FeedlineConfig()
    coupler_width: float = 2.0
    coupler_gap: float = 1.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = None
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 150 - 70
    height: float = 150 - 70


if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("Beta2PExamples")

    b = BoxConfig(InductorConfig(), CapacitorPPConfig())
    bd = b.draw(cellcache={}).copy("withcrossover")

    eb = BoxConfig(None, None)
    ebd = eb.draw(cellcache={}).copy("emptyboxcell")

    top = gdstk.Cell("top")
    top.add(gdstk.Reference(ebd, x_reflection=True, rotation=np.pi))
    top.add(gdstk.Reference(bd))

    lib.add(top, bd, ebd)
    lib.write_gds("b2pexample.gds")
