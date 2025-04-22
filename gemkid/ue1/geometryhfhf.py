#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from .layers import HF_GP, HF, HF_CONTACT
from ..layers import DrawingLayer

from .. import mecstyle

from .. import geometry

@dataclass(eq=True, frozen=True)
class UEFeedlineConfig(geometry.FeedlineConfig):
    a: float = 50
    b: float = 4.0
    c: float = 14
    feed_layer: tuple[int, int] | DrawingLayer = HF_GP
    ground_layer: tuple[int, int] | DrawingLayer = HF_GP

@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorDoubledConfig):
    legs: int = 4
    leg_gap: float = 4.0
    leg_length: float = 40.0
    leg_width: float = 4.0
    leg_landing: float = 8
    leg_layer: DrawingLayer = HF
    wiring_width: float = 4.0
    wiring_gap: float = 4.0
    wiring_layer: DrawingLayer = HF_GP
    wiring_extra: float = 8.0
    via_over: float = 1.0
    via_width: float = 5.0
    via_inset: float = 10.0
    via_gap: float = 3.0
    via_layer: DrawingLayer = HF_CONTACT

    def draw(self, port_offset=0, variation_layer=None, cellcache=...):
        c = super().draw(port_offset, variation_layer, cellcache)
        vias = [
            gdstk.rectangle(
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    - self.leg_landing / 2
                    - self.via_width / 2,
                    (self.wiring_width - self.leg_width) / 2 - self.via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    - self.leg_landing / 2
                    + self.via_width / 2
                    + self.via_inset,
                    self.dimensions[1] + self.via_over - self.wiring_gap,
                ),
                *self.via_layer,
            ),
            gdstk.rectangle(
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    + self.leg_landing / 2
                    - self.via_width / 2
                    - self.via_inset
                    + self.leg_length,
                    (self.wiring_width - self.leg_width) / 2 - self.via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    + self.leg_landing / 2
                    + self.via_width / 2
                    + self.leg_length,
                    self.dimensions[1] + self.via_over - self.wiring_gap,
                ),
                *self.via_layer,
            ),
        ]
        if self.via_gap > 0.0:
            cuts = []
            for i in range(self.legs * 2 + 1):
                cuts.append(
                    gdstk.rectangle(
                        (
                            0,
                            -self.via_gap / 2
                            - self.leg_gap / 2
                            + i * (self.leg_width + self.leg_gap),
                        ),
                        (
                            self.leg_length
                            + self.wiring_extra * 2
                            + self.wiring_width * 4
                            + self.wiring_gap * 4,
                            self.via_gap / 2
                            - self.leg_gap / 2
                            + i * (self.leg_width + self.leg_gap),
                        ),
                    )
                )
            vias = gdstk.boolean(vias, cuts, "not", 1e-6, *self.via_layer)
        c.add(*vias)
        return c


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 30
    leg_gap: float = 2
    leg_length: tuple[float, float] = (350, 200)
    leg_width: float = 2
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = HF_GP
    wiring_width: float = 4.0
    wiring_layer: DrawingLayer = HF_GP
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: UEFeedlineConfig = UEFeedlineConfig(feed_layer=HF_GP, ground_layer=HF_GP)
    coupler_width: float = 2.0
    coupler_gap: float = 3.5
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = HF_GP
    coupler_via: Optional[mecstyle.ViaWire] = (
        None  # mecstyle.ViaWire(2.0, HF, False, 2.0, 2.0, HF_GP, 2.0, 2.0, HF_CONTACT)
    )
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = HF_GP
    width: float = 444
    height: float = 222


