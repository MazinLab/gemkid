import gdstk
import numpy as np
from dataclasses import dataclass
from typing import Optional

from .layers import DrawingLayer

from .geometry import FeedlineConfig, GeomConfigMarker


@dataclass(eq=True, frozen=True)
class InductorConfig(GeomConfigMarker):
    legs: int
    leg_gap: float
    leg_length: float
    leg_width: float
    leg_landing: float
    leg_layer: tuple[int, int] | DrawingLayer
    wiring_width: float
    wiring_gap: float
    wiring_layer: tuple[int, int] | DrawingLayer

    def regions(self):
        topcap = self.wiring_width + self.wiring_gap * 2
        bottomcap = (self.wiring_width + self.wiring_gap) if self.legs % 2 == 0 else 0.0
        legvert = self.leg_width * self.legs + self.leg_gap * (self.legs - 1)
        leftcap = self.wiring_width
        rightcap = self.wiring_width * 2 + self.wiring_gap
        leghori = self.leg_length
        return [leftcap, leghori, rightcap], [bottomcap, legvert, topcap]

    @property
    def dimensions(self):
        regions = self.regions()
        return sum(regions[0]), sum(regions[1])

    @property
    def focus_point(self):
        regions = self.regions()
        return regions[0][0] + regions[0][1] / 2, regions[1][0] + regions[1][1] / 2

    @property
    def varsq(self):
        regions = self.regions()
        sq_start = (
            self.leg_length // (self.leg_width * 2) + regions[0][0],
            sum(regions[1][:2]) - self.leg_width,
        )
        sq_end = sq_start[0] + self.leg_width, sq_start[1] + self.leg_width
        return sq_start, sq_end

    def draw(self, port_offset=0.0, variation_layer=None, cellcache={}):
        regions = self.regions()
        h = hex(abs(hash((hash(self), hash(port_offset), hash(variation_layer)))))
        cellname = "Inductor-{:s}".format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c

        legs = [
            gdstk.rectangle(
                (regions[0][0] - self.leg_landing, regions[1][0] + i * (self.leg_width + self.leg_gap)),
                (
                    regions[0][0] + self.leg_length + self.leg_landing,
                    regions[1][0] + i * (self.leg_width + self.leg_gap) + self.leg_width,
                ),
                *self.leg_layer,
            )
            for i in range(self.legs)
        ]
        if variation_layer:
            legs = gdstk.boolean(
                legs, gdstk.rectangle(*self.varsq, *variation_layer), "not", 0.0001, *self.leg_layer
            )
            legs.append(gdstk.rectangle(*self.varsq, *variation_layer))
        c.add(*legs)

        leftwiring = [
            gdstk.rectangle(
                (
                    0,
                    regions[1][0]
                    + 2 * i * (self.leg_width + self.leg_gap)
                    + ((self.leg_width + self.leg_gap) if self.legs % 2 == 0 else 0),
                ),
                (
                    self.wiring_width,
                    regions[1][0]
                    + 2 * i * (self.leg_width + self.leg_gap)
                    + ((self.leg_width + self.leg_gap) if self.legs % 2 == 0 else 0)
                    + self.leg_width * 2
                    + self.leg_gap,
                ),
                *self.wiring_layer,
            )
            for i in range((self.legs - 1) // 2)
        ]
        rightwiring = [
            gdstk.rectangle(
                (
                    sum(regions[0][:2]),
                    regions[1][0]
                    + 2 * i * (self.leg_width + self.leg_gap)
                    + ((self.leg_width + self.leg_gap) if self.legs % 2 == 1 else 0),
                ),
                (
                    sum(regions[0][:2]) + self.wiring_width,
                    regions[1][0]
                    + 2 * i * (self.leg_width + self.leg_gap)
                    + ((self.leg_width + self.leg_gap) if self.legs % 2 == 1 else 0)
                    + self.leg_width * 2
                    + self.leg_gap,
                ),
                *self.wiring_layer,
            )
            for i in range(self.legs // 2)
        ]
        c.add(*leftwiring, *rightwiring)
        c.add(
            gdstk.rectangle(
                (0, sum(regions[1][:2]) - self.leg_width),
                (self.wiring_width, sum(regions[1]) - self.wiring_gap),
                *self.wiring_layer,
            ),
            gdstk.rectangle(
                (self.wiring_width, sum(regions[1]) - self.wiring_gap - self.wiring_width),
                (self.wiring_width + port_offset, sum(regions[1]) - self.wiring_gap),
                *self.wiring_layer,
            ),
            gdstk.rectangle(
                (port_offset, sum(regions[1]) - self.wiring_gap),
                (port_offset + self.wiring_width, sum(regions[1])),
                *self.wiring_layer,
            ),
            gdstk.rectangle(
                (regions[0][0] + self.wiring_gap + port_offset, sum(regions[1][:2]) + self.wiring_gap),
                (regions[0][0] + self.wiring_gap + self.wiring_width + port_offset, sum(regions[1])),
                *self.wiring_layer,
            ),
            gdstk.rectangle(
                (
                    regions[0][0] + self.wiring_gap + self.wiring_width + port_offset,
                    sum(regions[1]) - self.wiring_width - self.wiring_gap,
                ),
                (sum(regions[0]), sum(regions[1]) - self.wiring_gap),
                *self.wiring_layer,
            ),
            gdstk.rectangle(
                (sum(regions[0][:2]) + self.wiring_width + self.wiring_gap, 0),
                (sum(regions[0]), sum(regions[1]) - self.wiring_width - self.wiring_gap),
                *self.wiring_layer,
            ),
        )
        if self.legs % 2 == 0:
            c.add(
                gdstk.rectangle(
                    (0, 0), (sum(regions[0]) - self.wiring_width, self.wiring_width), *self.wiring_layer
                ),
                gdstk.rectangle(
                    (0, self.wiring_width),
                    (self.wiring_width, self.leg_width + self.wiring_gap + self.wiring_width),
                    *self.wiring_layer,
                ),
            )
        else:
            c.add(
                gdstk.rectangle(
                    (sum(regions[0][:2]), 0),
                    (sum(regions[0]) - self.wiring_width, self.leg_width),
                    *self.wiring_layer,
                )
            )
        return c

    @property
    def port(self):
        regions = self.regions()
        return regions[0][0], self.wiring_width


@dataclass(eq=True, frozen=True)
class CapacitorConfig(GeomConfigMarker):
    legs: int
    leg_gap: float
    leg_length: tuple[float, float]
    leg_width: float
    leg_landing: float
    leg_layer: tuple[int, int] | DrawingLayer
    wiring_width: float
    wiring_layer: tuple[int, int] | DrawingLayer
    extra_height: Optional[float]

    @property
    def dimensions(self):
        return (
            self.wiring_width * 2 + max(self.leg_length) + self.leg_gap,
            (
                (self.leg_width + self.leg_gap) * (self.legs + 1)
                + self.wiring_width
                + (self.extra_height if self.extra_height else 0.0)
            ),
        )

    def caprange(self):
        return self.legs * min(self.leg_length), self.legs * max(self.leg_length)

    def draw(self, tunable: float, port: tuple[float, float], cellcache={}):
        assert (
            tunable >= 0 and tunable <= 1
        ), "The capacitor tunable should be a fraction of the total possible in the [0, 1]"

        dim = self.dimensions

        h = hex(abs(hash((hash(self), hash(port), hash(tunable)))))
        cellname = "Capacitor-{:s}".format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c

        c.add(
            *gdstk.boolean(
                [
                    gdstk.rectangle((0, 0), (self.wiring_width, dim[1])),
                    gdstk.rectangle(
                        (dim[0] - self.wiring_width, 0), (dim[0], dim[1] - self.leg_width - self.leg_gap)
                    ),
                    gdstk.rectangle(
                        (self.wiring_width, 0),
                        (
                            dim[0] - self.wiring_width,
                            self.wiring_width + (self.extra_height if self.extra_height else 0.0),
                        ),
                    ),
                ],
                gdstk.rectangle(
                    (port[0], 0),
                    (
                        port[0] + port[1],
                        self.wiring_width + (self.extra_height if self.extra_height else 0.0),
                    ),
                ),
                "not",
                0.0001,
                *self.wiring_layer,
            )
        )

        cr = self.caprange()
        cap = (cr[1] - cr[0]) * tunable + cr[0]
        c.add(
            gdstk.rectangle(
                (self.wiring_width - self.leg_landing, dim[1] - self.leg_width),
                (dim[0], dim[1]),
                *self.leg_layer,
            )
        )
        leg_lengths = np.zeros(self.legs) + min(self.leg_length)
        current_cap = np.sum(leg_lengths)
        lg = max(self.leg_length) - min(self.leg_length)
        if self.legs % 2 == 1:
            leg_lengths[-1] += min(lg, cap - current_cap)
            current_cap = np.sum(leg_lengths)
        for i in range(0, self.legs, 2):
            if current_cap >= cap:
                break
            leg_lengths[i : i + 2] += min(lg * 2, cap - current_cap) / 2
            current_cap = np.sum(leg_lengths)
        leg_lengths = np.roll(leg_lengths, 3 * self.legs // 4)
        o = self.legs % 2
        legs = [
            (
                gdstk.rectangle(
                    (
                        self.wiring_width - self.leg_landing,
                        (
                            self.wiring_width
                            + self.leg_gap
                            + i * (self.leg_gap + self.leg_width)
                            + (self.extra_height if self.extra_height else 0.0)
                        ),
                    ),
                    (
                        self.wiring_width + le,
                        (
                            self.wiring_width
                            + (i + 1) * (self.leg_gap + self.leg_width)
                            + (self.extra_height if self.extra_height else 0.0)
                        ),
                    ),
                    *self.leg_layer,
                )
                if (i + o) % 2 == 0
                else gdstk.rectangle(
                    (
                        self.wiring_width + max(self.leg_length) + self.leg_gap - le,
                        (
                            self.wiring_width
                            + self.leg_gap
                            + i * (self.leg_gap + self.leg_width)
                            + (self.extra_height if self.extra_height else 0.0)
                        ),
                    ),
                    (
                        self.wiring_width + max(self.leg_length) + self.leg_gap + self.leg_landing,
                        (
                            self.wiring_width
                            + (i + 1) * (self.leg_gap + self.leg_width)
                            + (self.extra_height if self.extra_height else 0.0)
                        ),
                    ),
                    *self.leg_layer,
                )
            )
            for i, le in enumerate(leg_lengths)
        ]
        c.add(*legs)
        return c


@dataclass(eq=True, frozen=True)
class ViaWire:
    bridge_width: float
    bridge_layer: tuple[int, int] | DrawingLayer
    bridge_land: bool
    landing_width: float
    landing_length: float
    landing_layer: tuple[int, int] | DrawingLayer
    via_width: float
    via_length: float
    via_layer: tuple[int, int] | DrawingLayer

    def draw_polys(self, a: tuple[float, float], b: tuple[float, float]):
        if a[0] != b[0] and a[1] != b[1]:
            raise ValueError("Via must be horizontal or vertical")
        if a[1] == b[1]:
            landings = [
                (
                    (a[0], a[1] - self.landing_width / 2),
                    (a[0] + self.landing_length, a[1] + self.landing_width / 2),
                ),
                (
                    (b[0] - self.landing_length, b[1] - self.landing_width / 2),
                    (b[0], b[1] + self.landing_width / 2),
                ),
            ]
            bridge = ((a[0], a[1] - self.bridge_width / 2), (b[0], b[1] + self.bridge_width / 2))
        else:
            landings = [
                (
                    (a[0] - self.landing_width / 2, a[1]),
                    (a[0] + self.landing_width / 2, a[1] + self.landing_length),
                ),
                (
                    (b[0] - self.landing_width / 2, b[1]),
                    (b[0] + self.landing_width / 2, b[1] - self.landing_length),
                ),
            ]
            bridge = ((a[0], a[1] - self.bridge_width / 2), (b[0], b[1] + self.bridge_width / 2))

        centers = [
            ((landings[0][1][0] + landings[0][0][0]) / 2, ((landings[0][1][1] + landings[0][0][1])) / 2),
            ((landings[1][1][0] + landings[1][0][0]) / 2, ((landings[1][1][1] + landings[1][0][1])) / 2),
        ]
        vx, vy = (self.via_length, self.via_width) if a[1] == b[1] else (self.via_width, self.via_length)
        vias = [
            (
                (centers[0][0] - vx / 2, centers[0][1] - vy / 2),
                (centers[0][0] + vx / 2, centers[0][1] + vy / 2),
            ),
            (
                (centers[1][0] - vx / 2, centers[1][1] - vy / 2),
                (centers[1][0] + vx / 2, centers[1][1] + vy / 2),
            ),
        ]

        polys = [
            gdstk.rectangle(*landings[0], *self.landing_layer),
            gdstk.rectangle(*landings[1], *self.landing_layer),
            gdstk.rectangle(*vias[0], *self.via_layer),
            gdstk.rectangle(*vias[1], *self.via_layer),
            gdstk.rectangle(*bridge, *self.bridge_layer),
        ]

        if self.bridge_land:
            polys.extend(
                [
                    gdstk.rectangle(*landings[0], *self.bridge_layer),
                    gdstk.rectangle(*landings[1], *self.bridge_layer),
                ]
            )
        return polys


@dataclass(eq=True, frozen=True)
class BoxConfig(GeomConfigMarker):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig
    coupler_width: float
    coupler_gap: float
    coupler_fill: bool
    coupler_layer: tuple[int, int] | DrawingLayer
    coupler_via: Optional[ViaWire]
    box_width: float
    box_gap: float
    box_layer: tuple[int, int] | DrawingLayer
    width: float
    height: float

    @property
    def coupler_range(self):
        if self.capacitor:
            return sum(self.capacitor.dimensions)
        return None

    @property
    def dimensions(self):
        return self.width, self.height

    def regions(self):
        if self.coupler_via:
            cgl = self.coupler_gap * 2 + max(self.coupler_via.landing_length, self.coupler_width)
            cgw = self.coupler_gap * 2 + max(self.coupler_via.landing_width, self.coupler_width)
        else:
            cgl = cgw = self.coupler_gap * 2 + self.coupler_width
        x = [self.feedline.width_half, cgl]
        x.append(self.width - sum(x) - self.box_width - self.box_gap)
        x.append(self.box_width + self.box_gap)
        y = [
            self.box_width + self.box_gap,
            self.height - 2 * self.box_width - self.box_gap - cgw,
            cgw,
            self.box_width,
        ]
        return x, y

    def draw(
        self,
        coupler_tunable: float = 1.0,
        capacitor_tunable: float = 1.0,
        variation_layer=None,
        flatten=True,
        cellcache={},
    ):
        assert ((self.inductor is not None) and (self.capacitor is not None)) or (
            self.inductor is None and self.capacitor is None
        )
        r = self.regions()
        h = hex(abs(hash((self, coupler_tunable, capacitor_tunable, variation_layer))))
        subcells = []

        cellname = ("BoxFlat-{:s}" if flatten else "UE1Box-{:s}").format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c

        f = self.feedline.draw_half(
            self.height,
            ports=[(sum(r[1][:2]), r[1][2])] if self.coupler_via is None else [],
            cellcache=cellcache,
        )
        c.add(gdstk.Reference(f, (0, 0)))
        subcells.append(f)
        if self.coupler_via is None:
            c.add(
                gdstk.rectangle(
                    (self.feedline.a, sum(r[1][:2]) + self.coupler_gap),
                    (
                        sum(r[0][:2]) - self.coupler_gap,
                        sum(r[1][:2]) + self.coupler_gap + self.coupler_width,
                    ),
                    *self.coupler_layer,
                ),
            )
        else:
            c.add(
                *self.coupler_via.draw_polys(
                    (
                        self.feedline.a - self.coupler_via.landing_length,
                        sum(r[1][:2]) + self.coupler_gap + max(self.coupler_via.landing_width, self.coupler_width) / 2,
                    ),
                    (
                        sum(r[0][:2]) - self.coupler_gap,
                        sum(r[1][:2]) + self.coupler_gap + max(self.coupler_via.landing_width, self.coupler_width) / 2,
                    ),
                )
            )
        c.add(
            gdstk.rectangle(
                (sum(r[0][:2]) - self.coupler_gap, sum(r[1][:3]) - self.coupler_gap),
                (sum(r[0][:2]), sum(r[1][:3]) - self.coupler_gap - self.coupler_width),
                *self.coupler_layer,
            ),
            gdstk.rectangle(
                (sum(r[0][:2]) - self.coupler_gap, sum(r[1][:2])),
                (sum(r[0][:2]) - self.coupler_gap - self.coupler_width, sum(r[1][:2]) + self.coupler_gap),
                *self.coupler_layer,
            ),
        )
        if self.capacitor and self.inductor:
            lega = self.capacitor.dimensions[0]
            legb = self.capacitor.dimensions[1]
            if self.coupler_via and self.coupler_via.landing_width > self.coupler_width:
                legb -= self.coupler_via.landing_width - self.coupler_width
            lega *= coupler_tunable
            legb *= coupler_tunable
            c.add(
                gdstk.rectangle(
                    (sum(r[0][:2]), sum(r[1][:3]) - self.coupler_gap),
                    (
                        sum(r[0][:2]) + lega,
                        sum(r[1][:3]) - self.coupler_gap - self.coupler_width,
                    ),
                    *self.coupler_layer,
                ),
                gdstk.rectangle(
                    (sum(r[0][:2]) - self.coupler_gap, sum(r[1][:2]) - legb),
                    (sum(r[0][:2]) - self.coupler_gap - self.coupler_width, sum(r[1][:2])),
                    *self.coupler_layer,
                ),
            )
            if self.coupler_fill:
                c.add(
                    gdstk.rectangle(
                        (sum(r[0][:2]) + lega + self.coupler_gap, sum(r[1][:3])),
                        (
                            sum(r[0]) - self.box_width,
                            sum(r[1][:3]) - self.coupler_gap - self.coupler_width,
                        ),
                        *self.box_layer,
                    ),
                    gdstk.rectangle(
                        (sum(r[0][:2]) - self.coupler_gap, self.box_width),
                        (
                            sum(r[0][:2]) - 2 * self.coupler_gap - self.coupler_width,
                            sum(r[1][:2]) - legb - self.coupler_gap,
                        ),
                        *self.box_layer,
                    ),
                )
                if self.coupler_via and self.coupler_via.landing_length > self.coupler_width:
                    c.add(gdstk.rectangle((r[0][0], self.box_width), (sum(r[0][:2]) - self.coupler_width - self.coupler_gap * 2, sum(r[1][:2])), *self.box_layer))

            cap_pos = (sum(r[0][:2]), sum(r[1][:2]) - self.capacitor.dimensions[1])
            if self.coupler_via and self.coupler_via.landing_width > self.coupler_width:
                cap_pos = (cap_pos[0], cap_pos[1] + self.coupler_via.landing_width - self.coupler_width)
            ind_focus = self.inductor.focus_point
            ind_pos = (self.width / 2 - ind_focus[0], cap_pos[1] - self.inductor.dimensions[1])

            port_offset = max(
                0, (cap_pos[0] + self.capacitor.wiring_width - self.inductor.wiring_width) - ind_pos[0]
            )

            ind = self.inductor.draw(port_offset, variation_layer=variation_layer, cellcache=cellcache)
            cap = self.capacitor.draw(
                capacitor_tunable,
                (
                    ind_pos[0] - cap_pos[0] + self.inductor.wiring_width + port_offset,
                    self.inductor.wiring_gap,
                ),
                cellcache=cellcache,
            )
            subcells.append(ind)
            subcells.append(cap)
            c.add(gdstk.Reference(ind, ind_pos), gdstk.Reference(cap, cap_pos))

        c.add(
            gdstk.rectangle((r[0][0], 0), (self.width, self.box_width), *self.box_layer),
            gdstk.rectangle(
                (self.width - self.box_width, self.box_width), (self.width, self.height), *self.box_layer
            ),
            gdstk.rectangle(
                (r[0][0], self.height - self.box_width),
                (self.width - self.box_width, self.height),
                *self.box_layer,
            ),
        )

        if flatten:
            return c.flatten()
        else:
            return [c] + subcells
