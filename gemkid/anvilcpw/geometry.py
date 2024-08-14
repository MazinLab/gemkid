#!/usr/bin/env python3
import gdstk
import numpy as np

from dataclasses import dataclass
from typing import Optional

from ..anvil.layers import NB
from ..layers import DrawingLayer

from .. import geometry

FB = 3.0


def cpwgen(
    length,
    turns,
    start=0.0,
    end=None,
    center=3.0,
    gap=2.0,
    radius=8.0,
    shorted=(False, True),
):
    if end is None:
        end = length
    assert end >= radius
    assert radius * 2 > (gap * 2 + center)
    points = [(start, 0), (length, 0)]
    for i in range(1, turns - 1):
        if i % 2:
            points.append((length, 2 * i * radius))
            points.append((0, 2 * i * radius))
        else:
            points.append((0, 2 * i * radius))
            points.append((length, 2 * i * radius))
    if (turns - 1) % 2:
        points.append((length, 2 * (turns - 1) * radius))
        points.append((length - end, 2 * (turns - 1) * radius))
    else:
        points.append((0, 2 * (turns - 1) * radius))
        points.append((end, 2 * (turns - 1) * radius))

    path = gdstk.FlexPath(
        points,
        [gap, gap],
        [-(center + gap) / 2, (center + gap) / 2],
        bend_radius=radius,
    )
    geom = path.to_polygons()
    if not shorted[0]:
        geom.append(
            gdstk.rectangle(
                (start - gap, -(gap + center / 2)), (start, (gap + center / 2))
            )
        )
    if not shorted[1]:
        if (turns - 1) % 2:
            geom.append(
                gdstk.rectangle(
                    (points[-1][0] - gap, points[-1][1] - (gap + center / 2)),
                    (points[-1][0], points[-1][1] + (gap + center / 2)),
                )
            )
        else:
            geom.append(
                gdstk.rectangle(
                    (points[-1][0] + gap, points[-1][1] - (gap + center / 2)),
                    (points[-1][0], points[-1][1] + (gap + center / 2)),
                )
            )
    bends = 2 * turns - 2
    length_total = (turns - 2) * length + start + end
    length_total -= bends * (np.pi * radius - 2 * radius)
    return geom, length_total, path


@dataclass(eq=True, frozen=True)
class FeedlineConfig(geometry.FeedlineConfig):
    a: float = 40
    b: float = FB
    c: float = 10 - FB
    feed_layer: tuple[int, int] | DrawingLayer = NB
    ground_layer: tuple[int, int] | DrawingLayer = NB


@dataclass(eq=True, frozen=True)
class CPWConfig(geometry.GeomConfigMarker):
    feedline: FeedlineConfig = FeedlineConfig()
    length: float = 400.0
    turns: int = 15
    start: float = 350
    end: Optional[float] = None
    center: float = 3.0
    gap: float = 2.0
    radius: float = 6.0
    shorted: tuple[bool, bool] = (False, True)
    coupling_gap: float = 7.0
    padding: float = 4
    layer: DrawingLayer = NB

    @property
    def _meander_bbox(self) -> list[tuple[float, float]]:
        m = self.meander[2].spine()
        hw = self.gap + self.center / 2
        meander_bbox = [
            (np.min(m[::, 0]) - hw, np.max(m[::, 0]) + hw),
            (np.min(m[::, 1]) - hw, np.max(m[::, 1]) + hw),
        ]
        return meander_bbox

    @property
    def dimensions(self):
        meander_bbox = self._meander_bbox
        height = meander_bbox[0][1] - meander_bbox[0][0] + 2 * self.padding
        width = (
            meander_bbox[1][1]
            - meander_bbox[1][0]
            + self.padding
            + self.feedline.width_half
            - self.feedline.c
            + self.coupling_gap
        )
        return width, height

    @property
    def meander_length(self):
        return self.meander[1]

    @property
    def meander(self):
        return cpwgen(
            self.length,
            self.turns,
            self.start,
            self.end,
            self.center,
            self.gap,
            self.radius,
            self.shorted,
        )

    def draw(self, variation_layer=None, flatten=None, cellcache=None):
        cellname = "Meander-{:s}".format(hex(abs(hash(self))))
        c = gdstk.Cell(cellname)
        dim = self.dimensions
        flp = self.feedline.draw_half(height=dim[1], ports=[]).polygons
        rect = gdstk.rectangle(
            (self.feedline.width_half, 0), (dim[0], dim[1]), *self.layer
        )
        flp.append(rect)
        c.add(
            *gdstk.boolean(
                flp,
                [
                    i.rotate(np.pi / 2, (0, 0))
                    .mirror((0, dim[1]))
                    .translate(
                        self.feedline.width_half
                        + self.coupling_gap
                        - self._meander_bbox[1][0]
                        - self.feedline.c,
                        self.padding - self._meander_bbox[0][0],
                    )
                    for i in self.meander[0]
                ],
                "not",
            )
        )
        return c


if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("AnvilCPWResonators")

    c = CPWConfig(FeedlineConfig())
    print("Length: {:.1f}".format(c.meander_length))
    cd = c.draw()

    top = gdstk.Cell("top")
    top.add(gdstk.Reference(cd))

    lib.add(top, cd)
    lib.write_gds("anvilcpw.gds")