if __name__ == "__main__":
    import numpy as np

    variants = [
        (5, 0),
        (5, 5),
        (5, 10),
        (5, 21.5),
    ]

    lib = gdstk.Library("ue1example.gds")

    def make_variant(variant):
        top = gdstk.Cell("tm4top8phv{:d}".format(variant))

        b = BoxConfig(InductorConfig(via_gap = variants[variant][0], via_inset=variants[variant][1]), CapacitorConfig(), UEFeedlineConfig())

        resonators = {
            4.000: [0.73197856, 0.90878911],
            4.050: [0.71284686, 0.87875065],
            4.100: [0.68130627, 0.85073245],
            4.150: [0.66046119, 0.82411372],
            4.200: [0.63939131, 0.79743912],
            4.250: [0.61321495, 0.77290264],
            4.300: [0.59376567, 0.74837067],
            6.100: [0.12483863, 0.19270513],
            6.200: [0.11326375, 0.17862476],
            6.300: [0.11146182, 0.16575926],
            6.400: [0.10876179, 0.15185539],
            7.500: [0.15668923, 0.05048538],
            7.625: [0.14961197, 0.04269477],
            7.750: [0.14384848, 0.03588802],
            7.875: [0.13871147, 0.02900486],
            8.000: [0.13429182, 0.02171761],
        }

        np.random.seed(42)
        ks = list(resonators.keys())
        index = np.arange(len(ks))
        np.random.shuffle(index)

        freq_func = lambda i: ks[index[i]]
        coup_func = lambda i: resonators[freq_func(i)][0]
        cap_func = lambda i: resonators[freq_func(i)][1]

        flstub = UEFeedlineConfig().draw(222, ports=([], []), cellcache={})
        flstubmini = UEFeedlineConfig().draw(170, ports=([], []), cellcache={})

        flstub.add(gdstk.rectangle((UEFeedlineConfig().width_half, 0), (444, 222), *HF_GP))
        flstub.add(gdstk.rectangle((-UEFeedlineConfig().width_half, 0), (-444, 222), *HF_GP))

        flstubmini.add(gdstk.rectangle((UEFeedlineConfig().width_half, 0), (444, 170), *HF_GP))
        flstubmini.add(
            gdstk.rectangle((-UEFeedlineConfig().width_half, 0), (-444, 170), *HF_GP)
        )
        flstub.name = "flstubv{:d}".format(variant)
        flstubmini.name = "flstubmini{:d}".format(variant)

        rect_right = gdstk.rectangle((222 * 2, 0), (2700, 3500))
        rect_right = gdstk.boolean(rect_right, gdstk.rectangle((2700-1422.4, 0), (2700, 1524)), "not")
        rect_left = gdstk.rectangle((-222 * 2, 0), (-2700, 3500))

        for i in range(8):
            left = b.draw(capacitor_tunable=cap_func(i * 2), coupler_tunable=coup_func(i * 2), cellcache={})
            right = b.draw(capacitor_tunable=cap_func(i * 2 + 1), coupler_tunable=coup_func(i * 2 + 1), cellcache={})
            left.name = "left-wide-cap{}-coup{}-f{:.04f}-v{:d}".format(cap_func(i * 2), coup_func(i * 2), freq_func(i * 2), variant)
            right.name = "right-wide-cap{}-coup{}-f{:.04f}-v{:d}".format(cap_func(i * 2 + 1), coup_func(i * 2 + 1), freq_func(i * 2 + 1), variant)

            if i != 7:
                top.add(gdstk.Reference(flstub, origin=(0, (2 * i + 1) * 222)))

            rect_left = gdstk.boolean(rect_left, gdstk.text("{:.04f}".format(freq_func(i * 2 + 1)), 64, (-680, 2 * i * 222 + 111)), "not")
            rect_right = gdstk.boolean(rect_right, gdstk.text("{:.04f}".format(freq_func(i * 2)), 64, (+444 + 28, 2 * i * 222 + 111)), "not")
            top.add(gdstk.Reference(left, origin=(0, 2 * i * 222)))
            top.add(
                gdstk.Reference(
                    right, origin=(0, 2 * i * 222), x_reflection=True, rotation=np.pi
                )
            )
            lib.add(left, right)

        for i in range(0, 8):
            for j in range(0, 6):
                rect_right = gdstk.boolean(
                    rect_right,
                    gdstk.regular_polygon(
                        (
                            222 * 2 + j * 222 + b.focus_point[0],
                            222 + i * 444 + (j % 2) * 222 + b.focus_point[1],
                        ),
                        8,
                        12,
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
                        8,
                        12,
                    ),
                    "not",
                )

        milo = [
            p.scale(8).translate(2700-1422.4, 0)
            for p in gdstk.read_gds("./milo.gds")["TOP"].polygons
        ]


        endcap = gdstk.Cell("endcap{:d}".format(variant))
        ec = gdstk.rectangle((-2700, 0), (2700, 950), *HF_GP)
        f = UEFeedlineConfig()
        m = 3
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
            *HF_GP,
        )
        outline = gdstk.boolean(ec, outline, "not")
        outline = gdstk.boolean(outline, gdstk.text("8 pH/sq HFHF v{:d}".format(variant), 250, (-2500, 250)), "not", layer=HF_GP.gds_layer[0], datatype=HF_GP.gds_layer[1])

        surround = gdstk.rectangle((-3000, -950 - 100 - 200), (3000, -950 - 100 - 200 + 6000))
        surround = gdstk.boolean(
            surround,
            gdstk.rectangle((-2800, -950 - 100), (2800, -950 - 100 - 200 + 5800)),
            "not",
            layer=HF_GP.gds_layer[0],
            datatype=HF_GP.gds_layer[1]
        )

        LS = [20, 40, 60, 80, 100]
        tlm = [
            gdstk.rectangle(
                (-2700 + 150 + 150 + 200 + 8, 2700 // 2 - 2),
                (-2700 + 150 + 150 + 200 + 8 + sum(LS) + len(LS) * 32 + 32, 2700 // 2 + 2),
            )
        ]
        for i in range(0, len(LS) + 1):
            s = sum(LS[:i]) + 16 + 4 + i * 32
            if i != len(LS):
                if variant != 3:
                    inset = variants[variant][1]
                else:
                    inset = LS[i] / 2 + 1.5
                top.add(
                    *gdstk.boolean(
                        gdstk.rectangle(
                            (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 6.5, 2700 // 2 - 1.5),
                            (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 6.5, 2700 // 2 + 1.5),
                        ),
                        gdstk.rectangle(
                            (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 1.5 + inset, 2700 // 2 - 2),
                            (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 1.5 - inset, 2700 // 2 + 2),
                        ),
                        "not",
                        layer=HF_CONTACT.gds_layer[0],
                        datatype=HF_CONTACT.gds_layer[1]
                    )
                )
                top.add(
                    gdstk.rectangle(
                        (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 8, 2700 // 2 - 2),
                        (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 8, 2700 // 2 + 2),
                        layer=HF.gds_layer[0],
                        datatype=HF.gds_layer[1]
                    )
                )
                tlm = gdstk.boolean(
                    tlm,
                    gdstk.rectangle(
                        (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32, 2700 // 2 - 2),
                        (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i], 2700 // 2 + 2),
                    ),
                    "not"
                )

            tlm.append(
                gdstk.rectangle(
                    (-2700 + 150 + 150, 2700 // 2 - 32 - i * (200 + 16)),
                    (-2700 + 150 + 150 + 200, 2700 // 2 - 32 - 200 - i * (200 + 16))
                )
            )
            tlm.append(
                gdstk.rectangle(
                    (-2700 + 150 + 150, 2700 // 2 + 32 + i * (200 + 16)),
                    (-2700 + 150 + 150 + 200, 2700 // 2 + 32 + 200 + i * (200 + 16))
                )
            )
    
            tlm.append(
                gdstk.rectangle(
                    (-2700 + 150 + 150 + 200, 2700 // 2 - 32 - i * (200 + 16)),
                    (-2700 + 150 + 150 + 200 + s, 2700 // 2 - 32 - 8 - i * (200 + 16))
                )
            )
            tlm.append(
                gdstk.rectangle(
                    (-2700 + 150 + 150 + 200 + s, 2700 // 2 - 2),
                    (-2700 + 150 + 150 + 200 + s + 8, 2700 // 2 - 32 - 8 - i * (200 + 16))
                )
            )
            tlm.append(
                gdstk.rectangle(
                    (-2700 + 150 + 150 + 200, 2700 // 2 + 32 + i * (200 + 16)),
                    (-2700 + 150 + 150 + 200 + s, 2700 // 2 + 32 + 8 + i * (200 + 16))
                )
            )
            tlm.append(
                gdstk.rectangle(
                    (-2700 + 150 + 150 + 200 + s, 2700 // 2 + 2),
                    (-2700 + 150 + 150 + 200 + s + 8, 2700 // 2 + 32 + 8 + i * (200 + 16))
                )
            )

        
        max_extent = 32 + 200 + len(LS) * (200 + 16)
        rect_left = gdstk.boolean(
            rect_left,
            gdstk.rectangle(
                (-2700 + 200, 2700 // 2 -max_extent - 32),
                (-2700 + 150 + 150 + 200 + 8 + sum(LS) + len(LS) * 32 + 32 + 32, 2700 // 2 + max_extent + 32)
            ),
            "not"
        )

        rect_right = gdstk.boolean(rect_right, milo, "or", layer=HF_GP.gds_layer[0], datatype=HF_GP.gds_layer[1])
        rect_left = gdstk.boolean(rect_left, rect_left, "or", layer=HF_GP.gds_layer[0], datatype=HF_GP.gds_layer[1])

        top.add(*gdstk.boolean(tlm, tlm, "or", layer=HF_GP.gds_layer[0], datatype=HF_GP.gds_layer[1]))

        top.add(gdstk.Reference(flstubmini, origin=(0, 3500 - 170)))
        top.add(*rect_right, *rect_left)

        gold = gdstk.rectangle((-2700, -950), (2700, -950 + 5400))
        gold = gdstk.boolean(
            gold,
            gdstk.rectangle((-2700 + 150, -950 + 150), (2700-150, -950 + 5400 - 150)),
            "not"
        )
        gold = gdstk.boolean(
            gold,
            gdstk.rectangle((2700-200, 0), (2700 + 20, 1500)),
            "not"
        )

        gold.extend(
            gdstk.boolean(
                [
                    gdstk.regular_polygon((2200, 780), 16, 35),
                    gdstk.Polygon(
                        [
                            [2147.00000, 313.00000],
                            [2069.00000, 320.00000],
                            [2052.00000, 418.00000],
                            [2055.00000, 441.00000],
                            [2079.00000, 427.00000],
                            [2115.00000, 418.00000],
                            [2163.00000, 421.00000],
                            [2215.00000, 438.00000],
                            [2214.00000, 332.00000],
                        ]
                    )
                ],
                milo,
                "not"
            )
        )

        top.add(*gdstk.boolean(gold, gold, "or", layer=100))

        endcap.add(*outline)
        top.add(*surround)
        top.add(gdstk.Reference(endcap, (0, -950)))
        top.add(gdstk.Reference(endcap, (0, 4500-50), rotation=np.pi))

        lib.add(top)
        lib.add(flstub, flstubmini)
        lib.add(endcap)
        return top

    vs = [make_variant(v) for v in range(4)]

    tile = gdstk.Cell("tile")
    tile.add(gdstk.Reference(vs[0], (0 - 3000 - 100, 950 - 5400 / 2 + 3000 + 100)))
    tile.add(gdstk.Reference(vs[1], (0 + 3000 + 100, 950 - 5400 / 2 + 3000 + 100)))
    tile.add(gdstk.Reference(vs[2], (0 - 3000 - 100, 950 - 5400 / 2 - 3000 - 100)))
    tile.add(gdstk.Reference(vs[3], (0 + 3000 + 100, 950 - 5400 / 2 - 3000 - 100)))

    top = gdstk.Cell("top")

    for i in range(-1, 2):
        for j in range(-1, 2):
            top.add(gdstk.Reference(tile, ((6000 * 2 + 200 * 2)*i, (6000 * 2 + 200 * 2)*j)))

    for cord in [(-21000, -21000), (-21000, 21000), (21000, -21000), (21000, 21000), (0, 0)]:
        top.add(gdstk.cross(cord, 800, 50, *HF_GP))
        top.add(gdstk.cross(cord, 800, 50, *HF))
        top.add(gdstk.rectangle((cord[0] - 500, cord[1] - 500), (cord[0] + 500, cord[1] + 500), *HF_CONTACT))

    lib.add(top, tile)


    lib.write_gds("ue1tm4style8ph-hfhf.gds")
