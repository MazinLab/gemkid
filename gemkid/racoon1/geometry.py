#!/usr/bin/env python3
import gdstk

from dataclasses import dataclass
from typing import Optional

from ..ue1.layers import HFTA, ATA_NB, HF_CONTACT
from ..layers import DrawingLayer

from ..ue2 import geometry as ue2g, array

@dataclass(eq=True, frozen=True)
class UEFeedlineConfig(ue2g.UEFeedlineConfig):
    a: float = 5.0
    b: float = 3.5
    c: float = 9.5
    feed_layer: tuple[int, int] | DrawingLayer = ATA_NB
    ground_layer: tuple[int, int] | DrawingLayer = ATA_NB


@dataclass(eq=True, frozen=True)
class ViaWire(ue2g.ViaWire):
    bridge_width: float = 8
    bridge_layer: tuple[int, int] | DrawingLayer = HFTA
    bridge_land: bool = True
    landing_width: float = 8
    landing_length: float = 18
    landing_layer: tuple[int, int] | DrawingLayer = HFTA
    via_width: float = 5
    via_length: float = 15
    via_layer: tuple[int, int] | DrawingLayer = HF_CONTACT
    liftoff_width: float = 5
    asi_width: float = 6


@dataclass(eq=True, frozen=True)
class InductorConfig(ue2g.InductorConfig):
    legs: int = 4
    leg_gap: float = 0.5
    leg_length: float = 10.0
    leg_width: float = 4.0
    leg_landing: float = 0
    leg_layer: DrawingLayer = HFTA
    wiring_width: float = 4.0
    wiring_gap: float = 0.5
    wiring_layer: DrawingLayer = HFTA
    wiring_extra: float = 8.0
    wiring_extra_height: float = 10.0
    via_over: Optional[float] = None
    via_width: float = 5.0
    via_inset: float = 5
    via_gap: float = 3
    via_layer: DrawingLayer = HF_CONTACT
    litho_vias: Optional[int] = 0
    asi_layer = None
    asi_ep_layer = None
    liftoff_layer = None


@dataclass(eq=True, frozen=True)
class CapacitorConfig(ue2g.CapacitorConfig):
    legs: int = 74
    leg_gap: float = 1
    leg_length: tuple[float, float] = (212 - 33 - 6 - 6, 112 - 13)
    leg_width: float = 1
    leg_landing: float = 0.0
    leg_layer: DrawingLayer = HFTA
    wiring_width: float = 10.0
    wiring_layer: DrawingLayer = HFTA
    extra_height: float = 0.0


