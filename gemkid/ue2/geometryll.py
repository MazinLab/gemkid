#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..ue1.layers import HF_LL, TIN_LL, HF_CONTACT
from ..layers import DrawingLayer

from . import geometry
from . import array


@dataclass(eq=True, frozen=True)
class UEFeedlineConfig(geometry.UEFeedlineConfig):
    a: float = 4.5 + 2.25
    b: float = 4 - 2.25
    c: float = 9.5
    feed_layer: tuple[int, int] | DrawingLayer = TIN_LL
    ground_layer: tuple[int, int] | DrawingLayer = TIN_LL


@dataclass(eq=True, frozen=True)
class ViaWire(geometry.ViaWire):
    bridge_width: float = 4
    bridge_layer: tuple[int, int] | DrawingLayer = HF_LL
    bridge_land: bool = True
    landing_width: float = 4
    landing_length: float = 18
    landing_layer: tuple[int, int] | DrawingLayer = TIN_LL
    via_width: float = 3
    via_length: float = 15
    via_layer: tuple[int, int] | DrawingLayer = HF_CONTACT
    liftoff_width: float = 5
    asi_width: float = 6


@dataclass(eq=True, frozen=True)
class InductorConfig(geometry.InductorConfig):
    legs: int = 4
    leg_gap: float = 0.75
    leg_length: float = 40.0
    leg_width: float = 4.0
    leg_landing: float = 8
    leg_layer: DrawingLayer = HF_LL
    wiring_width: float = 3.0
    wiring_gap: float = 1.75
    wiring_layer: DrawingLayer = TIN_LL
    wiring_extra: float = 8.0
    wiring_extra_height: float = 10.0
    via_over: Optional[float] = None
    via_width: float = 5.0
    via_inset: float = 5
    via_gap: float = 3
    via_layer: DrawingLayer = HF_CONTACT
    litho_vias: Optional[int] = 2


