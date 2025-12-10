#!/usr/bin/env python3
import gdstk
import numpy as np

from dataclasses import dataclass
from typing import Optional

from ..ue1.layers import ATA_NB, HF, HF_CONTACT, HF_CONTACT_LIFTOFF, ASI, ASI_EP, SOLDER_MASK
from ..layers import DrawingLayer

from .. import mecstyle
from .. import geometry


def unionize(polys, layer, datatype):
    members = [p for p in polys if p.layer == layer and p.datatype == datatype]
    return gdstk.boolean(members, [], "or", 0.0001, layer, datatype)


@dataclass(eq=True, frozen=True)
class ViaWire(mecstyle.ViaWire):
    bridge_width: float = 4
    bridge_layer: tuple[int, int] | DrawingLayer = HF
    bridge_land: bool = True
    landing_width: float = 4
    landing_length: float = 18
    landing_layer: tuple[int, int] | DrawingLayer = ATA_NB
    via_width: float = 3
    via_length: float = 15
    via_layer: tuple[int, int] | DrawingLayer = HF_CONTACT
    liftoff_layer: tuple[int, int] | DrawingLayer = HF_CONTACT_LIFTOFF
    liftoff_width: float = 5
    asi_layer: tuple[int, int] | DrawingLayer = ASI
    asi_ep_layer: tuple[int, int] | DrawingLayer = ASI_EP
    asi_width: float = 6

    def draw_polys(self, a: tuple[float, float], b: tuple[float, float]):
        polys = super().draw_polys(a, b)
        center = (0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1]))
        pad = self.landing_length - self.via_length
        pad *= 0.5
        if a[1] == b[1]:
            length = abs(b[0] - a[0])
            asi = [
                gdstk.rectangle(
                    (
                        center[0] - length / 2 + self.via_length + pad * 2 + 1,
                        center[1] - self.asi_width / 2,
                    ),
                    (
                        center[0] + length / 2 - self.via_length - pad * 2 - 1,
                        center[1] + self.asi_width / 2,
                    ),
                    *self.asi_layer,
                ),
                gdstk.rectangle(
                    (
                        center[0] - length / 2 + self.via_length + pad * 2,
                        center[1] - self.asi_width / 2 - 1,
                    ),
                    (
                        center[0] + length / 2 - self.via_length - pad * 2,
                        center[1] + self.asi_width / 2 + 1,
                    ),
                    *self.asi_ep_layer,
                ),
            ]
            liftoff = [
                gdstk.rectangle(
                    (
                        center[0] - length / 2 + pad,
                        center[1] - self.liftoff_width / 2,
                    ),
                    (
                        center[0] - length / 2 + pad + self.via_length,
                        center[1] + self.liftoff_width / 2,
                    ),
                    *self.liftoff_layer,
                ),
                gdstk.rectangle(
                    (
                        center[0] + length / 2 - pad,
                        center[1] - self.liftoff_width / 2,
                    ),
                    (
                        center[0] + length / 2 - pad - self.via_length,
                        center[1] + self.liftoff_width / 2,
                    ),
                    *self.liftoff_layer,
                ),
            ]
            polys += asi + liftoff
        else:
            length = abs(b[1] - a[1])
            asi = [
                gdstk.rectangle(
                    (
                        center[0] - self.asi_width / 2,
                        center[1] - length / 2 + self.via_length + pad * 2 + 1,
                    ),
                    (
                        center[0] + self.asi_width / 2,
                        center[1] + length / 2 - self.via_length - pad * 2 - 1,
                    ),
                    *self.asi_layer,
                ),
                gdstk.rectangle(
                    (
                        center[0] - self.asi_width / 2 - 1,
                        center[1] - length / 2 + self.via_length + pad * 2,
                    ),
                    (
                        center[0] + self.asi_width / 2 + 1,
                        center[1] + length / 2 - self.via_length - pad * 2,
                    ),
                    *self.asi_ep_layer,
                ),
            ]
            liftoff = [
                gdstk.rectangle(
                    (
                        center[0] - self.liftoff_width / 2,
                        center[1] - length / 2 + pad,
                    ),
                    (
                        center[0] + self.liftoff_width / 2,
                        center[1] - length / 2 + pad + self.via_length,
                    ),
                    *self.liftoff_layer,
                ),
                gdstk.rectangle(
                    (
                        center[0] - self.liftoff_width / 2,
                        center[1] + length / 2 - pad,
                    ),
                    (
                        center[0] + self.liftoff_width / 2,
                        center[1] + length / 2 - pad - self.via_length,
                    ),
                    *self.liftoff_layer,
                ),
            ]
            polys += asi + liftoff

        return polys


