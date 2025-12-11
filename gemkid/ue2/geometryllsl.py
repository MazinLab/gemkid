#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..ue1.layers import HF_LL, HF_GP_LL, HF_CONTACT
from ..layers import DrawingLayer

from . import geometry
from . import array


@dataclass(eq=True, frozen=True)
class UEFeedlineConfig(geometry.UEFeedlineConfig):
    a: float = 37
    b: float = 1
    c: float = 30
    feed_layer: tuple[int, int] | DrawingLayer = HF_GP_LL
    ground_layer: tuple[int, int] | DrawingLayer = HF_GP_LL


@dataclass(eq=True, frozen=True)
class ViaWire(geometry.ViaWire):
    bridge_width: float = 4
    bridge_layer: tuple[int, int] | DrawingLayer = HF_LL
    bridge_land: bool = True
    landing_width: float = 4
    landing_length: float = 18
    landing_layer: tuple[int, int] | DrawingLayer = HF_GP_LL
    via_width: float = 3
    via_length: float = 15
    via_layer: tuple[int, int] | DrawingLayer = HF_CONTACT
    liftoff_width: float = 5
    asi_width: float = 6


@dataclass(eq=True, frozen=True)
class InductorConfig(geometry.InductorConfig):
    legs: int = 4
    leg_gap: float = 2.0
    leg_length: float = 40.0
    leg_width: float = 4.0
    leg_landing: float = 8
    leg_layer: DrawingLayer = HF_LL
    wiring_width: float = 4.0
    wiring_gap: float = 2.0
    wiring_layer: DrawingLayer = HF_GP_LL
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
    legs: int = 40
    leg_gap: float = 2
    leg_length: tuple[float, float] = (350 - 24, 200 - 24)
    leg_width: float = 1
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = HF_GP_LL
    wiring_width: float = 16
    wiring_layer: DrawingLayer = HF_GP_LL
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(geometry.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: UEFeedlineConfig = UEFeedlineConfig(feed_layer=HF_GP_LL, ground_layer=HF_GP_LL)
    coupler_width: float = 2.0
    coupler_gap: float = 4.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = HF_GP_LL
    coupler_via: Optional[geometry.mecstyle.ViaWire] = (
        None  # mecstyle.ViaWire(2.0, HF, False, 2.0, 2.0, HF_GP_LL, 2.0, 2.0, HF_CONTACT)
    )
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = HF_GP_LL
    width: float = 444
    height: float = 222
    extended_coupler_pullback: bool = False
    double_coupler: bool = True


if __name__ == "__main__":
    variants = [
        (3, 0),
        (3, 5),
        (3, 10),
        (3, 21.5),
    ]

    lib = gdstk.Library("ue2-ll-sl")

    resonators_tm = {
        4.0: {
            "coupler_tunable": 0.5873015873015872,
            "capacitor_tunable": 0.6929133858267716,
        },
        4.05: {
            "coupler_tunable": 0.5555555555555556,
            "capacitor_tunable": 0.6692913385826772,
        },
        4.1: {
            "coupler_tunable": 0.5396825396825397,
            "capacitor_tunable": 0.6456692913385826,
        },
        4.15: {
            "coupler_tunable": 0.5238095238095237,
            "capacitor_tunable": 0.6220472440944882,
        },
        4.2: {
            "coupler_tunable": 0.49206349206349204,
            "capacitor_tunable": 0.6062992125984252,
        },
        4.25: {
            "coupler_tunable": 0.47619047619047616,
            "capacitor_tunable": 0.5826771653543307,
        },
        4.3: {
            "coupler_tunable": 0.4603174603174603,
            "capacitor_tunable": 0.5669291338582677,
        },
        6.1: {
            "coupler_tunable": 0.15873015873015872,
            "capacitor_tunable": 0.14173228346456693,
        },
        6.2: {
            "coupler_tunable": 0.14285714285714285,
            "capacitor_tunable": 0.12598425196850394,
        },
        6.3: {
            "coupler_tunable": 0.14285714285714285,
            "capacitor_tunable": 0.11811023622047244,
        },
        6.4: {
            "coupler_tunable": 0.14285714285714285,
            "capacitor_tunable": 0.11023622047244094,
        },
        7.5: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.625: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.75: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.875: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.015748031496062992,
        },
        # TODO: This one seems wrong, simulate it
        8.0: {
            "coupler_tunable": 0.1111111111111111,
            "capacitor_tunable": 0.07086614173228346,
        },
    }
    resonators_array = {
        4.0: {
            "coupler_tunable": 0.5873015873015872,
            "capacitor_tunable": 0.6929133858267716,
        },
        4.06: {
            "coupler_tunable": 0.5555555555555556,
            "capacitor_tunable": 0.6692913385826772,
        },
        4.12: {
            "coupler_tunable": 0.5396825396825397,
            "capacitor_tunable": 0.6377952755905512,
        },
        4.18: {
            "coupler_tunable": 0.5079365079365079,
            "capacitor_tunable": 0.6141732283464567,
        },
        4.24: {
            "coupler_tunable": 0.47619047619047616,
            "capacitor_tunable": 0.5905511811023622,
        },
        4.3: {
            "coupler_tunable": 0.4603174603174603,
            "capacitor_tunable": 0.5669291338582677,
        },
        5.0: {
            "coupler_tunable": 0.3333333333333333,
            "capacitor_tunable": 0.33858267716535434,
        },
        5.1: {
            "coupler_tunable": 0.31746031746031744,
            "capacitor_tunable": 0.31496062992125984,
        },
        5.2: {
            "coupler_tunable": 0.30158730158730157,
            "capacitor_tunable": 0.29133858267716534,
        },
        5.3: {
            "coupler_tunable": 0.2857142857142857,
            "capacitor_tunable": 0.2755905511811024,
        },
        5.4: {
            "coupler_tunable": 0.2698412698412698,
            "capacitor_tunable": 0.25196850393700787,
        },
        5.5: {
            "coupler_tunable": 0.23809523809523808,
            "capacitor_tunable": 0.22834645669291337,
        },
        5.6: {
            "coupler_tunable": 0.19047619047619047,
            "capacitor_tunable": 0.2125984251968504,
        },
        5.7: {
            "coupler_tunable": 0.19047619047619047,
            "capacitor_tunable": 0.19685039370078738,
        },
        6.0: {
            "coupler_tunable": 0.15873015873015872,
            "capacitor_tunable": 0.14960629921259844,
        },
        6.11: {
            "coupler_tunable": 0.14285714285714285,
            "capacitor_tunable": 0.14173228346456693,
        },
        6.22: {
            "coupler_tunable": 0.14285714285714285,
            "capacitor_tunable": 0.12598425196850394,
        },
        6.33: {
            "coupler_tunable": 0.14285714285714285,
            "capacitor_tunable": 0.11811023622047244,
        },
        6.44: {
            "coupler_tunable": 0.12698412698412698,
            "capacitor_tunable": 0.10236220472440945,
        },
        6.55: {
            "coupler_tunable": 0.12698412698412698,
            "capacitor_tunable": 0.09448818897637795,
        },
        6.66: {
            "coupler_tunable": 0.12698412698412698,
            "capacitor_tunable": 0.08661417322834646,
        },
        6.7700000000000005: {
            "coupler_tunable": 0.12698412698412698,
            "capacitor_tunable": 0.07874015748031496,
        },
        6.88: {
            "coupler_tunable": 0.1111111111111111,
            "capacitor_tunable": 0.07086614173228346,
        },
        6.99: {
            "coupler_tunable": 0.1111111111111111,
            "capacitor_tunable": 0.05511811023622047,
        },
        7.4: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.45: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.5: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.031496062992125984,
        },
        7.550000000000001: {
            "coupler_tunable": 0.12698412698412698,
            "capacitor_tunable": 0.08661417322834646,
        },
        7.6000000000000005: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.65: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.7: {
            "coupler_tunable": 0.23809523809523808,
            "capacitor_tunable": 0.23622047244094488,
        },
        7.75: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.023622047244094488,
        },
        7.8: {
            "coupler_tunable": 0.1111111111111111,
            "capacitor_tunable": 0.047244094488188976,
        },
        7.8500000000000005: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.015748031496062992,
        },
        7.9: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.015748031496062992,
        },
        7.95: {
            "coupler_tunable": 0.09523809523809523,
            "capacitor_tunable": 0.015748031496062992,
        },
    }

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
        geometry.make_tm_variant(
            lib,
            i,
            resonators_tm,
            b,
            bhqc,
            UEFeedlineConfig,
            ViaWire,
            "UE2 LLSL 20pH",
            variants,
            "ll-sl-20ph",
            5,
        )
        array.make_array_variant(
            lib, i, resonators_array, b, UEFeedlineConfig, ViaWire, "UE2 LLSL 20pH Array", "ll-sl-20ph", 4
        )

    lib.write_gds("ue2-ll-sl.gds")
