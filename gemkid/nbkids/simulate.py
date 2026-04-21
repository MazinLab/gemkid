import gdstk

from dataclasses import dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimEmit, SimRun, SimCorner, SimOptimize

from .layers import (
    NB_SONNET,
    NB_VAR_SONNET,
    NB_SONNET_3D,
    NB_VAR_SONNET_3D,
)
from .layers import drawing_to_sonnet, drawing_to_sonnet_3d


@dataclass(frozen=True, eq=True)
class UE2TestBench(simulate.LeftFeedlineTestbench):
    delta: float = 0.5

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [NB_SONNET, NB_VAR_SONNET]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet(super()._cell)
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
        return "UE2" + super()._filename

    @property
    def _portlevel(self):
        return 0


@dataclass(frozen=True, eq=True)
class UE23DTestBench(simulate.LeftFeedlineTestbench):
    delta: float = 0.5

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _filename(self):
        return "UE23D" + super()._filename

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [NB_SONNET_3D, NB_VAR_SONNET_3D]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet_3d(super()._cell)
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


class UE2CMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        if "3d" in ns.__dict__.keys():
            return UE23DTestBench(cell, geometry.feedline)
        return UE2TestBench(cell, geometry.feedline)


if __name__ == "__main__":
    from .geometry import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE2 Simulation Tool")
    runner = UE2CMD(
        "ue2",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        NB_VAR_SONNET,
        [
            SimEmit(),
            SimRun(),
            SimBulkEstimate(NB_SONNET, NB_VAR_SONNET),
            SimCorner(),
            SimOptimize({"coupler_tunable": 64, "capacitor_tunable": 128}, NB_SONNET, NB_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