@dataclass(eq=True, frozen=True)
class CapacitorConfig(geometry.CapacitorConfig):
    legs: int = 66
    leg_gap: float = 1
    leg_length: tuple[float, float] = (212-33, 112)
    leg_width: float = 1
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = TIN_LL
    wiring_width: float = 4.0
    wiring_layer: DrawingLayer = TIN_LL
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(geometry.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: UEFeedlineConfig = UEFeedlineConfig()
    coupler_width: float = 2.0
    coupler_gap: float = 4.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = TIN_LL
    coupler_via: Optional[geometry.mecstyle.ViaWire] = (
        None  # mecstyle.ViaWire(2.0, HF, False, 2.0, 2.0, ATA_NB, 2.0, 2.0, HF_CONTACT)
    )
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = TIN_LL
    width: float = 222
    height: float = 222
    extended_coupler_pullback: bool = False
    double_coupler: bool = True
    box_width_extra: float = 0.0

    def draw(self, coupler_tunable: float = 1, capacitor_tunable: float = 1, variation_layer=None, flatten=True, cellcache=...):
        c = super().draw(coupler_tunable, capacitor_tunable, variation_layer, flatten, cellcache)
        if type(c) is list:
            c[0].add(gdstk.rectangle((self.feedline.width_half, self.box_width), (self.width, self.box_width + self.box_width_extra), *self.box_layer))
        else:
            c.add(gdstk.rectangle((self.feedline.width_half, self.box_width), (self.width, self.box_width + self.box_width_extra), *self.box_layer))
        return c


if __name__ == "__main__":
    import numpy as np

    variants = [
        (3, 0),
        (3, 5),
        (3, 10),
        (4.75, 21.5),
    ]

    lib = gdstk.Library("ue2-ll")
    resonators_tm = {
        4.0: {"coupler_tunable": 0.9523809523809523, "capacitor_tunable": 0.5275590551181102},
        4.05: {"coupler_tunable": 0.9047619047619047, "capacitor_tunable": 0.5118110236220472},
        4.1: {"coupler_tunable": 0.873015873015873, "capacitor_tunable": 0.4881889763779528},
        4.15: {"coupler_tunable": 0.8253968253968254, "capacitor_tunable": 0.47244094488188976},
        4.2: {"coupler_tunable": 0.7936507936507936, "capacitor_tunable": 0.45669291338582674},
        4.25: {"coupler_tunable": 0.7619047619047619, "capacitor_tunable": 0.4409448818897638},
        4.3: {"coupler_tunable": 0.7142857142857142, "capacitor_tunable": 0.4251968503937008},
        6.1: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.11811023622047244},
        6.2: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.11023622047244094},
        6.3: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.10236220472440945},
        6.4: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.09448818897637795},
        7.5: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.031496062992125984},
        7.625: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.023622047244094488},
        7.75: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.023622047244094488},
        7.875: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.015748031496062992},
        8.0: {"coupler_tunable": 0.06349206349206349, "capacitor_tunable": 0.015748031496062992},
    }

    resonators_array = {
        4.0: {"coupler_tunable": 0.9523809523809523, "capacitor_tunable": 0.5275590551181102},
        4.06: {"coupler_tunable": 0.9047619047619047, "capacitor_tunable": 0.5039370078740157},
        4.12: {"coupler_tunable": 0.8571428571428571, "capacitor_tunable": 0.48031496062992124},
        4.18: {"coupler_tunable": 0.8095238095238095, "capacitor_tunable": 0.4645669291338583},
        4.24: {"coupler_tunable": 0.7619047619047619, "capacitor_tunable": 0.44881889763779526},
        4.3: {"coupler_tunable": 0.7142857142857142, "capacitor_tunable": 0.4251968503937008},
        5.0: {"coupler_tunable": 0.2857142857142857, "capacitor_tunable": 0.25196850393700787},
        5.1: {"coupler_tunable": 0.20634920634920634, "capacitor_tunable": 0.23622047244094488},
        5.2: {"coupler_tunable": 0.1746031746031746, "capacitor_tunable": 0.2204724409448819},
        5.3: {"coupler_tunable": 0.1746031746031746, "capacitor_tunable": 0.2047244094488189},
        5.4: {"coupler_tunable": 0.15873015873015872, "capacitor_tunable": 0.1889763779527559},
        5.5: {"coupler_tunable": 0.15873015873015872, "capacitor_tunable": 0.1732283464566929},
        5.6: {"coupler_tunable": 0.14285714285714285, "capacitor_tunable": 0.1653543307086614},
        5.7: {"coupler_tunable": 0.14285714285714285, "capacitor_tunable": 0.15748031496062992},
        6.0: {"coupler_tunable": 0.12698412698412698, "capacitor_tunable": 0.12598425196850394},
        6.11: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.11811023622047244},
        6.22: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.10236220472440945},
        6.33: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.09448818897637795},
        6.44: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.08661417322834646},
        6.55: {"coupler_tunable": 0.1111111111111111, "capacitor_tunable": 0.07874015748031496},
        6.66: {"coupler_tunable": 0.09523809523809523, "capacitor_tunable": 0.07086614173228346},
        6.7700000000000005: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.07086614173228346,
        },
        6.88: {"coupler_tunable": 0.09523809523809523, "capacitor_tunable": 0.06299212598425197},
        6.99: {"coupler_tunable": 0.09523809523809523, "capacitor_tunable": 0.05511811023622047},
        7.4: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.031496062992125984},
        7.45: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.031496062992125984},
        7.5: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.031496062992125984},
        7.550000000000001: {
            "coupler_tunable": 0.07936507936507936,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.6000000000000005: {
            "coupler_tunable": 0.07936507936507936,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.65: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.023622047244094488},
        7.7: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.023622047244094488},
        7.75: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.023622047244094488},
        7.8: {"coupler_tunable": 0.07936507936507936, "capacitor_tunable": 0.015748031496062992},
        7.8500000000000005: {
            "coupler_tunable": 0.07936507936507936,
            "capacitor_tunable": 0.015748031496062992,
        },
        7.9: {"coupler_tunable": 0.06349206349206349, "capacitor_tunable": 0.015748031496062992},
        7.95: {"coupler_tunable": 0.06349206349206349, "capacitor_tunable": 0.015748031496062992},
    }

    for i in range(4):
        b = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            UEFeedlineConfig(),
            box_width_extra=10.5
        )

        bhqc = BoxConfig(
            InductorConfig(via_gap=variants[i][0], via_inset=variants[i][1]),
            CapacitorConfig(),
            UEFeedlineConfig(),
            double_coupler=False,
            extended_coupler_pullback=True,
            box_width_extra=10.5
        )
        geometry.make_tm_variant(
            lib,
            i,
            resonators_tm,
            b,
            bhqc,
            UEFeedlineConfig,
            ViaWire,
            "UE2 LL 20pH",
            variants,
            "ll-20ph",
        )
        array.make_array_variant(lib, i, resonators_array, b, UEFeedlineConfig, ViaWire, "ll-20ph")

    lib.write_gds("ue2-ll.gds")
