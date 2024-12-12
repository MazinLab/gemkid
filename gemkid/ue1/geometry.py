#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from .layers import ATA_NB, HF, HF_CONTACT
from ..layers import DrawingLayer

from ..geometry import FeedlineConfig
from .. import mecstyle


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorDoubledConfig):
    legs: int = 4
    leg_gap: float = 2.0
    leg_length: float = 40.0
    leg_width: float = 4.0
    leg_landing: float = 1.5
    leg_layer: DrawingLayer = HF
    wiring_width: float = 4.0
    wiring_gap: float = 2.0
    wiring_layer: DrawingLayer = ATA_NB
    via_over: float = 1.0
    via_width: float = 1.0
    via_layer: DrawingLayer = HF_CONTACT

    def draw(self, port_offset=0, variation_layer=None, cellcache=...):
        c = super().draw(port_offset, variation_layer, cellcache)
        c.add(
            gdstk.rectangle(
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    - self.leg_landing / 2
                    - self.via_width / 2,
                    (self.wiring_width - self.leg_width) / 2 - self.via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    - self.leg_landing / 2
                    + self.via_width / 2,
                    self.dimensions[1] + self.via_over,
                ),
                *self.via_layer,
            ),
            gdstk.rectangle(
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.leg_landing / 2
                    - self.via_width / 2
                    + self.leg_length,
                    (self.wiring_width - self.leg_width) / 2 - self.via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.leg_landing / 2
                    + self.via_width / 2
                    + self.leg_length,
                    self.dimensions[1] + self.via_over,
                ),
                *self.via_layer,
            ),
        )
        return c


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 38
    leg_gap: float = 2
    leg_length: tuple[float, float] = (122 + 222 + 218 - 150, 100 + 120)
    leg_width: float = 2
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = ATA_NB
    wiring_width: float = 2.0
    wiring_layer: DrawingLayer = ATA_NB
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig = FeedlineConfig(feed_layer=ATA_NB, ground_layer=ATA_NB)
    coupler_width: float = 2.0
    coupler_gap: float = 2.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = ATA_NB
    coupler_via: Optional[mecstyle.ViaWire] = (
        None  # mecstyle.ViaWire(2.0, HF, False, 2.0, 2.0, ATA_NB, 2.0, 2.0, HF_CONTACT)
    )
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = ATA_NB
    width: float = 444
    height: float = 222


