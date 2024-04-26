import abc
import gdstk
import os
import pathlib

import numpy as np


from dataclasses import dataclass
from typing import Any, Optional

from . import geometry
from .layers import DrawingLayer


class SonnetSerializableProperty(abc.ABC):
    @abc.abstractmethod
    def pysonnet_args(self) -> dict[str, Any]:
        pass


class SonnetMetal(SonnetSerializableProperty):
    pass


class SonnetDielectric(SonnetSerializableProperty):
    pass


@dataclass(frozen=True, eq=True)
class SonnetPlanarGeneral(SonnetMetal):
    rdc: float  # Ohm/sq
    rrf: float  # Ohm*sqrt(Hz)/sq
    xdc: float  # Ohm/sq
    ls: float  # pH/sq

    def pysonnet_args(self) -> dict[str, Any]:
        return {"metal_type": "general", "r_dc": self.rdc, "r_rf": self.rrf, "x_dc": self.xdc, "ls": self.ls}


@dataclass(frozen=True, eq=True)
class SonnetBrickCond(SonnetDielectric):
    erel: float | tuple[float, float, float]
    tan: float | tuple[float, float, float]
    cond: float | tuple[float, float, float]

    def anisotropic(self):
        if type(self.erel) is tuple:
            if not (self.erel[0] == self.erel[1] and self.erel[0] == self.erel[2]):
                return True
        if type(self.tan) is tuple:
            if not (self.tan[0] == self.tan[1] and self.tan[0] == self.tan[2]):
                return True
        if type(self.cond) is tuple:
            if not (self.cond[0] == self.cond[1] and self.cond[0] == self.cond[2]):
                return True

        return False


@dataclass(frozen=True, eq=True)
class SonnetLayer(DrawingLayer, SonnetSerializableProperty):
    level: int
    properties: SonnetPlanarGeneral | SonnetBrickCond
    thickness: Optional[float] = None

    def pysonnet_args(self) -> dict[str, Any]:
        return {"fill_type": "diagonal", "level": self.level, "name": self.name}


@dataclass(frozen=True, eq=True)
class DielectricLayer(SonnetSerializableProperty):
    name: str
    thickness: float
    level: int
    erel: float | tuple[float, float] = 1.0
    mrel: float | tuple[float, float] = 1.0
    eloss: float | tuple[float, float] = 0.0
    mloss: float | tuple[float, float] = 0.0
    cond: float | tuple[float, float] = 0.0

    def pysonnet_args(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "thickness": self.thickness,
            "level": self.level,
            "epsilon": self.erel,
            "mu": self.mrel,
            "dielectric_loss": self.eloss,
            "magnetic_loss": self.mloss,
            "conductivity": self.cond,
        }


@dataclass(frozen=True, eq=True)
class Port(SonnetSerializableProperty):
    n: int
    pos: tuple[float, float]
    z0: float | complex = 50.0


@dataclass(frozen=True, eq=True)
class StdPort(Port):
    def pysonnet_args(self):
        kwargs = {
            "port_type": "standard",
            "number": self.n,
            "x": self.pos[0],
            "y": self.pos[1],
            "resistance": self.z0.real,
        }
        if self.z0 is complex:
            kwargs["reactance"] = self.z0.imag
        return kwargs


class Sweep(SonnetSerializableProperty):
    pass


@dataclass(frozen=True, eq=True)
class AdaptiveSweep(Sweep):
    f_low: float = 3
    f_high: float = 10

    def pysonnet_args(self):
        return {"sweep_type": "abs", "f1": self.f_low, "f2": self.f_high}


@dataclass(frozen=True, eq=True)
class SonnetOptions(SonnetSerializableProperty):
    current: bool = False
    resonance_detection: bool = True
    q_accuracy: bool = True

    def pysonnet_args(self):
        return {
            "current_density": self.current,
            "resonance_detection": self.resonance_detection,
            "q_accuracy": self.q_accuracy,
        }