@dataclass(eq=True, frozen=True)
class BoxConfig(ue2g.BoxConfig):
    inductor: Optional[InductorConfig]
    capacitor: Optional[CapacitorConfig]
    feedline: UEFeedlineConfig = UEFeedlineConfig()
    coupler_width: float = 2.0
    coupler_gap: float = 4.0
    coupler_fill: bool = False
    coupler_layer: DrawingLayer = ATA_NB
    coupler_via: Optional[ue2g.mecstyle.ViaWire] = (
        None  # mecstyle.ViaWire(2.0, HF, False, 2.0, 2.0, ATA_NB, 2.0, 2.0, HF_CONTACT)
    )
    box_width: float = 2.0
    box_gap: float = 1.0
    box_layer: DrawingLayer = ATA_NB
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
        (0, 2),
        (5, 2),
        (10, 2),
        (21.5, 1),
    ]

    lib = gdstk.Library("r1")
    b = BoxConfig(InductorConfig(), CapacitorConfig(), UEFeedlineConfig())
    b00 = b.draw(
        coupler_tunable=0.0, capacitor_tunable=0.0, flatten=True, cellcache={}
    ).copy("rone00")
    b01 = b.draw(
        coupler_tunable=0.0, capacitor_tunable=1.0, flatten=True, cellcache={}
    ).copy("rone01")
    b10 = b.draw(
        coupler_tunable=1.0, capacitor_tunable=0.0, flatten=True, cellcache={}
    ).copy("rone10")
    b11 = b.draw(
        coupler_tunable=1.0, capacitor_tunable=1.0, flatten=True, cellcache={}
    ).copy("rone11")
    lib.add(b00, b01, b10, b11)
    lib.write_gds("racoon1-ll.gds")
    import sys
    sys.exit(0)

    resonators_tm = {
        4.7: {'capacitor_tunable': 0.8785797683223091,
          'coupler_tunable': 0.7853595734408289},
         4.75: {'capacitor_tunable': 0.8538423317734765,
          'coupler_tunable': 0.753930249811506},
         4.8: {'capacitor_tunable': 0.827636995610809,
          'coupler_tunable': 0.7237144027180294},
         4.85: {'capacitor_tunable': 0.9101123595505618,
          'coupler_tunable': 0.8253012048192772},
         4.9: {'capacitor_tunable': 0.7811214183479828,
          'coupler_tunable': 0.6701082171972915},
         4.95: {'capacitor_tunable': 0.7579921073376964,
          'coupler_tunable': 0.6478077360823395},
         5.0: {'capacitor_tunable': 0.7359964826072745,
          'coupler_tunable': 0.6219534557402806},
         6.1: {'capacitor_tunable': 0.3627344955862412,
          'coupler_tunable': 0.2588709694581718},
         6.2: {'capacitor_tunable': 0.33646437775522514,
          'coupler_tunable': 0.235430883763639},
         6.3: {'capacitor_tunable': 0.31133098076351984,
          'coupler_tunable': 0.21221627722422443},
         6.4: {'capacitor_tunable': 0.28746191876459765,
          'coupler_tunable': 0.18823970852655816},
         7.5: {'capacitor_tunable': 0.10474007888472624,
          'coupler_tunable': 0.08753274785087363},
         7.625: {'capacitor_tunable': 0.090552253757031,
          'coupler_tunable': 0.08574468059300579},
         7.75: {'capacitor_tunable': 0.0763728688671114,
          'coupler_tunable': 0.0826005975215284},
         7.875: {'capacitor_tunable': 0.06313837733183439,
          'coupler_tunable': 0.08092108132754271},
         8.0: {'capacitor_tunable': 0.05159835719223678,
          'coupler_tunable': 0.07814335486313163}
    }

    for g, igs in enumerate([
        {"leg_gap": 0.75, "via_gap": 1.75, "wiring_gap": 1.75, "asi_ep_layer": None, "asi_layer": None, "liftoff_layer": None},
        {"leg_gap": 1.00, "via_gap": 2.00, "wiring_gap": 2.00, "asi_ep_layer": None, "asi_layer": None, "liftoff_layer": None},
        {"leg_gap": 1.50, "via_gap": 2.50, "wiring_gap": 2.50, "asi_ep_layer": None, "asi_layer": None, "liftoff_layer": None},
        {"leg_gap": 1.50, "via_gap": 2.50, "wiring_gap": 2.50, "asi_ep_layer": None, "asi_layer": None, "liftoff_layer": HF_CONTACT},
        {"leg_gap": 2.50, "via_gap": 3.50, "wiring_gap": 3.50, "asi_ep_layer": None, "asi_layer": None, "liftoff_layer": None},
    ]):
        for i in range(4):
            text = f"leg_gap: {igs['leg_gap']:1.2f} via_inset: {variants[i][0]:02.1f}"
            if g == 3:
                text += " bar"
            if i == 3 and g == 3:
                continue
            if i == 3:
                igs["via_gap"] = 0.0
            b = BoxConfig(
                InductorConfig(via_inset=variants[i][0], litho_vias=variants[i][1], **igs),
                CapacitorConfig(),
                UEFeedlineConfig(),
                box_width_extra=10.5 if g != 4 else 0
            )
            bhqc = BoxConfig(
                InductorConfig(via_inset=variants[i][0], litho_vias=variants[i][1], **igs),
                CapacitorConfig(),
                UEFeedlineConfig(),
                double_coupler=False,
                extended_coupler_pullback=True,
                box_width_extra=10.5
            )
            barr = BoxConfig(
                InductorConfig(via_inset=variants[i][0], litho_vias=variants[i][1], **igs),
                CapacitorConfig(),
                UEFeedlineConfig(),
                box_width_extra=10.5,
            )
            big_array = array.ArrayConfig()
            mini_array = array.ArrayConfig(
                feedlines=1,
                dimensions=(2, 8),
                outer_width = 6000,
                outer_height = 6000,
                inner_width = 5400,
                inner_height = 5400,
                padring = 200
            )
            geometry.make_tm_variant(lib, i, resonators_tm, b, bhqc, UEFeedlineConfig, ViaWire, f"Racoon1 20pH {g}\n{text}", variants, f"r1-18ph-g{g}")
            # if g == 1 and (i == 3 or i == 1):
            #     array.make_array_variant(lib, i, resonators_tm, barr, UEFeedlineConfig, ViaWire, f"rq-20ph-g{g}")
            # array.make_array_variant(lib, i, resonators_array, b, UEFeedlineConfig, ViaWire, "ll-ma-20ph", mini_array)

    lib.write_gds("racoon1-ll.gds")
