import gdstk

from dataclasses import dataclass, is_dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimCorner, SimEmit, SimOptimize, SimRun

from .layers import (
    NB_SONNET,
    BTA_SONNET,
    BTA_VAR_SONNET,
    TI_GOLD_SONNET,
)
from .layers import drawing_to_sonnet, drawing_to_sonnet_3d


@dataclass(frozen=True, eq=True)
class B2Testbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25
    backside_gold: bool = False

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [NB_SONNET, BTA_SONNET, BTA_VAR_SONNET, TI_GOLD_SONNET]

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
        return "B2" + super()._filename

    @property
    def _portlevel(self):
        return 0


class B2CMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        return B2Testbench(cell, geometry.feedline)


if __name__ == "__main__":
    from .geometry import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE1 Simulation Tool")
    runner = B2CMD(
        "b2",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        BTA_VAR_SONNET,
        [
            SimEmit(),
            SimRun(),
            SimBulkEstimate(BTA_SONNET, BTA_VAR_SONNET),
            SimCorner(),
            SimOptimize({"coupler_tunable": 64, "capacitor_tunable": 512}, BTA_SONNET, BTA_VAR_SONNET),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
