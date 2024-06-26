import gdstk

from dataclasses import dataclass, is_dataclass
from .. import simulate
from ..cmd import GeMKIDCMD, SimBulkEstimate, SimCorner, SimEmit, SimOptimize, SimRun

from .layers import (
    NB_SONNET,
    NB_SONNET_3D,
    BTA_SONNET,
    BTA_SONNET_3D,
    BTA_VAR_SONNET,
    BTA_VAR_SONNET_3D,
    TI_GOLD_SONNET,
    TI_GOLD_SONNET_3D,
    VIA_SONNET_3D,
    AL_SONNET_3D,
)
from .layers import drawing_to_sonnet, drawing_to_sonnet_3d


@dataclass(frozen=True, eq=True)
class B2Testbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25
    backside_gold: bool = False
    threedee: bool = False

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        if self.threedee:
            return [
                NB_SONNET_3D,
                BTA_SONNET_3D,
                BTA_VAR_SONNET_3D,
                TI_GOLD_SONNET_3D,
                VIA_SONNET_3D,
                AL_SONNET_3D,
            ]
        return [NB_SONNET, BTA_SONNET, BTA_VAR_SONNET, TI_GOLD_SONNET]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet(super()._cell) if not self.threedee else drawing_to_sonnet_3d(super()._cell)
        if self.backside_gold:
            width = c.bounding_box()[1][0] - c.bounding_box()[0][0]
            height = c.bounding_box()[1][1] - c.bounding_box()[0][1]
            c.add(
                gdstk.rectangle(
                    (self.padding, 0),
                    (width - self.padding, height),
                    *(TI_GOLD_SONNET if self.threedee else TI_GOLD_SONNET_3D),
                )
            )
        return c

    @property
    def _dielectric_stack(self) -> list[simulate.DielectricLayer]:
        if self.threedee:
            return [
                simulate.DielectricLayer("airtop", 100000.0, 0),
                simulate.DielectricLayer("airbridge", 1.0, 1),
                simulate.DielectricLayer("cplanesaph", 750.0, 2, (9.3, 11.5)),
                simulate.DielectricLayer("airbot", 100000, 3),
            ]
        return [
            simulate.DielectricLayer("airtop", 100000.0, 0),
            simulate.DielectricLayer("cplanesaph", 750.0, 1, (9.3, 11.5)),
            simulate.DielectricLayer("airbot", 100000.0, 2),
        ]

    @property
    def _filename(self):
        if self.threedee:
            return "B23D" + super()._filename
        return "B2" + super()._filename

    @property
    def _portlevel(self):
        return 0 if not self.threedee else 1


class B2CMD(GeMKIDCMD):
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        return B2Testbench([cell], geometry.feedline, stub=18, threedee=ns.threedee, cell_heights=[150.0])

    generation = 1


if __name__ == "__main__":
    from .geometry import BoxConfig

    import argparse
    import logging
    import sys

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Beta 2 Simulation Tool")
    parser.add_argument("--threedee", action="store_true", default=False)
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
