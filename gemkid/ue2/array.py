import gdstk

from .geometry import *
from ..ue1.layers import ATA_NB, HF, HF_CONTACT, HF_CONTACT_LIFTOFF, ASI, ASI_EP

if __name__ == "__main__":
    import numpy as np

    lib = gdstk.Library("ue2array-ucsb.gds")
    top = gdstk.Cell("tm4top8pharray")
    b = BoxConfig(
        InductorConfig(),
        CapacitorConfig(),
        UEFeedlineConfig(),
    )
    flstub = UEFeedlineConfig().draw(222, ports=([], []), cellcache={})
    flstub.add(gdstk.rectangle((UEFeedlineConfig().width_half, 0), (444, 222), *ATA_NB))
    flstub.add(gdstk.rectangle((-UEFeedlineConfig().width_half, 0), (-444, 222), *ATA_NB))
    flstub.add(gdstk.cross(b.focus_point, 32, 4, *ASI))
    flstub.add(gdstk.cross((-b.focus_point[0], b.focus_point[1]), 32, 4, *ASI))
    lib.add(flstub)

    ROWS = 10
    COLS = 10
    for x in range(-2, 3):
        for y in range(-ROWS // 2, ROWS // 2):
            left = b.draw(cellcache={})
            right = b.draw(cellcache={})
            left.name = f"left-r{y}c{x}"
            right.name = f"right-r{y}c{x}"
            if y != -5:
                top.add(gdstk.Reference(flstub, origin=(4 * 222 * x, 2 * y * 222 - b.focus_point[1])))
            top.add(gdstk.Reference(left, origin=(4 * 222 * x, 2 * y * 222 - b.focus_point[1] + 222)))
            top.add(
                gdstk.Reference(
                    right,
                    origin=(4 * 222 * x, 2 * y * 222 - b.focus_point[1] + 222),
                    x_reflection=True,
                    rotation=np.pi,
                )
            )
            lib.add(left, right)

    ARRAY_BOTTOM = (-ROWS // 2) * 444 - b.focus_point[1] + 222
    ARRAY_TOP = ARRAY_BOTTOM + ROWS * 444 - 222
    ARRAY_LEFT = -444*5
    ARRAY_RIGHT = 444*5
    CURVATURE_RADIUS = 100
    SPACING = 100

    wiring = gdstk.Cell("Wiring")
    paths = []
    for x in range(-2, 2, 2):
        p = gdstk.RobustPath(
            (2*x*444, ARRAY_BOTTOM),
            [UEFeedlineConfig().b, UEFeedlineConfig.b],
            [UEFeedlineConfig().a + UEFeedlineConfig().b / 2, -UEFeedlineConfig().a - UEFeedlineConfig().b / 2],
        )
        p.arc(CURVATURE_RADIUS, -np.pi, -np.pi/2)
        p.horizontal(444 * 2 - CURVATURE_RADIUS * 2, relative=True)
        p.arc(CURVATURE_RADIUS, -np.pi/2, 0)
        paths.append(p)
    p = gdstk.RobustPath(
        (0, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING),
        [UEFeedlineConfig().b, UEFeedlineConfig.b],
        [UEFeedlineConfig().a + UEFeedlineConfig().b / 2, -UEFeedlineConfig().a - UEFeedlineConfig().b / 2],
    )
    p.arc(CURVATURE_RADIUS, -np.pi, -np.pi*3/2)
    p.horizontal(444*4 - CURVATURE_RADIUS * 2, relative=True)
    p.arc(CURVATURE_RADIUS, -np.pi/2, 0)
    p.vertical(ARRAY_BOTTOM)
    paths.append(p)

    rect = gdstk.rectangle((ARRAY_LEFT, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING), (ARRAY_RIGHT, ARRAY_BOTTOM))
    wiring.add(*gdstk.boolean(rect, paths, "not", 0.0001, *ATA_NB))

    prect = gdstk.rectangle((ARRAY_LEFT, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING - b.focus_point[1] * 4), (ARRAY_RIGHT, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING))
    p = gdstk.RobustPath(
        (0, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING),
        [UEFeedlineConfig().b, UEFeedlineConfig.b],
        [UEFeedlineConfig().a + UEFeedlineConfig().b / 2, -UEFeedlineConfig().a - UEFeedlineConfig().b / 2],
    )
    p.vertical(-b.focus_point[1] * 4, relative=True)
    top.add(*gdstk.boolean(prect, p, "not", 0.0001, *ATA_NB))

    ARRAY_WIRED_BOTTOM = ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING - b.focus_point[1] * 4
    ARRAY_WIRED_TOP = -ARRAY_WIRED_BOTTOM

    capping = gdstk.Cell("Bond Cap")
    m = 18
    f = UEFeedlineConfig()
    HEIGHT = 750
    TAPER = 70
    stop = HEIGHT - TAPER
    outline = gdstk.Polygon(
        [
            (-(f.a + f.b), HEIGHT),
            (-(f.a + f.b) * m, stop),
            (-(f.a + f.b) * m, stop - (f.a + f.b * 0.5) * m * 2),
            ((f.a + f.b) * m, stop - (f.a + f.b * 0.5) * m * 2),
            ((f.a + f.b) * m, stop),
            ((f.a + f.b), HEIGHT),
            ((f.a), HEIGHT),
            ((f.a) * m, stop),
            ((f.a) * m, stop - (f.a) * m * 2),
            (-(f.a) * m, stop - (f.a) * m * 2),
            (-(f.a) * m, stop),
            (-(f.a), HEIGHT),
        ],
        *ATA_NB,
    ).translate((0, ARRAY_WIRED_BOTTOM - HEIGHT))
    rect = gdstk.rectangle((ARRAY_LEFT, ARRAY_WIRED_BOTTOM - 304 - 13), (ARRAY_RIGHT, ARRAY_WIRED_BOTTOM))
    capping.add(*gdstk.boolean(rect, outline, "not", 0.0001, *ATA_NB))

    top.add(gdstk.Reference(wiring))
    top.add(gdstk.Reference(wiring, rotation=np.pi, origin=(0, b.focus_point[1] * 4)))
    top.add(gdstk.Reference(capping))
    top.add(gdstk.Reference(capping, rotation=np.pi))

    top.add(gdstk.rectangle((-5600/2, -5600/2), (ARRAY_LEFT, 5600/2), *ATA_NB))
    top.add(gdstk.rectangle((5600/2, -5600/2), (ARRAY_RIGHT, 5600/2), *ATA_NB))
    top.add(
        gdstk.Polygon(
            [
                (-3000, -3000),
                (-3000, 3000),
                (3000, 3000),
                (3000, -3000),
                (-2925, -3000),
                (-2925, -2925),
                (2925, -2925),
                (2925, 2925),
                (-2925, 2925),
                (-2925, -2925)
            ]
        )
    )
    lib.add(capping)
    lib.add(wiring)
    lib.add(top)
    lib.write_gds("ue2array-ucsb.gds")
