import gdstk

from dataclasses import dataclass, is_dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimCorner, SimEmit, SimOptimize, SimRun

from ..beta2.layers import (
    NB_SONNET_3D,
    BTA_SONNET_3D,
    BTA_VAR_SONNET_3D,
    TI_GOLD_SONNET_3D,
    AL_SONNET_3D,
    VIA_SONNET_3D,
)
from ..beta2.layers import drawing_to_sonnet_3d


@dataclass(frozen=True, eq=True)
class B2PTestbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25
    backside_gold: bool = False

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [
            NB_SONNET_3D,
            BTA_SONNET_3D,
            BTA_VAR_SONNET_3D,
            TI_GOLD_SONNET_3D,
            AL_SONNET_3D,
            VIA_SONNET_3D,
        ]

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
            simulate.DielectricLayer("airbridge", 1.0, 1),
            simulate.DielectricLayer("cplanesaph", 750.0, 2, (9.3, 11.5)),
            simulate.DielectricLayer("airbot", 100000.0, 3),
        ]

    @property
    def _filename(self):
        return "B2P" + super()._filename

    @property
    def _portlevel(self):
        return 1


class B2PCMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        return B2PTestbench(cell, geometry.feedline, 1.0, stub=10)


if __name__ == "__main__":
    from .geometry import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Beta 2P Simulation Tool")
    runner = B2PCMD(
        "b2p",
        parser,
        BoxConfig,
        ["coupler_tunable", "capacitor_tunable"],
        BTA_VAR_SONNET_3D,
        [
            SimEmit(),
            SimRun(),
            SimBulkEstimate(BTA_SONNET_3D, BTA_VAR_SONNET_3D),
            SimCorner(),
            SimOptimize({"coupler_tunable": 64, "capacitor_tunable": 512}, BTA_SONNET_3D, BTA_VAR_SONNET_3D),
        ],
    )
    runner.run(parser.parse_args())

    sys.exit(0)