if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("ue1example.gds")
    top = gdstk.Cell("tm4top4ph")

    b = BoxConfig(InductorConfig(), CapacitorConfig(), FeedlineConfig())
    caps = np.linspace(0.1, 1.0, 18, endpoint=True).reshape((9, 2))
    coups = np.ones_like(caps)
    coups[::][::] = 0.25

    flstub = FeedlineConfig().draw(222, ports=([], []))
    flstubmini = FeedlineConfig().draw(4, ports=([], []))

    flstub.add(gdstk.rectangle((FeedlineConfig().width_half, 0), (444, 222), *ATA_NB))
    flstub.add(gdstk.rectangle((-FeedlineConfig().width_half, 0), (-444, 222), *ATA_NB))

    flstubmini.add(gdstk.rectangle((FeedlineConfig().width_half, 0), (444, 4), *ATA_NB))
    flstubmini.add(
        gdstk.rectangle((-FeedlineConfig().width_half, 0), (-444, 4), *ATA_NB)
    )
    flstub.name = "flstub"
    flstubmini.name = "flstubmini"

    for i in range(9):
        left = b.draw(capacitor_tunable=caps[i][0], coupler_tunable=coups[i][0])
        right = b.draw(capacitor_tunable=caps[i][1], coupler_tunable=coups[i][1])
        left.name = "left-cap{}-coup{}".format(caps[i, 0], coups[i, 0])
        right.name = "right-cap{}-coup{}".format(caps[i, 1], coups[i, 1])

        top.add(gdstk.Reference(flstub, origin=(0, (2 * i + 1) * 222)))
        top.add(gdstk.Reference(left, origin=(0, 2 * i * 222)))
        top.add(
            gdstk.Reference(
                right, origin=(0, 2 * i * 222), x_reflection=True, rotation=np.pi
            )
        )
        lib.add(left, right)

    rect_right = gdstk.rectangle((222 * 2, 0), (3000, 4000), *ATA_NB)
    rect_left = gdstk.rectangle((-222 * 2, 0), (-3000, 4000), *ATA_NB)
    for i in range(0, 8):
        for j in range(0, 6):
            rect_right = gdstk.boolean(
                rect_right,
                gdstk.regular_polygon(
                    (
                        222 * 2 + j * 222 + b.focus_point[0],
                        222 + i * 444 + (j % 2) * 222 + b.focus_point[1],
                    ),
                    50,
                    6,
                ),
                "not",
            )
            rect_left = gdstk.boolean(
                rect_left,
                gdstk.regular_polygon(
                    (
                        -222 * 2 - j * 222 - 222 + b.focus_point[0],
                        222 + i * 444 + ((j + 1) % 2) * 222 + b.focus_point[1],
                    ),
                    50,
                    6,
                ),
                "not",
            )

    rect_left = gdstk.boolean(
        rect_left, gdstk.rectangle((-3000, 0), (-3000 + 177.8 * 8, 190.5 * 8)), "not"
    )

    milo = [
        p.scale(8).translate(-3000, 0)
        for p in gdstk.read_gds("./milo.gds")["TOP"].polygons
    ]
    rect_left = gdstk.boolean(rect_left, milo, "or")

    top.add(gdstk.Reference(flstubmini, origin=(0, 3996)))
    # top.add(gdstk.rectangle((222, 0), (222 * 2, 4000), *ATA_NB))
    # top.add(gdstk.rectangle((-222, 0), (-222 * 2, 4000), *ATA_NB))
    top.add(*rect_right, *rect_left)
    top.add(
        *gdstk.boolean(
            milo,
            milo,
            "or",
            layer=HF_CONTACT.gds_layer[0],
            datatype=HF_CONTACT.gds_layer[1],
        )
    )
    top.add(
        *gdstk.boolean(
            milo, milo, "or", layer=HF.gds_layer[0], datatype=HF.gds_layer[1]
        )
    )

    endcap = gdstk.Cell("endcap")
    ec = gdstk.rectangle((-3000, 0), (3000, 1000), *ATA_NB)
    f = FeedlineConfig()
    m = (32 + 16)
    outline = gdstk.Polygon(
        [
            (-(f.a + f.b), 1000),
            (-(f.a + f.b), 900),
            (-(f.a + f.b) * m, 600),
            (-(f.a + f.b) * m, 600 - (f.a + f.b * 0.5) * m * 2),
            ((f.a + f.b) * m, 600 - (f.a + f.b * 0.5) * m * 2),
            ((f.a + f.b) * m, 600),
            ((f.a + f.b), 900),
            ((f.a + f.b), 1000),
            ((f.a), 1000),
            ((f.a), 900),
            ((f.a) * m, 600),
            ((f.a) * m, 600 - (f.a) * m * 2),
            (-(f.a) * m, 600 - (f.a) * m * 2),
            (-(f.a) * m, 600),
            (-(f.a), 900),
            (-(f.a), 1000),
        ],
        *HF,
    )
    outline = gdstk.boolean(ec, outline, "not")
    outline = gdstk.boolean(outline, gdstk.text("4 pH/sq", 250, (-2750, 250)), "not")
    endcap.add(*outline)
    top.add(gdstk.Reference(endcap, (0, -1000)))
    top.add(gdstk.Reference(endcap, (0, 5000), rotation=np.pi))
    
    lib.add(top)
    lib.add(flstub, flstubmini)
    lib.add(endcap)

    lib.write_gds("ue1example.gds")