@dataclass(eq=True, frozen=True)
class UEFeedlineConfig(geometry.FeedlineConfig):
    a: float = 4.5
    b: float = 4.0
    c: float = 9.5
    feed_layer: tuple[int, int] | DrawingLayer = ATA_NB
    ground_layer: tuple[int, int] | DrawingLayer = ATA_NB


@dataclass(eq=True, frozen=True)
class InductorConfig(mecstyle.InductorDoubledConfig):
    legs: int = 4
    leg_gap: float = 2.0
    leg_length: float = 40.0
    leg_width: float = 4.0
    leg_landing: float = 8
    leg_layer: DrawingLayer = HF
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

    def draw(self, port_offset=0, variation_layer=None, cellcache=...):
        c = super().draw(port_offset, variation_layer, cellcache)
        assert self.via_gap >= 0.0
        if self.via_gap > 0.0:
            assert self.litho_vias is not None
            assert self.via_over is None
            via_over = self.litho_vias * (self.leg_width + self.leg_gap)
        else:
            assert self.litho_vias is None
            via_over = self.via_over or 0.0
        vias = [
            gdstk.rectangle(
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    - self.leg_landing / 2
                    - self.via_width / 2,
                    self.wiring_gap
                    + self.wiring_extra_height
                    + (self.wiring_width - self.leg_width) / 2
                    - via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    - self.leg_landing / 2
                    + self.via_width / 2
                    + self.via_inset,
                    self.dimensions[1] + via_over,
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
                    self.wiring_gap
                    + self.wiring_extra_height
                    + (self.wiring_width - self.leg_width) / 2
                    - via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    + self.leg_landing / 2
                    + self.via_width / 2
                    + self.leg_length,
                    self.dimensions[1] + via_over,
                ),
                *self.via_layer,
            ),
        ]

        if self.via_gap > 0.0:
            cuts = []
            for i in range(-1 - self.litho_vias, self.legs * 2 + self.litho_vias):
                cuts.append(
                    gdstk.rectangle(
                        (
                            0,
                            self.wiring_gap
                            + self.wiring_extra_height
                            + self.leg_width
                            + self.leg_gap / 2
                            - self.via_gap / 2
                            + i * (self.leg_width + self.leg_gap),
                        ),
                        (
                            self.leg_length
                            + self.wiring_extra * 2
                            + self.wiring_width * 4
                            + self.wiring_gap * 4,
                            self.wiring_gap
                            + self.wiring_extra_height
                            + self.leg_width
                            + self.leg_gap / 2
                            + self.via_gap / 2
                            + i * (self.leg_width + self.leg_gap),
                        ),
                    )
                )
            vias = gdstk.boolean(vias, cuts, "not", 1e-6, *self.via_layer)

        if self.via_inset * 2 < self.leg_length:
            # TODO: Fit into the rest of the framework
            ASI_PADDING = 1.0
            asi = [
                gdstk.rectangle(
                    (
                        self.wiring_width * 2
                        + self.wiring_gap * 2
                        + self.wiring_extra
                        + ASI_PADDING
                        + self.via_inset,
                        self.wiring_gap
                        + self.wiring_extra_height
                        + (self.wiring_width - self.leg_width) / 2
                        - via_over
                        + ASI_PADDING,
                    ),
                    (
                        self.wiring_width * 2
                        + self.wiring_gap * 2
                        + self.wiring_extra
                        + self.leg_length
                        - ASI_PADDING
                        - self.via_inset,
                        self.dimensions[1] + via_over - ASI_PADDING,
                    ),
                    *ASI,
                ),
                gdstk.rectangle(
                    (
                        self.wiring_width * 2 + self.wiring_gap * 2 + self.wiring_extra + self.via_inset,
                        self.wiring_gap
                        + self.wiring_extra_height
                        + (self.wiring_width - self.leg_width) / 2
                        - via_over,
                    ),
                    (
                        self.wiring_width * 2
                        + self.wiring_gap * 2
                        + self.wiring_extra
                        + self.leg_length
                        - self.via_inset,
                        self.dimensions[1] + via_over,
                    ),
                    *ASI_EP,
                ),
            ]
        else:
            asi = []

        liftoff = [
            gdstk.rectangle(
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    - self.leg_landing / 2
                    - self.via_width / 2,
                    self.wiring_gap
                    + self.wiring_extra_height
                    + (self.wiring_width - self.leg_width) / 2
                    - via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    - self.leg_landing / 2
                    + self.via_width / 2
                    + self.via_inset,
                    self.dimensions[1] + via_over,
                ),
                *HF_CONTACT_LIFTOFF,
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
                    self.wiring_gap
                    + self.wiring_extra_height
                    + (self.wiring_width - self.leg_width) / 2
                    - via_over,
                ),
                (
                    self.wiring_width * 2
                    + self.wiring_gap * 2
                    + self.wiring_extra
                    + self.leg_landing / 2
                    + self.via_width / 2
                    + self.leg_length,
                    self.dimensions[1] + via_over,
                ),
                *HF_CONTACT_LIFTOFF,
            ),
        ]
        mirrorline = (0, self.dimensions[1] / 2), (self.dimensions[0], self.dimensions[1] / 2)
        c.add(
            *[l.mirror(*mirrorline) for l in vias],
            *[l.mirror(*mirrorline) for l in liftoff],
            *[l.mirror(*mirrorline) for l in asi],
        )
        return c


