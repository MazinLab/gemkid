import gdstk

from dataclasses import dataclass, is_dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimCorner, SimEmit, SimOptimize, SimRun

from ..anvil.layers import NB_SONNET, NB_VAR_SONNET
from ..anvil.layers import drawing_to_sonnet


@dataclass(frozen=True, eq=True)
class ANVCPWTestbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25

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
            simulate.DielectricLayer("cplanesaph", 750.0, 1, 5.7, 1.0, 1e-4),
            simulate.DielectricLayer("airbot", 100000.0, 2),
        ]

    @property
    def _filename(self):
        return "ANVCPW" + super()._filename

    @property
    def _portlevel(self):
        return 0


class ANVCPWCMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        return ANVCPWTestbench(cell, geometry.feedline, 1.0, stub=10)


if __name__ == "__main__":
    from .geometry import CPWConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Beta 2P Simulation Tool")
    runner = ANVCPWCMD(
        "anvcpw",
        parser,
        CPWConfig,
        [],
        NB_VAR_SONNET,
        [
            SimEmit(),
            SimRun(),
            SimBulkEstimate(NB_SONNET, NB_VAR_SONNET),
            SimCorner(),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
