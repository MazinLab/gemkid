#!/usr/bin/env python3
import gdstk
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass(eq=True, frozen=True)
class InductorConfig:
    legs: int = 15
    leg_gap: float = 0.5
    leg_length: float = 102.5
    leg_width: float = 1.5
    leg_landing: float = 1.5
    leg_layer: tuple[int, int] = (1, 0)
    wiring_width: float = 2
    wiring_gap: float = 0.5
    wiring_layer: tuple[int, int] = (0, 0)

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

    def draw(self, port_offset=0.0, cellcache={}):
        regions = self.regions()
        h = hex(abs(hash(self) + hash(port_offset)))
        cellname = "UE1Inductor-{:s}".format(h)
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
                *self.wiring_layer
            ),
            gdstk.rectangle(
                (port_offset, sum(regions[1]) - self.wiring_gap),
                (port_offset + self.wiring_width, sum(regions[1])),
                *self.wiring_layer
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
class CapacitorConfig:
    legs: int = 46
    leg_gap: float = 1
    leg_length: tuple[float, float] = (114, 62)
    leg_width: float = 1
    leg_landing: float = 0
    leg_layer: tuple[int, int] = (0, 0)
    wiring_width: float = 5
    wiring_layer: tuple[int, int] = (0, 0)

    @property
    def dimensions(self):
        return (
            self.wiring_width * 2 + max(self.leg_length) + self.leg_gap,
            (self.leg_width + self.leg_gap) * (self.legs + 1) + self.wiring_width,
        )

    def caprange(self):
        return self.legs * min(self.leg_length), self.legs * max(self.leg_length)

    def draw(self, tunable: float, port: tuple[float, float], cellcache={}):
        assert (
            tunable >= 0 and tunable <= 1
        ), "The capacitor tunable should be a fraction of the total possible in the [0, 1]"

        dim = self.dimensions

        h = hex(abs(hash(self) + hash(port) + hash(tunable)))
        cellname = "UE1Capacitor-{:s}".format(h)
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
                        (dim[0] - self.wiring_width, self.wiring_width),
                    ),
                ],
                gdstk.rectangle((port[0], 0), (port[0] + port[1], self.wiring_width)),
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
                        self.wiring_width + self.leg_gap + i * (self.leg_gap + self.leg_width),
                    ),
                    (self.wiring_width + le, self.wiring_width + (i + 1) * (self.leg_gap + self.leg_width)),
                    *self.leg_layer,
                )
                if (i + o) % 2 == 0
                else gdstk.rectangle(
                    (
                        self.wiring_width + max(self.leg_length) + self.leg_gap - le,
                        self.wiring_width + self.leg_gap + i * (self.leg_gap + self.leg_width),
                    ),
                    (
                        self.wiring_width + max(self.leg_length) + self.leg_gap + self.leg_landing,
                        self.wiring_width + (i + 1) * (self.leg_gap + self.leg_width),
                    ),
                    *self.leg_layer,
                )
            )
            for i, le in enumerate(leg_lengths)
        ]
        c.add(*legs)
        return c


@dataclass(eq=True, frozen=True)
class FeedlineConfig:
    a: float = 3.5
    b: float = 2
    c: float = 9.5
    feed_layer: tuple[int, int] = (0, 0)
    ground_layer: tuple[int, int] = (0, 0)

    @property
    def width(self):
        return 2 * self.width_half

    def draw(
        self, height: float, ports: tuple[list[tuple[float, float]], list[tuple[float, float]]], cellcache={}
    ):
        h = hex(abs(hash(hash(self) + sum([hash(port) for port in ports[0] + ports[1]]) + hash(height))))
        cellname = "UE1Feedline-{:s}".format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c
        cl = self.draw_half(height=height, ports=ports[0], cellcache=cellcache)
        cr = self.draw_half(height=height, ports=ports[1], cellcache=cellcache)
        c.add(gdstk.Reference(cl, (0, 0), x_reflection=True))
        c.add(gdstk.Reference(cr, (self.width_half, 0)))
        return c.flatten()

    @property
    def width_half(self):
        return self.a + self.b + self.c

    def draw_half(self, height: float, ports: list[tuple[float, float]], cellcache={}):
        h = hex(abs(hash(hash(self) + sum([hash(port) for port in ports]) + hash(height))))
        cellname = "UE1FeedlineHalf-{:s}".format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c
        c.add(gdstk.rectangle((0, 0), (self.a, height), *self.feed_layer))
        c.add(
            *gdstk.boolean(
                gdstk.rectangle((self.a + self.b, 0), (self.width_half, height)),
                [
                    gdstk.rectangle((self.a + self.b, pos), (self.width_half, pos + width))
                    for pos, width in ports
                ],
                "not",
                0.0001,
                *self.ground_layer,
            )
        )
        return c