@dataclass(eq=True, frozen=True)
class CapacitorConfig(mecstyle.CapacitorConfig):
    legs: int = 66
    leg_gap: float = 1
    leg_length: tuple[float, float] = (222 - 33 + 212, 247)
    leg_width: float = 1
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = ATA_NB
    wiring_width: float = 4.0
    wiring_layer: DrawingLayer = ATA_NB
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(mecstyle.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: UEFeedlineConfig = UEFeedlineConfig(feed_layer=ATA_NB, ground_layer=ATA_NB)
    coupler_width: float = 2.0
    coupler_gap: float = 4.0
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
    extended_coupler_pullback: bool = False
    double_coupler: bool = True


def make_tm_variant(
    lib,
    variant,
    resonators,
    boxconfig,
    boxconfighqc,
    feedlineconfig,
    viawire,
    dietext,
    variants,
    arrayname="",
    flmult=33,
):
    top = gdstk.Cell(f"tm4-tm-{arrayname}-v{variant:d}")
    b = boxconfig
    bhqc = boxconfighqc

    np.random.seed(42)
    ks = list(resonators.keys())
    index = np.arange(len(ks))
    np.random.shuffle(index)

    freq_func = lambda i: ks[index[i]]
    coup_func = lambda i: resonators[freq_func(i)]["coupler_tunable"]
    cap_func = lambda i: resonators[freq_func(i)]["capacitor_tunable"]
    hqc_func = lambda i: freq_func(i) < 7.0 and freq_func(i) >= 6.0

    flstub = feedlineconfig().draw(222, ports=([], []), cellcache={})
    flstubmini = feedlineconfig().draw(170, ports=([], []), cellcache={})

    flstub.add(gdstk.rectangle((feedlineconfig().width_half, 0), (b.width, 222), *boxconfig.box_layer))
    flstub.add(gdstk.rectangle((-feedlineconfig().width_half, 0), (-b.width, 222), *boxconfig.box_layer))

    flstubmini.add(gdstk.rectangle((feedlineconfig().width_half, 0), (b.width, 170), *boxconfig.box_layer))
    flstubmini.add(gdstk.rectangle((-feedlineconfig().width_half, 0), (-b.width, 170), *boxconfig.box_layer))
    flstub.name = "flstubv{:d}".format(variant)
    flstubmini.name = "flstubmini{:d}".format(variant)

    rect_right = gdstk.rectangle((b.width, 0), (2700, 3500))
    rect_right = gdstk.boolean(rect_right, gdstk.rectangle((2700 - 1422.4, 0), (2700, 1524)), "not")
    rect_left = gdstk.rectangle((-b.width, 0), (-2700, 3500))

    for i in range(8):
        if not hqc_func(i * 2):
            left = b.draw(capacitor_tunable=cap_func(i * 2), coupler_tunable=coup_func(i * 2), cellcache={})
        else:
            left = bhqc.draw(
                capacitor_tunable=cap_func(i * 2), coupler_tunable=0, cellcache={}
            )
        if not hqc_func(i * 2 + 1):
            right = b.draw(
                capacitor_tunable=cap_func(i * 2 + 1), coupler_tunable=coup_func(i * 2 + 1), cellcache={}
            )
        else:
            right = bhqc.draw(
                capacitor_tunable=cap_func(i * 2 + 1), coupler_tunable=0, cellcache={}
            )
        left.name = "left-wide-cap{}-coup{}-f{:.04f}-v{:d}".format(
            cap_func(i * 2), coup_func(i * 2), freq_func(i * 2), variant
        )
        right.name = "right-wide-cap{}-coup{}-f{:.04f}-v{:d}".format(
            cap_func(i * 2 + 1), coup_func(i * 2 + 1), freq_func(i * 2 + 1), variant
        )

        if i != 7:
            top.add(gdstk.Reference(flstub, origin=(0, (2 * i + 1) * 222)))
        rect_left = gdstk.boolean(
            rect_left,
            gdstk.text("{:.04f}".format(freq_func(i * 2 + 1)), 64, (-680, 2 * i * 222 + 111)),
            "not",
        )
        rect_right = gdstk.boolean(
            rect_right,
            gdstk.text("{:.04f}".format(freq_func(i * 2)), 64, (+444 + 28, 2 * i * 222 + 111)),
            "not",
        )
        top.add(gdstk.Reference(left, origin=(0, 2 * i * 222)))
        top.add(gdstk.Reference(right, origin=(0, 2 * i * 222), x_reflection=True, rotation=np.pi))
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

    milo = [p.scale(8).translate(2700 - 1422.4, 0) for p in gdstk.read_gds("./milo.gds")["TOP"].polygons]

    endcap = gdstk.Cell("endcap{:d}".format(variant))
    ec = gdstk.rectangle((-2700, 0), (2700, 950), *boxconfig.box_layer)
    f = feedlineconfig()
    m = flmult
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
        *boxconfig.box_layer,
    )
    outline = gdstk.boolean(ec, outline, "not")
    outline = gdstk.boolean(
        outline,
        gdstk.text(dietext + " v{:d}".format(variant), 250, (-2500, 600)),
        "not",
        layer=boxconfig.box_layer.gds_layer[0],
        datatype=boxconfig.box_layer.gds_layer[1],
    )
    endcap.add(*outline)
    for i in range(-3, 3 + 1):
        endcap.add(
            gdstk.ellipse(
                (800 * i, 500),
                125.0,
                tolerance=1,
                layer=SOLDER_MASK.gds_layer[0],
                datatype=SOLDER_MASK.gds_layer[1],
            )
        )

    surround = gdstk.rectangle((-3000, -950 - 100 - 200), (3000, -950 - 100 - 200 + 6000))
    surround = gdstk.boolean(
        surround,
        gdstk.rectangle((-2800, -950 - 100), (2800, -950 - 100 - 200 + 5800)),
        "not",
        layer=boxconfig.box_layer.gds_layer[0],
        datatype=boxconfig.box_layer.gds_layer[1],
    )

    LS = [20, 40, 60, 80, 100]
    WS = [3, 4, 6, 8, 10, 16, 20, 32]
    max_extent = 32 + 200 + len(LS) * (200 + 16)
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
            for j in range(-2, 3):
                top.add(
                    *gdstk.boolean(
                        gdstk.rectangle(
                            (
                                -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 6.5,
                                2700 // 2 - 1.5 + j * 6,
                            ),
                            (
                                -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 6.5,
                                2700 // 2 + 1.5 + j * 6,
                            ),
                        ),
                        gdstk.rectangle(
                            (
                                -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 1.5 + inset,
                                2700 // 2 - 2 + j * 6,
                            ),
                            (
                                -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 1.5 - inset,
                                2700 // 2 + 2 + j * 6,
                            ),
                        ),
                        "not",
                        layer=viawire().via_layer.gds_layer[0],
                        datatype=viawire().via_layer.gds_layer[1],
                    )
                )
            top.add(
                gdstk.rectangle(
                    (
                        -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 1.5 + inset + 1.5 + 1,
                        2700 // 2 - 14 + 1,
                    ),
                    (
                        -2700
                        + 150
                        + 150
                        + 200
                        + 8
                        + sum(LS[:i])
                        + i * 32
                        + 32
                        + LS[i]
                        + 1.5
                        - inset
                        - 1.5
                        - 1,
                        2700 // 2 + 14 - 1,
                    ),
                    *viawire().asi_layer,
                )
            )
            top.add(
                gdstk.rectangle(
                    (
                        -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 1.5 + inset + 1.5,
                        2700 // 2 - 14,
                    ),
                    (
                        -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 1.5 - inset - 1.5,
                        2700 // 2 + 14,
                    ),
                    *viawire().asi_ep_layer,
                )
            )
            top.add(
                *gdstk.boolean(
                    gdstk.rectangle(
                        (
                            -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 6.5,
                            2700 // 2 - 14,
                        ),
                        (
                            -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 6.5,
                            2700 // 2 + 14,
                        ),
                    ),
                    gdstk.rectangle(
                        (
                            -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 1.5 + inset,
                            2700 // 2 - 15,
                        ),
                        (
                            -2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 1.5 - inset,
                            2700 // 2 + 15,
                        ),
                    ),
                    "not",
                    layer=viawire().liftoff_layer.gds_layer[0],
                    datatype=viawire().liftoff_layer.gds_layer[1],
                )
            )
            top.add(
                gdstk.rectangle(
                    (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 - 8, 2700 // 2 - 2),
                    (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i] + 8, 2700 // 2 + 2),
                    layer=viawire().bridge_layer.gds_layer[0],
                    datatype=viawire().bridge_layer.gds_layer[1],
                )
            )
            tlm = gdstk.boolean(
                tlm,
                gdstk.rectangle(
                    (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32, 2700 // 2 - 2),
                    (-2700 + 150 + 150 + 200 + 8 + sum(LS[:i]) + i * 32 + 32 + LS[i], 2700 // 2 + 2),
                ),
                "not",
            )

        tlm.append(
            gdstk.rectangle(
                (-2700 + 150 + 150, 2700 // 2 - 32 - i * (200 + 16)),
                (-2700 + 150 + 150 + 200, 2700 // 2 - 32 - 200 - i * (200 + 16)),
            )
        )
        tlm.append(
            gdstk.rectangle(
                (-2700 + 150 + 150, 2700 // 2 + 32 + i * (200 + 16)),
                (-2700 + 150 + 150 + 200, 2700 // 2 + 32 + 200 + i * (200 + 16)),
            )
        )

        tlm.append(
            gdstk.rectangle(
                (-2700 + 150 + 150 + 200, 2700 // 2 - 32 - i * (200 + 16)),
                (-2700 + 150 + 150 + 200 + s, 2700 // 2 - 32 - 8 - i * (200 + 16)),
            )
        )
        tlm.append(
            gdstk.rectangle(
                (-2700 + 150 + 150 + 200 + s, 2700 // 2 - 2),
                (-2700 + 150 + 150 + 200 + s + 8, 2700 // 2 - 32 - 8 - i * (200 + 16)),
            )
        )
        tlm.append(
            gdstk.rectangle(
                (-2700 + 150 + 150 + 200, 2700 // 2 + 32 + i * (200 + 16)),
                (-2700 + 150 + 150 + 200 + s, 2700 // 2 + 32 + 8 + i * (200 + 16)),
            )
        )
        tlm.append(
            gdstk.rectangle(
                (-2700 + 150 + 150 + 200 + s, 2700 // 2 + 2),
                (-2700 + 150 + 150 + 200 + s + 8, 2700 // 2 + 32 + 8 + i * (200 + 16)),
            )
        )

    rect_left = gdstk.boolean(
        rect_left,
        gdstk.rectangle(
            (-2700 + 200, 2700 // 2 - max_extent - 32),
            (-2700 + 150 + 150 + 200 + 8 + sum(LS) + len(LS) * 32 + 32 + 32, 2700 // 2 + max_extent + 32),
        ),
        "not",
    )
    rect_left = gdstk.boolean(
        rect_left,
        gdstk.rectangle(
            (-2700 + 200, 2700 // 2 + max_extent + 64),
            (
                -2700 + 150 + 150 + 200 + 8 + sum(LS) + len(LS) * 32 + 32 + 32,
                2700 // 2 + max_extent + 1000 + 64,
            ),
        ),
        "not",
    )

    LS = [20, 40, 60, 80, 100, 120]

    ps = []
    for i in range(0, len(LS)):
        h = 0
        for j in range(0, len(WS)):
            if j != 0:
                h += (WS[j] - WS[j - 1]) / 2
                h += 10
            for _ in range(4):
                ps.extend(
                    viawire(
                        via_length=5,
                        landing_length=8,
                        via_width=WS[j] - 1,
                        bridge_width=WS[j],
                        landing_width=WS[j],
                        asi_width=WS[j] + 8,
                        liftoff_width=WS[j] + 8,
                    ).draw_polys(
                        (
                            -2700 + 200 + 150 + 150 + 16 + sum(LS[:i]) + i * 16,
                            2700 // 2 + max_extent + 64 + 32 + h,
                        ),
                        (
                            -2700 + 200 + 150 + 150 + 16 + sum(LS[:i]) + i * 16 + LS[i],
                            2700 // 2 + max_extent + 64 + 32 + h,
                        ),
                    )
                )
                h += 8 + WS[j]

    top.add(*unionize(ps, *viawire().bridge_layer))
    top.add(*unionize(ps, *viawire().via_layer))
    top.add(*unionize(ps, *viawire().liftoff_layer))
    top.add(*unionize(ps, *viawire().landing_layer))
    top.add(*unionize(ps, *viawire().asi_layer))
    top.add(*unionize(ps, *viawire().asi_ep_layer))

    for i in range(4):
        top.add(
            gdstk.rectangle(
                (-2700 + 200 + 50, 2700 // 2 + max_extent + 64 + 33 + i * (16 + 165)),
                (-2700 + 200 + 50 + 200, 2700 // 2 + max_extent + 64 + 33 + 165 + i * (16 + 165)),
                *b.box_layer,
            )
        )

    rect_right = gdstk.boolean(
        rect_right,
        milo,
        "or",
        layer=boxconfig.box_layer.gds_layer[0],
        datatype=boxconfig.box_layer.gds_layer[1],
    )
    rect_left = gdstk.boolean(
        rect_left,
        rect_left,
        "or",
        layer=boxconfig.box_layer.gds_layer[0],
        datatype=boxconfig.box_layer.gds_layer[1],
    )

    top.add(
        *gdstk.boolean(
            tlm, tlm, "or", layer=boxconfig.box_layer.gds_layer[0], datatype=boxconfig.box_layer.gds_layer[1]
        )
    )

    top.add(gdstk.Reference(flstubmini, origin=(0, 3500 - 170)))
    top.add(*rect_right, *rect_left)

    gold = gdstk.rectangle((-2700, -950), (2700, -950 + 5400))
    gold = gdstk.boolean(
        gold, gdstk.rectangle((-2700 + 150, -950 + 150), (2700 - 150, -950 + 5400 - 150)), "not"
    )
    gold = gdstk.boolean(gold, gdstk.rectangle((2700 - 200, 0), (2700 + 20, 1500)), "not")

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
                ),
            ],
            milo,
            "not",
        )
    )
    via = viawire(via_length=5, landing_length=8, asi_width=22.2)
    xovers = gdstk.Cell(f"half_coax_crossovers{variant}")
    XOVER_LENGTH = 2 * (feedlineconfig().a + feedlineconfig().b + via.landing_length + 1)
    ps = []
    for i in range(160):
        yposh = i * 11.1 * 2
        ps.extend(via.draw_polys((-XOVER_LENGTH / 2, yposh), (+XOVER_LENGTH / 2, yposh)))
    j = 0
    while j * 6 + 2 < feedlineconfig().a + feedlineconfig().b:
        ps.append(gdstk.rectangle((j * 6 - 2, 0), (j * 6 + 2, yposh), *via.bridge_layer))
        ps.append(gdstk.rectangle((-j * 6 - 2, 0), (-j * 6 + 2, yposh), *via.bridge_layer))
        j += 1
    c = XOVER_LENGTH / 2 - via.landing_length / 2
    for i in range(0, 16):
        ps.append(gdstk.rectangle((-c - 2.5, 0 + 222 * i), (-c + 2.5, 200 + 222 * i), *via.liftoff_layer))
        ps.append(gdstk.rectangle((+c + 2.5, 0 + 222 * i), (+c - 2.5, 200 + 222 * i), *via.liftoff_layer))
    xovers.add(*unionize(ps, *viawire().bridge_layer))
    xovers.add(*unionize(ps, *viawire().via_layer))
    xovers.add(*unionize(ps, *viawire().liftoff_layer))
    xovers.add(*unionize(ps, *viawire().landing_layer))
    xovers.add(*unionize(ps, *viawire().asi_layer))
    xovers.add(*unionize(ps, *viawire().asi_ep_layer))
    top.add(gdstk.Reference(xovers, (0, 0)))
    lib.add(xovers)

    via = viawire()
    XOVER_LENGTH = 2 * (feedlineconfig().a + feedlineconfig().b + via.landing_length + 1)
    XOVER_LENGTH_COUPLER = 56
    xovers = gdstk.Cell(f"crossovers{variant}")
    for y in range(0, 16, 2):
        yposh = y * 222
        yposv = yposh + b.height - b.box_width - b.coupler_gap - b.coupler_width / 2
        xovers.add(
            *via.draw_polys(
                (-f.a - f.b - f.c / 2, -XOVER_LENGTH_COUPLER / 2 + yposv),
                (-f.a - f.b - f.c / 2, +XOVER_LENGTH_COUPLER / 2 + yposv),
            )
        )
        xovers.add(
            *via.draw_polys(
                (+f.a + f.b + f.c / 2, -XOVER_LENGTH_COUPLER / 2 + yposv),
                (+f.a + f.b + f.c / 2, +XOVER_LENGTH_COUPLER / 2 + yposv),
            )
        )
        xovers.add(*via.draw_polys((-XOVER_LENGTH / 2, yposh), (+XOVER_LENGTH / 2, yposh)))
        xovers.add(*via.draw_polys((-XOVER_LENGTH / 2, yposh), (+XOVER_LENGTH / 2, yposh)))
    top.add(gdstk.Reference(xovers, (0, 0)))
    lib.add(xovers)

    top.add(*gdstk.boolean(gold, gold, "or", layer=100))

    top.add(*surround)
    top.add(gdstk.Reference(endcap, (0, -950)))
    top.add(gdstk.Reference(endcap, (0, 4500 - 50), rotation=np.pi))

    lib.add(top)
    lib.add(flstub, flstubmini)
    lib.add(endcap)
    return top


if __name__ == "__main__":
    import numpy as np

    variants = [
        (3, 0),
        (3, 5),
        (3, 10),
        (3, 21.5),
    ]
    resonators = {
        4.0: {
            "coupler_tunable": 0.7142857142857142,
            "capacitor_tunable": 0.952755905511811,
        },
        4.05: {
            "coupler_tunable": 0.6825396825396826,
            "capacitor_tunable": 0.9212598425196851,
        },
        4.1: {
            "coupler_tunable": 0.6507936507936507,
            "capacitor_tunable": 0.889763779527559,
        },
        4.15: {
            "coupler_tunable": 0.6349206349206349,
            "capacitor_tunable": 0.8582677165354331,
        },
        4.2: {
            "coupler_tunable": 0.6031746031746031,
            "capacitor_tunable": 0.8346456692913385,
        },
        4.25: {
            "coupler_tunable": 0.5714285714285714,
            "capacitor_tunable": 0.8110236220472441,
        },
        4.3: {
            "coupler_tunable": 0.5396825396825397,
            "capacitor_tunable": 0.7874015748031495,
        },
        6.1: {
            "coupler_tunable": 0.0,
            "capacitor_tunable": 0.25984251968503935,
        },
        6.2: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.1732283464566929,
        },
        6.3: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.15748031496062992,
        },
        6.4: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.14173228346456693,
        },
        7.5: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.625: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.75: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.015748031496062992,
        },
        7.875: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.007874015748031496,
        },
        8.0: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.0,
        },
    }

    lib = gdstk.Library("ue2-ucsb-tm")

    for i in range(4):
        b = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            UEFeedlineConfig(),
        )

        bhqc = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            UEFeedlineConfig(),
            double_coupler=False,
            extended_coupler_pullback=True,
        )
        make_tm_variant(
            lib, i, resonators, b, bhqc, UEFeedlineConfig, ViaWire, "UE2 UCSB 8pH", variants, "ucsb-8ph"
        )

    # tile = gdstk.Cell("tile")
    # tile.add(gdstk.Reference(vs[0], (0 - 3000 - 100, 950 - 5400 / 2 + 3000 + 100)))
    # tile.add(gdstk.Reference(vs[1], (0 + 3000 + 100, 950 - 5400 / 2 + 3000 + 100)))
    # tile.add(gdstk.Reference(vs[2], (0 - 3000 - 100, 950 - 5400 / 2 - 3000 - 100)))
    # tile.add(gdstk.Reference(vs[3], (0 + 3000 + 100, 950 - 5400 / 2 - 3000 - 100)))

    # top = gdstk.Cell("top")

    # for i in range(-1, 2):
    #     for j in range(-1, 2):
    #         top.add(gdstk.Reference(tile, ((6000 * 2 + 200 * 2) * i, (6000 * 2 + 200 * 2) * j)))

    # for cord in [(-21000, -21000), (-21000, 21000), (21000, -21000), (21000, 21000), (0, 0)]:
    #     top.add(gdstk.cross(cord, 800, 50, *ATA_NB))
    #     top.add(gdstk.cross(cord, 800, 50, *HF))
    #     top.add(gdstk.rectangle((cord[0] - 500, cord[1] - 500), (cord[0] + 500, cord[1] + 500), *HF_CONTACT))

    # lib.add(top, tile)

    lib.write_gds("ue2-ucsb-tm4.gds")
