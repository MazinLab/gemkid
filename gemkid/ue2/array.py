import gdstk

from .geometry import *
from ..ue1.layers import ATA_NB, HF, HF_CONTACT, HF_CONTACT_LIFTOFF, ASI, ASI_EP, MLA_MARK, MLA_PITCH


@dataclass(eq=True, frozen=True)
class Vernier:
    vernier_delta: float = 0.25
    vernier_count: int = 4
    vernier_width: float = 4
    vernier_length: float = 16
    vernier_spacing: float = 8
    center_stub: float = 4
    lower_layer: tuple[int, int] | DrawingLayer = ATA_NB
    upper_layer: tuple[int, int] | DrawingLayer = MLA_MARK

    def draw_polys(self, point: tuple[float, float], rotation: float = 0.0):
        rects = []

        rects.append(
            gdstk.rectangle(
                (0, -self.vernier_width / 2),
                (self.vernier_length + self.center_stub, self.vernier_width / 2),
                *self.lower_layer,
            ),
        )
        rects.append(
            gdstk.rectangle(
                (0, -self.vernier_width / 2),
                (-self.vernier_length - self.center_stub, self.vernier_width / 2),
                *self.upper_layer,
            ),
        )
        for d in range(1, self.vernier_count + 1):
            rects.append(
                gdstk.rectangle(
                    (0, d * self.vernier_spacing - self.vernier_width / 2),
                    (self.vernier_length, d * self.vernier_spacing + self.vernier_width / 2),
                    *self.lower_layer,
                ),
            )
            rects.append(
                gdstk.rectangle(
                    (0, d * (self.vernier_spacing + self.vernier_delta) - self.vernier_width / 2),
                    (
                        -self.vernier_length,
                        d * (self.vernier_spacing + self.vernier_delta) + self.vernier_width / 2,
                    ),
                    *self.upper_layer,
                )
            )
            rects.append(
                gdstk.rectangle(
                    (0, -d * self.vernier_spacing - self.vernier_width / 2),
                    (self.vernier_length, -d * self.vernier_spacing + self.vernier_width / 2),
                    *self.lower_layer,
                ),
            )
            rects.append(
                gdstk.rectangle(
                    (0, -d * (self.vernier_spacing + self.vernier_delta) - self.vernier_width / 2),
                    (
                        -self.vernier_length,
                        -d * (self.vernier_spacing + self.vernier_delta) + self.vernier_width / 2,
                    ),
                    *self.upper_layer,
                )
            )
        return [p.rotate(rotation).translate(point) for p in rects]


