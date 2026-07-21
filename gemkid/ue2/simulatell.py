import gdstk

from dataclasses import dataclass

from ..ue1.layers import (
    TIN_LL_SONNET,
    HF_LL_SONNET,
    HF_VAR_SONNET,
    TI_GOLD_SONNET,
    TIN_LL_SONNET_3D,
    HF_LL_SONNET_3D,
    HF_VAR_SONNET_3D,
    HF_VIA_SONNET_3D,
    TI_GOLD_SONNET_3D,
)
from . import simulate

@dataclass(frozen=True, eq=True)
class UE2LLTestBench(simulate.UE2TestBench):

    @property
    def _layer_stack(self) -> list[simulate.simulate.SonnetLayer]:
        return [TIN_LL_SONNET, HF_LL_SONNET, HF_VAR_SONNET, TI_GOLD_SONNET]

    @property
    def _filename(self):
        return "LL-" + super()._filename

@dataclass(frozen=True, eq=True)
class UE2LL3DTestBench(simulate.UE23DTestBench):
    @property
    def _layer_stack(self) -> list[simulate.simulate.SonnetLayer]:
        return [TIN_LL_SONNET_3D, HF_LL_SONNET_3D, HF_VAR_SONNET_3D, HF_VIA_SONNET_3D, TI_GOLD_SONNET_3D]

    @property
    def _filename(self):
        return "LL-" + super()._filename

class UE2LLCMD(simulate.GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.simulate.TestbenchABC:
        if "3d" in ns.__dict__.keys():
            return UE2LL3DTestBench(cell, geometry.feedline)
        return UE2LLTestBench(cell, geometry.feedline)

if __name__ == "__main__":
    from .geometryll import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE2 LL Simulation Tool")
    runner = UE2LLCMD(
        "ue2",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        HF_VAR_SONNET,
        [
            simulate.SimEmit(),
            simulate.SimRun(),
            simulate.SimBulkEstimate(HF_LL_SONNET, HF_VAR_SONNET),
            simulate.SimCorner(),
            simulate.SimOptimize({"coupler_tunable": 167, "capacitor_tunable": 268}, HF_LL_SONNET, HF_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
