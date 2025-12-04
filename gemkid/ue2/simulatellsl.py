from dataclasses import dataclass

from ..ue1.layers import (
    HF_GP_SONNET,
    HF_LL_SONNET,
    HF_VAR_SONNET,
    TI_GOLD_SONNET,
    HF_GP_SONNET_3D,
    HF_LL_SONNET_3D,
    HF_VAR_SONNET_3D,
    HF_VIA_SONNET_3D,
    TI_GOLD_SONNET_3D,
)
from . import simulate

@dataclass(frozen=True, eq=True)
class UE2LLSLTestBench(simulate.UE2TestBench):

    @property
    def _layer_stack(self) -> list[simulate.simulate.SonnetLayer]:
        return [HF_GP_SONNET, HF_LL_SONNET, HF_VAR_SONNET, TI_GOLD_SONNET]

    @property
    def _filename(self):
        return "LLSL-" + super()._filename

@dataclass(frozen=True, eq=True)
class UE2LLSL3DTestBench(simulate.UE23DTestBench):
    @property
    def _layer_stack(self) -> list[simulate.simulate.SonnetLayer]:
        return [HF_GP_SONNET_3D, HF_LL_SONNET_3D, HF_VAR_SONNET_3D, HF_VIA_SONNET_3D, TI_GOLD_SONNET_3D]

    @property
    def _filename(self):
        return "LLSL-" + super()._filename

class UE2LLSLCMD(simulate.GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.simulate.TestbenchABC:
        if "3d" in ns.__dict__.keys():
            return UE2LLSL3DTestBench(cell, geometry.feedline)
        return UE2LLSLTestBench(cell, geometry.feedline)

if __name__ == "__main__":
    from .geometryllsl import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE2 LL Simulation Tool")
    runner = UE2LLSLCMD(
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
            simulate.SimOptimize({"coupler_tunable": 64, "capacitor_tunable": 128}, HF_LL_SONNET, HF_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
