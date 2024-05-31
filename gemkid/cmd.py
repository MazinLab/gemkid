import argparse
import abc
import os
import typing
import logging
import itertools

import numpy as np

from dataclasses import dataclass, is_dataclass
from typing import Optional, Type

from . import simulate
from .geometry import GeomConfigMarker
from .layers import DrawingLayer


class GeMCommandABC(abc.ABC):
    @property
    @abc.abstractmethod
    def subcommand(self) -> str:
        pass

    @abc.abstractmethod
    def add_args(self, subparser):
        pass

    @abc.abstractmethod
    def run(self, ns, command):
        pass


class SimSweepABC(GeMCommandABC):
    pass


class SimGeomABC(GeMCommandABC):
    pass


class SimGeomSpecificABC(SimGeomABC):
    pass


class SimEmit(SimGeomSpecificABC, SimSweepABC):
    @property
    def subcommand(self) -> str:
        return "emit"

    def add_args(self, subparser):
        subparser.add_argument("--filename", type=str)
        subparser.add_argument("--variational", nargs='?', default=False, const=True)

    def run(self, ns, command: "GeMKIDCMD"):
        tunables = command.get_tunables(ns)
        geom = command.construct_geometry(ns)
        cell = command.draw_cell(geom, tunables, ns.variational)
        tb, emited = command.construct_testbench(cell, geom, ns)
        return tb, emited


class SimRun(SimEmit):
    @property
    def subcommand(self) -> str:
        return "run"

    def run(self, ns, command: "GeMKIDCMD"):
        tb, emited = super().run(ns, command)
        emited.run()
        fit = command.fit_testbench(tb, ns)

        log = logging.getLogger(__name__)
        log.info("Tunables: " + repr(command.get_tunables(ns)))
        log.info("\tf0 {:2.5f}G, fm {:2.5f}G".format(fit["fm"], fit["f0"]))
        log.info("\tqc {:4.3f}k, qi {:4.3f}k".format(fit["qc"] / 1000, fit["qi"] / 1000))
        return fit

class SimCorner(SimGeomABC, SimSweepABC):
    @property
    def subcommand(self) -> str:
        return "corner"

    def add_args(self, subparser):
        pass

    def run(self, ns, command: "GeMKIDCMD"):
        prod = itertools.product([0.0, 1.0], repeat = len(command.tunables))
        geom = command.construct_geometry(ns)
        fits = []
        for tunes in prod:
            tdict = {t: v for t, v in zip(command.tunables, tunes)}
            cell = command.draw_cell(geom, tdict)
            tb, emited = command.construct_testbench(cell, geom, ns)
            emited.run()
            fit = command.fit_testbench(tb, ns)
            fits.append((tdict, fit))
        log = logging.getLogger(__name__)
        for tunables, fit in fits:
            log.info("Tunables: " + repr(tunables))
            log.info("\tf0 {:2.5f}G, fm {:2.5f}G".format(fit["fm"], fit["f0"]))
            log.info("\tqc {:4.3f}k, qi {:4.3f}k".format(fit["qc"] / 1000, fit["qi"] / 1000))
        


@dataclass
class SimBulkEstimate(SimGeomSpecificABC, SimSweepABC):
    base_layer: simulate.SonnetMetalLayer
    variational_layer: simulate.SonnetMetalLayer

    @property
    def subcommand(self) -> str:
        return "bulkestimate"

    def add_args(self, subparser):
        pass

    def run(self, ns, command: "GeMKIDCMD"):
        tunables = command.get_tunables(ns)
        geom = command.construct_geometry(ns)
        cell_base, cell_var = command.draw_cell(geom, tunables, False), command.draw_cell(
            geom, tunables, True
        )
        fits = []
        for cell in [cell_base, cell_var]:
            tb, emitted = command.construct_testbench(cell, geom, ns)
            emitted.run()
            fits.append(command.fit_testbench(tb, ns))
        l_bulk = (
            (self.variational_layer.properties.ls - self.base_layer.properties.ls)
            * 1e-12
            * (fits[0]["f0"] * 1e9 / (fits[0]["f0"] * 1e9 - fits[1]["f0"] * 1e9))
            / 2
        )
        c_bulk = 1 / (l_bulk * np.pi * 2 * (fits[0]["f0"] * 1e9) ** 2)

        log = logging.getLogger(__name__)
        log.info("Tunables: " + repr(command.get_tunables(ns)))
        log.info("\tf0 {:2.5f}G, fm {:2.5f}G".format(fits[0]["fm"], fits[0]["f0"]))
        log.info("\tqc {:4.3f}k, qi {:4.3f}k".format(fits[0]["qc"] / 1000, fits[0]["qi"] / 1000))
        log.info("\tLb {:.5e}H ({:4.5f}nH)".format(l_bulk, l_bulk / 1e-9))
        log.info("\tCb {:.5e}F ({:4.5f}nF)".format(c_bulk, c_bulk / 1e-9))


