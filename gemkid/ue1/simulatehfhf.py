import gdstk

from dataclasses import dataclass, is_dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimEmit, SimRun, SimCorner, SimOptimize

from .layers import (
    ATA_NB_SONNET,
    HF_SONNET,
    HF_VAR_SONNET,
    TI_GOLD_SONNET,
    ATA_NB_SONNET_3D,
    HF_SONNET_3D,
    HF_VAR_SONNET_3D,
    HF_VIA_SONNET_3D,
    TI_GOLD_SONNET_3D,
)
from .layers import drawing_to_sonnet, drawing_to_sonnet_3d


@dataclass(frozen=True, eq=True)
class UE1Testbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.5
    backside_gold: bool = False

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [ATA_NB_SONNET, HF_SONNET, HF_VAR_SONNET, TI_GOLD_SONNET]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet(super()._cell)
        if self.backside_gold:
            width = c.bounding_box()[1][0] - c.bounding_box()[0][0]
            height = c.bounding_box()[1][1] - c.bounding_box()[0][1]
            c.add(gdstk.rectangle((self.padding, 0), (width - self.padding, height), *TI_GOLD_SONNET))
        return c

    @property
    def _dielectric_stack(self) -> list[simulate.DielectricLayer]:
        return [
            simulate.DielectricLayer("airtop", 100000.0, 0),
            simulate.DielectricLayer("cplanesaph", 750.0, 1, (9.3, 11.5)),
            simulate.DielectricLayer("airbot", 100000.0, 2),
        ]

    @property
    def _filename(self):
        return "UE1" + super()._filename

    @property
    def _portlevel(self):
        return 0


@dataclass(frozen=True, eq=True)
class UE13DTestBench(simulate.LeftFeedlineTestbench):
    delta: float = 0.5
    backside_gold: bool = False

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _filename(self):
        return "3D" + super()._filename

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [ATA_NB_SONNET_3D, HF_SONNET_3D, HF_VAR_SONNET_3D, HF_VIA_SONNET_3D, TI_GOLD_SONNET_3D]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet_3d(super()._cell)
        if self.backside_gold:
            width = c.bounding_box()[1][0] - c.bounding_box()[0][0]
            height = c.bounding_box()[1][1] - c.bounding_box()[0][1]
            c.add(gdstk.rectangle((self.padding, 0), (width - self.padding, height), *TI_GOLD_SONNET_3D))
        return c

    @property
    def _dielectric_stack(self) -> list[simulate.DielectricLayer]:
        return [
            simulate.DielectricLayer("airtop", 100000.0, 0),
            simulate.DielectricLayer("airbridge", 0.700, 1),
            simulate.DielectricLayer("cplanesaph", 430.0, 2, (9.3, 11.5)),
            simulate.DielectricLayer("airbot", 100000.0, 3),
        ]

    @property
    def _portlevel(self):
        return 1


class UE1CMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        if "3d" in ns.__dict__.keys():
            return UE13DTestBench(cell, geometry.feedline)
        return UE1Testbench(cell, geometry.feedline)


if __name__ == "__main__":
    from .geometryhfhf import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE1 Simulation Tool")
    runner = UE1CMD(
        "ue1",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        HF_VAR_SONNET,
        [
            SimEmit(),
            SimRun(),
            SimBulkEstimate(HF_SONNET, HF_VAR_SONNET),
            SimCorner(),
            SimOptimize({"coupler_tunable": 64, "capacitor_tunable": 128}, HF_SONNET, HF_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
