#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from .layers import NB
from ..layers import DrawingLayer

from .. import geometry
from .. import mecstyle

FB = 3.00


@dataclass(eq=True, frozen=True)
class FeedlineConfig(geometry.FeedlineConfig):
    a: float = 40
    b: float = FB
    c: float = 10 - FB
    feed_layer: tuple[int, int] | DrawingLayer = NB
    ground_layer: tuple[int, int] | DrawingLayer = NB


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorConfig):
    legs: int = 32
    leg_gap: float = 2.0
    leg_length: float = 100.0
    leg_width: float = 2.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = NB
    wiring_width: float = 4.0
    wiring_gap: float = 4.0
    wiring_layer: DrawingLayer = NB


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 64
    leg_gap: float = 2.0
    leg_length: tuple[float, float] = (140, 75)
    leg_width: float = 2.0
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = NB
    wiring_width: float = 4.0
    wiring_layer: DrawingLayer = NB
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=NB, ground_layer=NB)
    coupler_width: float = 2.0
    coupler_gap: float = 4.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = NB
    coupler_via: Optional[mecstyle.ViaWire] = None
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = NB
    width: float = 220
    height: float = 440


def bondpad(width, leadlength, fl):
    center = fl.a * 2
    gap = fl.b
    edge = fl.c

    ratio = width / center

    strip = gdstk.Polygon(
        [
            (-fl.a, 0),
            (+fl.a, 0),
            (+width / 2, -leadlength),
            (+width / 2, -leadlength - width),
            (-width / 2, -leadlength - width),
            (-width / 2, -leadlength),
        ]
    )

    outside = gdstk.Polygon(
        [
            (-(fl.a + fl.b), 0),
            (-(fl.a + fl.b + fl.c) * ratio, 0),
            (
                -(fl.a + fl.b + fl.c) * ratio,
                -leadlength - width - (fl.b + fl.c) * ratio,
            ),
            (
                +(fl.a + fl.b + fl.c) * ratio,
                -leadlength - width - (fl.b + fl.c) * ratio,
            ),
            (+(fl.a + fl.b + fl.c) * ratio, 0),
            (+(fl.a + fl.b), 0),
            (+(fl.a + fl.b) * ratio, -leadlength),
            (+(fl.a + fl.b) * ratio, -leadlength - width - fl.b * ratio),
            (-(fl.a + fl.b) * ratio, -leadlength - width - fl.b * ratio),
            (-(fl.a + fl.b) * ratio, -leadlength),
        ]
    )

    return [strip, outside]


if __name__ == "__main__":
    import numpy as np

    from ..anvilcpw import geometry as cg

    lib = gdstk.Library("Anvil Devices Devices")
    b = BoxConfig(InductorConfig(), CapacitorConfig(), FeedlineConfig())
    b50 = b.draw(
        coupler_tunable=0.0, capacitor_tunable=0.50, flatten=True, cellcache={}
    ).copy("anv50")
    b100 = b.draw(
        coupler_tunable=1.0, capacitor_tunable=1.00, flatten=True, cellcache={}
    ).copy("anv100")

    cpw = cg.CPWConfig(cg.FeedlineConfig()).draw()
    
    endcap = gdstk.Cell("endcap")
    endcap.add(*bondpad(150.0, 75.0, FeedlineConfig()))

    fl = FeedlineConfig().draw_half(440 * 2, ports=[])

    flin = FeedlineConfig().draw(2.5, ports=([], []))
    flout = FeedlineConfig().draw(1750 - 225 * 2 - 440 * 2 - 2.5, ports=([], []))

    top = gdstk.Cell("top")
    top.add(gdstk.Reference(endcap, (0, 225)))
    top.add(gdstk.Reference(flin, (0, 225)))
    top.add(gdstk.Reference(b50, (0, 227.5)))
    top.add(gdstk.Reference(b100, (0, 227.5 + 440)))
    top.add(gdstk.Reference(fl, (0, 227.5), x_reflection=True, rotation=np.pi))
    top.add(gdstk.Reference(flout, (0, 227.5 + 2*440)))
    top.add(gdstk.Reference(cpw, (0, 227.5 + 2*440)))
    top.add(gdstk.Reference(endcap, (0, 1750-225), rotation=np.pi))

    top.add(gdstk.rectangle((FeedlineConfig().width_half, 225), (93.75 + 200, 227.5)))
    top.add(gdstk.rectangle((FeedlineConfig().width_half, 1750-225), (93.75 + 200, 1750-227.5)))
    top.add(gdstk.rectangle((93.75, -18.75), (93.75 + 200, 225)))
    top.add(gdstk.rectangle((93.75, 1750 + 18.75), (93.75 + 200, 1750-225)))
    top.add(gdstk.rectangle((229, 227.5), (93.75 + 200, 1750-227.5)))
    top.add(gdstk.rectangle((220, 227.5), (229, 227.5 + 880)))

    lib.add(top, b50, b100, fl, endcap, cpw, flin, flout)
    lib.write_gds("anvmec.gds")