@dataclass
class GeMKIDCMD(abc.ABC):
    prefix: str
    parser: argparse.ArgumentParser
    geometry_config: Type[GeomConfigMarker]
    tunables: list[str]
    variation_layer: Optional[DrawingLayer]
    subcommands: list[GeMCommandABC]

    def __post_init__(self):
        sps = self.parser.add_subparsers(dest="subparser")
        for subcommand in self.subcommands:
            sp = sps.add_parser(subcommand.subcommand)
            subcommand.add_args(sp)
            if issubclass(subcommand.__class__, SimSweepABC):
                sp.add_argument("--flow", type=float, default=3)
                sp.add_argument("--fhigh", type=float, default=10)
            if issubclass(subcommand.__class__, SimGeomABC):
                sp.add_argument("--output_folder", type=str, default=os.getcwd())
                geo = sp.add_argument_group("Geometry Arguments")
                self.add_geom_args(geo, self.geometry_config, self.prefix)
            if issubclass(subcommand.__class__, SimGeomSpecificABC):
                for tunable in self.tunables:
                    sp.add_argument("--" + tunable, type=float, default=0.5)

    @abc.abstractmethod
    def _testbench_from_cell(self, cell, geometry, ns) -> simulate.TestbenchABC:
        pass

    def run(self, ns):
        for subcommand in self.subcommands:
            if subcommand.subcommand == ns.subparser:
                subcommand.run(ns, self)

    def construct_geometry(self, ns, geom=None, path=""):
        if geom is None:
            geom = self.geometry_config
        args = ns.__dict__
        kws = {}
        for k, v in typing.get_type_hints(geom).items():
            if typing.get_args(v):
                if len(typing.get_args(v)) == 2:
                    v = typing.get_args(v)[0]
                else:
                    continue
            if self.prefix + path + "." + k in args:
                kws[k] = args[self.prefix + path + "." + k]
            elif is_dataclass(v) and issubclass(v, GeomConfigMarker):
                kws[k] = self.construct_geometry(ns, v, path + "." + k)
        return geom(**kws)

    def draw_cell(self, config, tunables, variation=False):
        if variation:
            if self.variation_layer is None:
                raise ValueError("Requested a variational sim when no variation layer specified")
            return config.draw(**tunables, variation_layer=self.variation_layer, flatten=True, cellcache={})
        return config.draw(**tunables, variation_layer=None, flatten=True, cellcache={})

    def construct_testbench(self, cell, geometry, ns, filename=None):
        tb = self._testbench_from_cell(cell, geometry, ns)
        if "flow" in ns.__dict__ and "fhigh" in ns.__dict__:
            tb.add_sweep(simulate.AdaptiveSweep(ns.flow, ns.fhigh))
        if filename is None and "filename" in ns.__dict__.keys():
            filename = ns.filename
        return tb, tb.emit(output_folder=ns.output_folder, filename=filename)

    def run_testbench(self, tb):
        return tb.run()

    def fit_testbench(self, tb, ns, f_range=()):
        import loopfit
        import numpy as np
        import pathlib

        f, i, q = loopfit.load_touchstone(
            pathlib.Path(ns.output_folder) / (tb._filename.split(".")[0] + ".ts")
        )

        sorter = np.argsort(f)
        f, i, q = f[sorter], i[sorter], q[sorter]
        if f_range:
            start_mask = (f < f_range[1]) & (f > f_range[0])
            f, i, q = f[start_mask], i[start_mask], q[start_mask]

        mag = 10 * np.log10(i**2 + q**2)
        index = np.argmin(mag)
        mask = (f > f[index] - 0.1) & (f < f[index] + 0.1)
        guess = loopfit.guess(f[mask], i[mask], q[mask], phase0=0, phase1=0)
        result = loopfit.fit(f[mask], i[mask], q[mask], **guess)

        return result

    @classmethod
    def add_geom_args(cls, sp, c, prefix):
        for k, v in typing.get_type_hints(c).items():
            if typing.get_args(v):
                if len(typing.get_args(v)) == 2:
                    v = typing.get_args(v)[0]
                else:
                    continue
            if v is int:
                sp.add_argument(
                    "--" + prefix + "." + k, type=int, default=c.__dict__[k] if k in c.__dict__ else None
                )
            if v is float:
                sp.add_argument(
                    "--" + prefix + "." + k, type=float, default=c.__dict__[k] if k in c.__dict__ else None
                )
            if is_dataclass(v) and issubclass(v, GeomConfigMarker):
                cls.add_geom_args(sp, v, prefix + "." + k)

    def get_tunables(self, ns):
        args = ns.__dict__
        return {t: args[t] for t in self.tunables}
