import gdstk

from dataclasses import dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimCorner, SimEmit, SimOptimize, SimRun

from .layers import NB_SONNET, NB_VAR_SONNET
from .layers import drawing_to_sonnet


@dataclass(frozen=True, eq=True)
class ANVTestbench(simulate.LeftFeedlineTestbench):
    delta: float = 1.0

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [NB_SONNET]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet(super()._cell)
        return c

    @property
    def _dielectric_stack(self) -> list[simulate.DielectricLayer]:
        return [
            simulate.DielectricLayer("airtop", 100000.0, 0),
            simulate.DielectricLayer("diamond", 750.0, 1, 5.7, 1.0, 1e-4),
            simulate.DielectricLayer("airbot", 100000.0, 2),
        ]

    @property
    def _filename(self):
        return "ANV" + super()._filename

    @property
    def _portlevel(self):
        return 0


class ANVCMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        return ANVTestbench(cell, geometry.feedline, stub=80, padding=2)


if __name__ == "__main__":
    from .geometry import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Beta 2 Simulation Tool")
    parser.add_argument("--threedee", action="store_true", default=False)
    runner = ANVCMD(
        "anv",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        NB_SONNET,
        [
            SimEmit(),
            SimRun(),
            SimBulkEstimate(NB_SONNET, NB_VAR_SONNET),
            SimCorner(),
            SimOptimize({"coupler_tunable": 64, "capacitor_tunable": 512}, NB_SONNET, NB_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
