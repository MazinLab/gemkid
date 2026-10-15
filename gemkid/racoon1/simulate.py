import gdstk

from dataclasses import dataclass

from ..ue1.layers import (
    ATA_NB_SONNET,
    HFTA_SONNET,
    HF_VAR_SONNET,
    TI_GOLD_SONNET,
    ATA_NB_SONNET_3D,
    HFTA_SONNET_3D,
    HF_VAR_SONNET_3D,
    HF_VIA_SONNET_3D,
    TI_GOLD_SONNET_3D,
)
from ..ue2 import simulate

@dataclass(frozen=True, eq=True)
class RacoonOneTestBench(simulate.UE2TestBench):

    @property
    def _layer_stack(self) -> list[simulate.simulate.SonnetLayer]:
        return [ATA_NB_SONNET, HFTA_SONNET, HF_VAR_SONNET, TI_GOLD_SONNET]

    @property
    def _filename(self):
        return "R1-" + super()._filename

@dataclass(frozen=True, eq=True)
class RacoonOne3DTestBench(simulate.UE23DTestBench):
    @property
    def _layer_stack(self) -> list[simulate.simulate.SonnetLayer]:
        return [ATA_NB_SONNET_3D, HFTA_SONNET, HF_VAR_SONNET_3D, HF_VIA_SONNET_3D, TI_GOLD_SONNET_3D]

    @property
    def _filename(self):
        return "R1-" + super()._filename

class RacoonOneCMD(simulate.GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.simulate.TestbenchABC:
        if "3d" in ns.__dict__.keys():
            return RacoonOne3DTestBench(cell, geometry.feedline, delta=0.5)
        return RacoonOneTestBench(cell, geometry.feedline, delta=0.5)

if __name__ == "__main__":
    from .geometry import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE2 LL Simulation Tool")
    runner = RacoonOneCMD(
        "r1",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        HF_VAR_SONNET,
        [
            simulate.SimEmit(),
            simulate.SimRun(),
            simulate.SimBulkEstimate(HFTA_SONNET, HF_VAR_SONNET),
            simulate.SimCorner(),
            simulate.SimOptimize({"coupler_tunable": 167, "capacitor_tunable": 268}, HFTA_SONNET, HF_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