@dataclass(eq=True, frozen=True)
class BoxConfig:
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: FeedlineConfig
    coupler_width: float = 1.5
    coupler_gap: float = 2.0
    coupler_layer: tuple[int, int] = (0, 0)
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: tuple[int, int] = (0, 0)
    width: float = 150
    height: float = 150

    @property
    def coupler_range(self):
        if self.capacitor:
            return sum(self.capacitor.dimensions)
        return None

    @property
    def dimensions(self):
        return self.width, self.height

    def regions(self):
        x = [self.feedline.width_half, self.coupler_gap * 2 + self.coupler_width]
        x.append(sum(x) - self.box_width - self.box_gap)
        x.append(self.box_width + self.box_gap)
        y = [
            self.box_width + self.box_gap,
            self.height - 2 * self.box_width - self.box_gap - 2 * self.coupler_gap - self.coupler_width,
            2 * self.coupler_gap + self.coupler_width,
            self.box_width,
        ]
        return x, y

    def draw(self, coupler_tunable: float = 1.0, capacitor_tunable: float = 1.0, flatten=True, cellcache={}):
        assert ((self.inductor is not None) and (self.capacitor is not None)) or (
            self.inductor is None and self.capacitor is None
        )
        r = self.regions()
        h = hex(abs(hash(self) + hash(coupler_tunable) + hash(capacitor_tunable)))
        subcells = []

        cellname = ("UE1BoxFlat-{:s}" if flatten else "UE1Box-{:s}").format(h)
        c = gdstk.Cell(cellname)
        if cellcache is not None:
            if cellname in cellcache.keys():
                return cellcache[cellname]
            else:
                cellcache[cellname] = c

        f = self.feedline.draw_half(self.height, ports=[(sum(r[1][:2]), r[1][2])], cellcache=cellcache)
        c.add(gdstk.Reference(f, (0, 0)))
        subcells.append(f)
        c.add(
            gdstk.rectangle(
                (self.feedline.a, sum(r[1][:2]) + self.coupler_gap),
                (
                    sum(r[0][:2]),
                    sum(r[1][:2]) + self.coupler_gap + self.coupler_width,
                ),
                *self.coupler_layer,
            ),
            gdstk.rectangle(
                (r[0][0] + self.coupler_gap, sum(r[1][:2])),
                (r[0][0] + self.coupler_gap + self.coupler_width, sum(r[1][:2]) + self.coupler_gap),
                *self.coupler_layer,
            ),
        )
        if self.capacitor and self.inductor:
            lega = self.capacitor.dimensions[0]
            legb = self.capacitor.dimensions[1]
            lega *= coupler_tunable
            legb *= coupler_tunable
            c.add(
                gdstk.rectangle(
                    (sum(r[0][:2]), sum(r[1][:2]) + self.coupler_gap),
                    (
                        sum(r[0][:2]) + lega,
                        sum(r[1][:2]) + self.coupler_gap + self.coupler_width,
                    ),
                    *self.coupler_layer,
                ),
                gdstk.rectangle(
                    (r[0][0] + self.coupler_gap, sum(r[1][:2]) - legb),
                    (r[0][0] + self.coupler_gap + self.coupler_width, sum(r[1][:2])),
                    *self.coupler_layer,
                ),
            )

            cap_pos = (sum(r[0][:2]), sum(r[1][:2]) - self.capacitor.dimensions[1])
            ind_focus = self.inductor.focus_point
            ind_pos = (self.width / 2 - ind_focus[0], cap_pos[1] - self.inductor.dimensions[1])

            port_offset = max(0, (cap_pos[0] + self.capacitor.wiring_width - self.inductor.wiring_width) - ind_pos[0])

            ind = self.inductor.draw(port_offset, cellcache=cellcache)
            cap = self.capacitor.draw(
                capacitor_tunable,
                (ind_pos[0] - cap_pos[0] + self.inductor.wiring_width + port_offset, self.inductor.wiring_gap),
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


if __name__ == "__main__":
    lib = gdstk.Library("ue1example.gds")
    b = BoxConfig(InductorConfig(), CapacitorConfig(), FeedlineConfig())
    eb = BoxConfig(None, None, FeedlineConfig())
    lib.add(b.draw(coupler_tunable=0.5, capacitor_tunable=0.5), eb.draw())
    lib.write_gds("ue1example.gds")