if __name__ == "__main__":
    import numpy as np

    variants = [
        (3, 0),
        (3, 5),
        (3, 10),
        (3, 21.5),
    ]
    lib = gdstk.Library("ue2array-ucsb.gds")

    def make_variant(variant):
        top = gdstk.Cell(f"tm4top8pharray-v{variant:d}")
        b = BoxConfig(
            InductorConfig(via_gap=variants[variant][0], via_inset=variants[variant][1]),
            CapacitorConfig(),
            UEFeedlineConfig(),
        )

        shuffler = np.arange(36)
        np.random.seed(42)
        np.random.shuffle(shuffler)
        freqs = []
        for n in [
            np.linspace(4, 4.36, 6, endpoint=False),
            np.linspace(5, 5.8, 8, endpoint=False),
            np.linspace(6.0, 7.1, 10, endpoint=False),
            np.linspace(8 - 0.6, 8, 12, endpoint=False),
        ]:
            freqs.extend(list(n))
        freqs = np.array(freqs)[shuffler].reshape((6, 6))

        COLUMN_PAD = 444
        STUB_HEIGHT = 444
        flstub = UEFeedlineConfig().draw(STUB_HEIGHT, ports=([], []), cellcache={})
        flstub.name = f"flstub-v{variant:d}"
        rects = [
            gdstk.rectangle((UEFeedlineConfig().width_half, 0), (444, STUB_HEIGHT)),
            gdstk.rectangle((-UEFeedlineConfig().width_half, 0), (-444, STUB_HEIGHT)),
        ]
        crosses = [
            gdstk.cross(b.focus_point, 32, 4),
            gdstk.cross((-b.focus_point[0], b.focus_point[1]), 32, 4),
            gdstk.cross((+b.focus_point[0], b.focus_point[1] + 222), 32, 4),
            gdstk.cross((-b.focus_point[0], b.focus_point[1] + 222), 32, 4),
        ]
        flstub.add(*gdstk.boolean(rects, crosses, "not", 0.0001, *ATA_NB))

        lib.add(flstub)

        ROWS = 6
        COLS = 6
        text = []
        text_origin = (222 * -12, 222 * -10)
        for i, x in enumerate(range(-COLS // 4 + 1, COLS // 4 + 1)):
            for j, y in enumerate(range(-ROWS // 2, ROWS // 2)):
                left = b.draw(cellcache={})
                right = b.draw(cellcache={})
                left.name = f"left-r{j}c{i}-v{variant}"
                right.name = f"right-r{j}c{i}-v{variant}"
                if y != -ROWS // 4 - 1:
                    top.add(
                        gdstk.Reference(
                            flstub,
                            origin=(
                                4 * 222 * x + x * COLUMN_PAD,
                                y * 222 + y * STUB_HEIGHT - 222 - b.focus_point[1],
                            ),
                        )
                    )
                top.add(
                    gdstk.Reference(
                        left,
                        origin=(
                            4 * 222 * x + x * COLUMN_PAD,
                            y * 222 + y * STUB_HEIGHT - b.focus_point[1] + 222,
                        ),
                    )
                )
                top.add(
                    gdstk.Reference(
                        right,
                        origin=(
                            4 * 222 * x + x * COLUMN_PAD,
                            y * 222 + y * STUB_HEIGHT - b.focus_point[1] + 222,
                        ),
                        x_reflection=True,
                        rotation=np.pi,
                    )
                )
                lib.add(left, right)
                text.extend(
                    gdstk.text(
                        f"{freqs[i * 2 + 1][j]:.3f} {freqs[i * 2][j]:.3f}",
                        32,
                        (4 * 64 * i + text_origin[0], j * 128 + text_origin[1]),
                        False,
                        *HF,
                    )
                )
        for x in range(-7, 8):
            for y in range(-7, 8):
                flstub.add(gdstk.cross((x * 222, y * 222 + b.focus_point[1] + 222), 32, 4, *MLA_PITCH))

        ARRAY_BOTTOM = (-ROWS // 2) * (222 + STUB_HEIGHT) - b.focus_point[1] + 222
        ARRAY_TOP = ARRAY_BOTTOM + ROWS * (222 + STUB_HEIGHT) - STUB_HEIGHT
        for x in range(-COLS // 4 + 1, COLS // 4):
            xll = 4 * 222 * x + x * COLUMN_PAD + 444
            rect = gdstk.rectangle(
                (xll, ARRAY_BOTTOM),
                (xll + COLUMN_PAD, ARRAY_TOP),
            )
            crosses = []
            for y in range(0, int(min(-ARRAY_BOTTOM, ARRAY_TOP)), 222):
                crosses.append(gdstk.cross((xll + 222, y), 32, 4))
                crosses.append(gdstk.cross((xll + 222, -y - 222), 32, 4))
            top.add(*gdstk.boolean(rect, crosses, "not", 0.0001, *ATA_NB))

        ARRAY_LEFT = -444 * COLS // 2 - (COLS - 3) // 2 * COLUMN_PAD
        ARRAY_RIGHT = +444 * COLS // 2 + (COLS - 3) // 2 * COLUMN_PAD
        CURVATURE_RADIUS = 200
        SPACING = 100

        wiring = gdstk.Cell(f"Wiring-v{variant:d}")
        paths = []
        for x in range(-1, 1, 2):
            p = gdstk.RobustPath(
                (2 * x * 444 + x * COLUMN_PAD, ARRAY_BOTTOM),
                [UEFeedlineConfig().b, UEFeedlineConfig.b],
                [
                    UEFeedlineConfig().a + UEFeedlineConfig().b / 2,
                    -UEFeedlineConfig().a - UEFeedlineConfig().b / 2,
                ],
            )
            p.arc(CURVATURE_RADIUS, -np.pi, -np.pi / 2)
            p.horizontal(444 * 2 + COLUMN_PAD - CURVATURE_RADIUS * 2, relative=True)
            p.arc(CURVATURE_RADIUS, -np.pi / 2, 0)
            paths.append(p)
        p = gdstk.RobustPath(
            (0, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING),
            [UEFeedlineConfig().b, UEFeedlineConfig.b],
            [
                UEFeedlineConfig().a + UEFeedlineConfig().b / 2,
                -UEFeedlineConfig().a - UEFeedlineConfig().b / 2,
            ],
        )
        p.arc(CURVATURE_RADIUS, -np.pi, -np.pi * 3 / 2)
        p.horizontal(444 * 3 - CURVATURE_RADIUS * 2, relative=True)
        p.arc(CURVATURE_RADIUS, -np.pi / 2, 0)
        p.vertical(ARRAY_BOTTOM)
        paths.append(p)

        ARRAY_WIRED_BOTTOM = ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING
        ARRAY_WIRED_TOP = ARRAY_TOP + CURVATURE_RADIUS * 2 + SPACING
        rect = gdstk.rectangle((ARRAY_LEFT, ARRAY_WIRED_BOTTOM), (ARRAY_RIGHT, ARRAY_BOTTOM))
        wiring.add(*gdstk.boolean(rect, paths, "not", 0.0001, *ATA_NB))

        capping = gdstk.Cell(f"Bond Cap-v{variant:d}")
        m = 22
        f = UEFeedlineConfig()
        CAPPING_HEIGHT = 450
        HEIGHT = 750
        TAPER = 125
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
        ).translate((0, -5600 // 2 - HEIGHT + CAPPING_HEIGHT))
        rect = gdstk.rectangle((ARRAY_LEFT, -5600 // 2), (ARRAY_RIGHT, -5600 // 2 + CAPPING_HEIGHT))
        for i in range(-3, 3 + 1):
            capping.add(
                gdstk.ellipse(
                    (800 * i, -2575),
                    125.0,
                    tolerance=1,
                    layer=SOLDER_MASK.gds_layer[0],
                    datatype=SOLDER_MASK.gds_layer[1],
                )
            )
        capping.add(*gdstk.boolean(rect, outline, "not", 0.0001, *ATA_NB))

        top.add(gdstk.Reference(wiring))
        top.add(gdstk.Reference(wiring, rotation=np.pi, origin=(0, b.focus_point[1] * 4 - STUB_HEIGHT // 2)))
        top.add(gdstk.Reference(capping))
        top.add(gdstk.Reference(capping, rotation=np.pi))

        prect = gdstk.rectangle((ARRAY_LEFT, -5600 // 2 + CAPPING_HEIGHT), (ARRAY_RIGHT, ARRAY_WIRED_BOTTOM))
        p = gdstk.RobustPath(
            (0, -5600 // 2),
            [UEFeedlineConfig().b, UEFeedlineConfig.b],
            [
                UEFeedlineConfig().a + UEFeedlineConfig().b / 2,
                -UEFeedlineConfig().a - UEFeedlineConfig().b / 2,
            ],
        )
        p.vertical(ARRAY_WIRED_BOTTOM)
        top.add(*gdstk.boolean(prect, p, "not", 0.0001, *ATA_NB))

        prect = gdstk.rectangle((ARRAY_LEFT, +5600 // 2 - CAPPING_HEIGHT), (ARRAY_RIGHT, ARRAY_WIRED_TOP))
        p = gdstk.RobustPath(
            (0, 5600 // 2),
            [UEFeedlineConfig().b, UEFeedlineConfig.b],
            [
                UEFeedlineConfig().a + UEFeedlineConfig().b / 2,
                -UEFeedlineConfig().a - UEFeedlineConfig().b / 2,
            ],
        )
        p.vertical(ARRAY_WIRED_TOP)
        top.add(*gdstk.boolean(prect, p, "not", 0.0001, *ATA_NB))

        via = ViaWire()
        xovers = gdstk.Cell(f"crossovers-v{variant:d}")
        XOVER_LENGTH = 56
        for y in range(-ROWS // 2, ROWS // 2):
            yposh = y * 222 + y * STUB_HEIGHT - b.focus_point[1] + 222
            yposv = yposh + b.height - b.box_width - b.coupler_gap - b.coupler_width / 2
            xovers.add(
                *via.draw_polys(
                    (-f.a - f.b - f.c / 2, -XOVER_LENGTH / 2 + yposv),
                    (-f.a - f.b - f.c / 2, +XOVER_LENGTH / 2 + yposv),
                )
            )
            xovers.add(
                *via.draw_polys(
                    (+f.a + f.b + f.c / 2, -XOVER_LENGTH / 2 + yposv),
                    (+f.a + f.b + f.c / 2, +XOVER_LENGTH / 2 + yposv),
                )
            )
            xovers.add(*via.draw_polys((-XOVER_LENGTH / 2, yposh), (+XOVER_LENGTH / 2, yposh)))
            xovers.add(*via.draw_polys((-XOVER_LENGTH / 2, yposh), (+XOVER_LENGTH / 2, yposh)))
        xovers.add(
            *via.draw_polys(
                (-XOVER_LENGTH / 2, ARRAY_TOP + CURVATURE_RADIUS + SPACING + CURVATURE_RADIUS),
                (+XOVER_LENGTH / 2, ARRAY_TOP + CURVATURE_RADIUS + SPACING + CURVATURE_RADIUS),
            )
        )
        xovers.add(
            *via.draw_polys(
                (-XOVER_LENGTH / 2, ARRAY_BOTTOM - CURVATURE_RADIUS - SPACING - CURVATURE_RADIUS),
                (+XOVER_LENGTH / 2, ARRAY_BOTTOM - CURVATURE_RADIUS - SPACING - CURVATURE_RADIUS),
            )
        )

        for y in [
            ARRAY_BOTTOM - CURVATURE_RADIUS,
            ARRAY_BOTTOM - CURVATURE_RADIUS - SPACING,
            ARRAY_TOP + CURVATURE_RADIUS,
            ARRAY_TOP + CURVATURE_RADIUS + SPACING,
        ]:
            xovers.add(
                *via.draw_polys(
                    (-CURVATURE_RADIUS, -XOVER_LENGTH / 2 + y),
                    (-CURVATURE_RADIUS, +XOVER_LENGTH / 2 + y),
                )
            )
            xovers.add(
                *via.draw_polys(
                    (+CURVATURE_RADIUS, -XOVER_LENGTH / 2 + y),
                    (+CURVATURE_RADIUS, +XOVER_LENGTH / 2 + y),
                )
            )

        for x in range(-COLS // 4 + 1, COLS // 4 + 1):
            top.add(gdstk.Reference(xovers, (4 * 222 * x + x * COLUMN_PAD, 0)))

        crosses = []
        for x in [222 * 12, -222 * 12]:
            for y in [222 * 12, -222 * 12]:
                crosses.extend(Vernier().draw_polys((x + 111, y), 0.0))
                crosses.extend(Vernier().draw_polys((x - 111, y), np.pi))
                crosses.extend(Vernier().draw_polys((x, y + 111), np.pi / 2))
                crosses.extend(Vernier().draw_polys((x, y - 111), -np.pi / 2))
                crosses.append(gdstk.cross((x, y), 75, 20, *ATA_NB))
                crosses.append(gdstk.cross((x, y), 72, 18, *MLA_MARK))

        crosses_atanb = [
            c for c in crosses if c.layer == ATA_NB.gds_layer[0] and c.datatype == ATA_NB.gds_layer[1]
        ]
        crosses_mark = [
            c for c in crosses if c.layer == MLA_MARK.gds_layer[0] and c.datatype == MLA_MARK.gds_layer[1]
        ]
        rects = [
            gdstk.rectangle((-5600 / 2, -5600 / 2), (ARRAY_LEFT, 5600 / 2)),
            gdstk.rectangle((5600 / 2, -5600 / 2), (ARRAY_RIGHT, 5600 / 2)),
        ]

        AP = 2850
        for x, y in [(-AP, -AP), (-AP, AP), (AP, AP), (AP, -AP)]:
            top.add(gdstk.cross((x, y), 100, 20, *ATA_NB))
            top.add(gdstk.cross((x, y), 100, 20, *HF))
            top.add(gdstk.rectangle((x - 50, y - 50), (x + 50, y + 50), *HF_CONTACT))

        for rot in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
            vs = []
            for i, pair in enumerate(
                [
                    (ATA_NB, HF),
                    (ATA_NB, HF_CONTACT),
                    (ATA_NB, HF_CONTACT_LIFTOFF),
                    (ATA_NB, ASI),
                    (ATA_NB, ASI_EP),
                ]
            ):
                vs.extend(
                    Vernier(lower_layer=pair[0], upper_layer=pair[1]).draw_polys((-AP + 100 + 50 * i, -AP))
                )
            top.add(*[v.rotate(rot) for v in vs])
            top.add(*[v.copy().mirror((-1, -1), (1, 1)) for v in vs])

        top.add(*gdstk.boolean(rects, crosses_atanb + text, "not", 0.0001, *ATA_NB))
        top.add(*crosses_mark)
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
                    (-2925, -3000),
                ]
            )
        )
        lib.add(xovers)
        lib.add(capping)
        lib.add(wiring)
        lib.add(top)
        return top

    for i in range(4):
        make_variant(i)
    lib.write_gds("ue2-ucsb-array.gds")
