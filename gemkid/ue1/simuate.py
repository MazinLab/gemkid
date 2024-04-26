import gdstk

from dataclasses import dataclass
from .. import simulate
from .. import layers

from .layers import ATA_NB_SONNET, HF_SONNET, drawing_to_sonnet


@dataclass
class UE1Testbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [ATA_NB_SONNET, HF_SONNET]

    @property
    def _cell(self) -> gdstk.Cell:
        return drawing_to_sonnet(super()._cell)

    @property
    def _dielectric_stack(self) -> list[simulate.DielectricLayer]:
        return [
            simulate.DielectricLayer("airtop", 100000.0, 0),
            simulate.DielectricLayer("cplanesaph", 430.0, 1, (9.3, 11.5)),
            simulate.DielectricLayer("airbot", 100000.0, 2),
        ]
