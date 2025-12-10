import gdstk

from .geometry import *
from ..ue1.layers import ATA_NB, HF_CONTACT, HF_CONTACT_LIFTOFF, ASI, ASI_EP, MLA_MARK, MLA_PITCH


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
    tiebar: bool = True

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
        if self.tiebar:
            rects.append(
                gdstk.rectangle(
                    (self.vernier_length - self.vernier_width, self.vernier_count * (self.vernier_spacing)),
                    (self.vernier_length, -self.vernier_count * (self.vernier_spacing)),
                    *self.lower_layer,
                )
            )
            rects.append(
                gdstk.rectangle(
                    (-self.vernier_length + self.vernier_width, self.vernier_count * (self.vernier_spacing + self.vernier_delta)),
                    (-self.vernier_length, -self.vernier_count * (self.vernier_spacing + self.vernier_delta)),
                    *self.upper_layer,
                )
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


def make_array_variant(lib, variant, resonators, boxconfig, feedlineconfig, viawire, arrayname="", flmult=22):
    b = boxconfig

    top = gdstk.Cell(f"tm4-array-{arrayname}-v{variant:d}")

    shuffler = np.arange(36)
    np.random.seed(42)
    np.random.shuffle(shuffler)

    freqs = list(resonators.keys())
    freqs = np.array(freqs)[shuffler].reshape((6, 6))
 
    COLUMN_PAD = 444
    STUB_HEIGHT = 444
    flstub = feedlineconfig().draw(STUB_HEIGHT, ports=([], []), cellcache={})
    flstub.name = f"flstub-v{variant:d}"
    rects = [
        gdstk.rectangle((feedlineconfig().width_half, 0), (444, STUB_HEIGHT)),
        gdstk.rectangle((-feedlineconfig().width_half, 0), (-444, STUB_HEIGHT)),
    ]
    crosses = [
        gdstk.cross(b.focus_point, 32, 4),
        gdstk.cross((-b.focus_point[0], b.focus_point[1]), 32, 4),
        gdstk.cross((+b.focus_point[0], b.focus_point[1] + 222), 32, 4),
        gdstk.cross((-b.focus_point[0], b.focus_point[1] + 222), 32, 4),
    ]
    flstub.add(*gdstk.boolean(rects, crosses, "not", 0.0001, *b.box_layer))

    lib.add(flstub)

    ROWS = 6
    COLS = 6
    text = []
    text_origin = (222 * -12, 222 * -10)
    for i, x in enumerate(range(-COLS // 4 + 1, COLS // 4 + 1)):
        for j, y in enumerate(range(-ROWS // 2, ROWS // 2)):
            left = b.draw(**(resonators[freqs[i * 2][j]]), cellcache={})
            right = b.draw(**(resonators[freqs[i * 2 + 1][j]]), cellcache={})
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
        top.add(*gdstk.boolean(rect, crosses, "not", 0.0001, *b.box_layer))

    ARRAY_LEFT = -444 * COLS // 2 - (COLS - 3) // 2 * COLUMN_PAD
    ARRAY_RIGHT = +444 * COLS // 2 + (COLS - 3) // 2 * COLUMN_PAD
    CURVATURE_RADIUS = 200
    SPACING = 100

    wiring = gdstk.Cell(f"Wiring-v{variant:d}")
    paths = []
    for x in range(-1, 1, 2):
        p = gdstk.RobustPath(
            (2 * x * 444 + x * COLUMN_PAD, ARRAY_BOTTOM),
            [feedlineconfig().b, feedlineconfig.b],
            [
                feedlineconfig().a + feedlineconfig().b / 2,
                -feedlineconfig().a - feedlineconfig().b / 2,
            ],
        )
        p.arc(CURVATURE_RADIUS, -np.pi, -np.pi / 2)
        p.horizontal(444 * 2 + COLUMN_PAD - CURVATURE_RADIUS * 2, relative=True)
        p.arc(CURVATURE_RADIUS, -np.pi / 2, 0)
        paths.append(p)
    p = gdstk.RobustPath(
        (0, ARRAY_BOTTOM - CURVATURE_RADIUS * 2 - SPACING),
        [feedlineconfig().b, feedlineconfig.b],
        [
            feedlineconfig().a + feedlineconfig().b / 2,
            -feedlineconfig().a - feedlineconfig().b / 2,
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
    wiring.add(*gdstk.boolean(rect, paths, "not", 0.0001, *b.box_layer))

    capping = gdstk.Cell(f"Bond Cap-v{variant:d}")
    m = flmult
    f = feedlineconfig()
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
        *b.box_layer,
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
    capping.add(*gdstk.boolean(rect, outline, "not", 0.0001, *b.box_layer))

    top.add(gdstk.Reference(wiring))
    top.add(gdstk.Reference(wiring, rotation=np.pi, origin=(0, -b.focus_point[1] * 2)))
    top.add(gdstk.Reference(capping))
    top.add(gdstk.Reference(capping, rotation=np.pi))

    prect = gdstk.rectangle((ARRAY_LEFT, -5600 // 2 + CAPPING_HEIGHT), (ARRAY_RIGHT, ARRAY_WIRED_BOTTOM))
    p = gdstk.RobustPath(
        (0, -5600 // 2),
        [feedlineconfig().b, feedlineconfig.b],
        [
            feedlineconfig().a + feedlineconfig().b / 2,
            -feedlineconfig().a - feedlineconfig().b / 2,
        ],
    )
    p.vertical(ARRAY_WIRED_BOTTOM)
    top.add(*gdstk.boolean(prect, p, "not", 0.0001, *b.box_layer))

    prect = gdstk.rectangle((ARRAY_LEFT, +5600 // 2 - CAPPING_HEIGHT), (ARRAY_RIGHT, ARRAY_WIRED_TOP))
    p = gdstk.RobustPath(
        (0, 5600 // 2),
        [feedlineconfig().b, feedlineconfig.b],
        [
            feedlineconfig().a + feedlineconfig().b / 2,
            -feedlineconfig().a - feedlineconfig().b / 2,
        ],
    )
    p.vertical(ARRAY_WIRED_TOP)
    top.add(*gdstk.boolean(prect, p, "not", 0.0001, *b.box_layer))

    via = viawire()
    xovers = gdstk.Cell(f"crossovers-v{variant:d}")
    XOVER_LENGTH = 2 * (feedlineconfig().a + feedlineconfig().b + via.landing_length + 1)
    XOVER_LENGTH_COUPLER = 56
    for y in range(-ROWS // 2, ROWS // 2):
        yposh = y * 222 + y * STUB_HEIGHT - b.focus_point[1] + 222
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
            crosses.extend(Vernier(lower_layer=b.box_layer).draw_polys((x + 111, y), 0.0))
            crosses.extend(Vernier(lower_layer=b.box_layer).draw_polys((x - 111, y), np.pi))
            crosses.extend(Vernier(lower_layer=b.box_layer).draw_polys((x, y + 111), np.pi / 2))
            crosses.extend(Vernier(lower_layer=b.box_layer).draw_polys((x, y - 111), -np.pi / 2))
            crosses.append(gdstk.cross((x, y), 75, 20, *b.box_layer))
            crosses.append(gdstk.cross((x, y), 72, 18, *MLA_MARK))

    crosses_atanb = [
        c for c in crosses if c.layer == b.box_layer.gds_layer[0] and c.datatype == b.box_layer.gds_layer[1]
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
        top.add(gdstk.cross((x, y), 100, 20, *b.box_layer))
        top.add(gdstk.cross((x, y), 100, 20, *b.inductor.leg_layer))
        top.add(gdstk.rectangle((x - 50, y - 50), (x + 50, y + 50), *HF_CONTACT))

    for rot in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
        vs = []
        for i, pair in enumerate(
            [
                (b.box_layer, b.inductor.leg_layer),
                (b.box_layer, HF_CONTACT),
                (b.box_layer, HF_CONTACT_LIFTOFF),
                (b.box_layer, ASI),
                (b.box_layer, ASI_EP),
            ]
        ):
            vs.extend(Vernier(lower_layer=pair[0], upper_layer=pair[1]).draw_polys((-AP + 100 + 50 * i, -AP)))
        top.add(*[v.rotate(rot) for v in vs])
        top.add(*[v.copy().mirror((-1, -1), (1, 1)) for v in vs])

    top.add(*gdstk.boolean(rects, crosses_atanb + text, "not", 0.0001, *b.box_layer))
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
            ],
            *b.box_layer,
        )
    )
    lib.add(xovers)
    lib.add(capping)
    lib.add(wiring)
    lib.add(top)
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
        4.06: {
            "coupler_tunable": 0.6825396825396826,
            "capacitor_tunable": 0.9133858267716535,
        },
        4.12: {
            "coupler_tunable": 0.6507936507936507,
            "capacitor_tunable": 0.8818897637795275,
        },
        4.18: {
            "coupler_tunable": 0.6190476190476191,
            "capacitor_tunable": 0.84251968503937,
        },
        4.24: {
            "coupler_tunable": 0.5873015873015872,
            "capacitor_tunable": 0.8110236220472441,
        },
        4.3: {
            "coupler_tunable": 0.5396825396825397,
            "capacitor_tunable": 0.7874015748031495,
        },
        5.0: {
            "coupler_tunable": 0.5396825396825397,
            "capacitor_tunable": 0.49606299212598426,
        },
        5.1: {
            "coupler_tunable": 0.4603174603174603,
            "capacitor_tunable": 0.4645669291338583,
        },
        5.2: {
            "coupler_tunable": 0.3968253968253968,
            "capacitor_tunable": 0.4251968503937008,
        },
        5.3: {
            "coupler_tunable": 0.3492063492063492,
            "capacitor_tunable": 0.39370078740157477,
        },
        5.4: {
            "coupler_tunable": 0.2857142857142857,
            "capacitor_tunable": 0.36220472440944884,
        },
        5.5: {
            "coupler_tunable": 0.2222222222222222,
            "capacitor_tunable": 0.3307086614173228,
        },
        5.6: {
            "coupler_tunable": 0.15873015873015872,
            "capacitor_tunable": 0.2992125984251969,
        },
        5.7: {
            "coupler_tunable": 0.047619047619047616,
            "capacitor_tunable": 0.26771653543307083,
        },
        6.0: {
            "coupler_tunable": 0.0,
            "capacitor_tunable": 0.25984251968503935,
        },
        6.11: {
            "coupler_tunable": 0.015873015873015872,
            "capacitor_tunable": 0.18110236220472442,
        },
        6.22: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.1653543307086614,
        },
        6.33: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.14960629921259844,
        },
        6.44: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.13385826771653542,
        },
        6.55: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.12598425196850394,
        },
        6.66: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.11023622047244094,
        },
        6.7700000000000005: {
            "coupler_tunable": 0.047619047619047616,
            "capacitor_tunable": 0.09448818897637795,
        },
        6.88: {
            "coupler_tunable": 0.047619047619047616,
            "capacitor_tunable": 0.08661417322834646,
        },
        6.99: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.07086614173228346,
        },
        7.4: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.03937007874015748,
        },
        7.45: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.5: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.550000000000001: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.6000000000000005: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.65: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.7: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.015748031496062992,
        },
        7.75: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.015748031496062992,
        },
        7.8: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.007874015748031496,
        },
        7.8500000000000005: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.007874015748031496,
        },
        7.9: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.007874015748031496,
        },
        7.95: {
            "coupler_tunable": 0.031746031746031744,
            "capacitor_tunable": 0.0,
        },
    }

    lib = gdstk.Library("ue2-ucsb-array")

    for i in range(4):
        b = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            UEFeedlineConfig(),
        )
        make_array_variant(lib, i, resonators, b, UEFeedlineConfig, ViaWire, "ucsb-8ph")
    lib.write_gds("ue2-ucsb-array.gds")