class TestbenchABC(abc.ABC):
    _sweeps = []

    @property
    @abc.abstractmethod
    def _filename(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def _ports(self) -> list[Port]:
        pass

    @property
    @abc.abstractmethod
    def _delta(self) -> tuple[float, float]:
        pass

    @property
    @abc.abstractmethod
    def _cell(self) -> gdstk.Cell:
        pass

    @property
    @abc.abstractmethod
    def _dielectric_stack(self) -> list[DielectricLayer]:
        pass

    @property
    @abc.abstractmethod
    def _layer_stack(self) -> list[SonnetLayer]:
        pass

    @property
    @abc.abstractmethod
    def _sonnet_options(self) -> SonnetOptions:
        pass

    @property
    def _width(self) -> float:
        bb = self._cell.bounding_box()
        if bb is None:
            raise ValueError("Cell does not have a defined bounding box??? Please emit GDS and send to Aled")
        return bb[1][0] - bb[0][0]

    @property
    def _height(self) -> float:
        bb = self._cell.bounding_box()
        if bb is None:
            raise ValueError("Cell does not have a defined bounding box??? Please emit GDS and send to Aled")
        return bb[1][1] - bb[0][1]

    def add_sweep(self, sweep: Sweep = AdaptiveSweep()) -> "TestbenchABC":
        self._sweeps.append(sweep)
        return self

    def _make_project(self):
        import pysonnet as ps

        dx, dy = self._delta

        p = ps.GeometryProject()
        p.set_units(length="um")
        p.set_box_cover("free space", top=True)
        p.set_box_cover("free space", bottom=True)
        cell = self._cell
        box_width = self._width
        box_height = self._height
        p.setup_box(box_width, box_height, int(box_width / dx), int(box_height / dy))
        for diel in self._dielectric_stack:
            p.add_dielectric(**diel.pysonnet_args())
        for layer in self._layer_stack:
            if issubclass(layer.properties.__class__, SonnetMetal):
                p.define_metal(**layer.properties.pysonnet_args(), name=layer.name + "-metal")
                p.define_technology_layer(
                    layer_type="metal", material=layer.name + "-metal", **layer.pysonnet_args()
                )
                p.add_gdstk_cell("metal", cell, *layer, tech_layer=layer.name)
            else:
                raise NotImplementedError(
                    "Layer type {:s} not yet implemented".format(repr(layer.properties.__class__))
                )

        for port in self._ports:
            p.add_port(**port.pysonnet_args())

        for sweep in self._sweeps:
            p.add_frequency_sweep(**sweep.pysonnet_args())
        p.set_analysis("frequency sweep")

        # TODO: WTF
        p["control"]["speed"] = 0
        p.set_options(**self._sonnet_options.pysonnet_args())

        return p

    def emit(self, filename: Optional[str] = None, output_folder: Optional[str | pathlib.Path] = None):
        if output_folder is None:
            output_folder = os.getcwd()
        output_folder = pathlib.Path(output_folder)
        assert output_folder.is_dir()

        if filename is None:
            filename = self._filename

        p = self._make_project()

        p.add_output_file("touchstone2", output_folder=output_folder)
        p.make_sonnet_file(output_folder / filename)

        return p

    def run(self, filename: Optional[str] = None, output_folder: Optional[str | pathlib.Path] = None):
        self.emit(filename, output_folder).run()


@dataclass
class LeftFeedlineTestbench(TestbenchABC):
    cell: gdstk.Cell | list[gdstk.Cell]
    feedline_config: geometry.FeedlineConfig
    padding: float = 0.5
    stub: float = 10
    filename: Optional[str] = None

    @property
    def _filename(self):
        if self.filename is not None:
            return self.filename
        return (
            "LeftFeedlineTestbench-"
            + hex(
                abs(
                    hash(self.cell.name)
                    if type(self.cell) is gdstk.Cell
                    else sum([hash(i.name) for i in self.cell])
                )
            )
            + ".son"
        )

    @property
    def _sonnet_options(self) -> SonnetOptions:
        return SonnetOptions()

    def __height(self):
        ch = (
            (self.cell.bounding_box()[1][1] - self.cell.bounding_box()[0][1])
            if type(self.cell) is gdstk.Cell
            else sum([i.bounding_box()[1][1] - i.bounding_box()[0][1] for i in self.cell])
        )
        return ch + self.stub * 2

    @property
    def _ports(self) -> list[Port]:
        return [
            StdPort(-1, (self.padding + self.feedline_config.c / 2, 0)),
            StdPort(
                1,
                (
                    self.padding
                    + self.feedline_config.c
                    + self.feedline_config.b
                    + self.feedline_config.a / 2,
                    0,
                ),
            ),
            StdPort(
                -1,
                (
                    self.padding
                    + self.feedline_config.c * 1.5
                    + self.feedline_config.b * 2
                    + self.feedline_config.a,
                    0,
                ),
            ),
            StdPort(-2, (self.padding + self.feedline_config.c / 2, self.__height())),
            StdPort(
                2,
                (
                    self.padding
                    + self.feedline_config.c
                    + self.feedline_config.b
                    + self.feedline_config.a / 2,
                    self.__height(),
                ),
            ),
            StdPort(
                -2,
                (
                    self.padding
                    + self.feedline_config.c * 1.5
                    + self.feedline_config.b * 2
                    + self.feedline_config.a,
                    self.__height(),
                ),
            ),
        ]

    @property
    def _width(self) -> float:
        return super()._width + self.padding * 2

    @property
    def _cell(self) -> gdstk.Cell:
        c = gdstk.Cell("Top" + self._filename)
        cache = {}
        stub = self.feedline_config.draw(self.stub, ([], []), cache)
        c.add(
            gdstk.Reference(stub, (self.padding, 0.0)),
            gdstk.Reference(stub, (self.padding, self.__height() - self.stub)),
        )
        leftline = self.feedline_config.draw_half(self.__height() - 2 * self.stub, [], cache)
        c.add(gdstk.Reference(leftline, (self.feedline_config.width_half + self.padding, self.__height() - self.stub), rotation=np.pi))
        y = self.stub
        if type(self.cell) is gdstk.Cell:
            c.add(gdstk.Reference(self.cell, (self.padding + self.feedline_config.width_half, y)))
        else:
            for cell in self.cell:
                c.add(gdstk.Reference(cell, (self.padding + self.feedline_config.width_half, y)))
                y += cell.bounding_box()[1][1] - cell.bounding_box()[0][1]
        return c.flatten()
