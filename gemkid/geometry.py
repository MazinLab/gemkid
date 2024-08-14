import abc

import gdstk
import numpy as np

from dataclasses import dataclass
from .layers import DrawingLayer


class GeomConfigMarker(abc.ABC):
    pass


@dataclass(eq=True, frozen=True)
class FeedlineConfig(GeomConfigMarker):
    a: float = 3.5
    b: float = 2
    c: float = 9.5
    feed_layer: tuple[int, int] | DrawingLayer = (0, 0)
    ground_layer: tuple[int, int] | DrawingLayer = (0, 0)

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
        c.add(gdstk.Reference(cl, (0, height), rotation=np.pi))
        c.add(gdstk.Reference(cr, (0, 0)))
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
