import argparse
import abc
from ctypes import ArgumentError
import os
import typing
import logging
import itertools
import pathlib

import numpy as np
import pandas as pd
import scipy as sp

from dataclasses import dataclass, is_dataclass
from typing import Optional, Type
from pathlib import Path

from . import simulate
from .geometry import GeomConfigMarker
from .layers import DrawingLayer


def _fit(touchstone, f_range=()):
    import loopfit

    f, i, q = loopfit.load_touchstone(touchstone)

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
        subparser.add_argument("--variational", nargs="?", default=False, const=True)

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
        prod = itertools.product([0.0, 1.0], repeat=len(command.tunables))
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


class SimOptimize(SimGeomABC, SimSweepABC):
    def __init__(
        self,
        tunable_grid: dict[str, int],
        base_layer: simulate.SonnetMetalLayer,
        variational_layer: simulate.SonnetMetalLayer,
    ):
        self.base_layer = base_layer
        self.variational_layer = variational_layer
        self.grid = {k: np.linspace(0, 1, v, endpoint=True) for k, v in tunable_grid.items()}

    @property
    def subcommand(self) -> str:
        return "optimize"

    def add_args(self, subparser):
        subparser.add_argument("--database", type=str, required=True)
        subparser.add_argument(
            "--deltal",
            type=float,
            required=True,
            help="Change in inductance for which we are optimizing our response in pH",
        )
        subparser.add_argument(
            "--metric",
            type=str,
            required=False,
            choices=["meanphase", "maxphase", "centralphase", "qc"],
            default="centralphase",
        )
        subparser.add_argument(
            "--target",
            type=float,
            required=True,
            help="Target phase response in degrees or target qc in thousands",
        )
        subparser.add_argument("--fstart", type=float, default=4.05)
        subparser.add_argument("--fstop", type=float, default=8.5)
        subparser.add_argument("--fcount", type=int, default=256)
        subparser.add_argument("--quiet", nargs="?", default=False, const=True)

    def run(self, ns, command: "GeMKIDCMD"):
        import tqdm

        self.df = self.get_database(ns.database, command.tunables)
        self.generation = command.generation
        self.command = command
        self.ns = ns
        self.geometry = command.construct_geometry(ns)

        if ns.quiet:
            logging.getLogger("pysonnet").setLevel(logging.WARNING)

        prod = itertools.product([0.0, 1.0], repeat=len(command.tunables))
        for tunes in prod:
            tdict = {t: v for t, v in zip(command.tunables, tunes)}
            self.get_result(tdict, ns.deltal)
            self.save_database(ns.database)

        freqs = np.linspace(self.ns.fstart, self.ns.fstop, self.ns.fcount, endpoint=True)
        for freq in tqdm.tqdm(freqs):
            self.optimize_freq(freq, self.ns.deltal, self.ns.target)
            self.save_database(ns.database)

    def optimize_freq(self, freq, deltal, target, maxiter=32, x0=None):
        if maxiter == 0:
            return

        tunes = list(self.grid.keys())[:2]
        if self.ns.metric == "meanphase":
            objective = lambda rm, rc, qc: (rm + rc) / 2
        elif self.ns.metric == "maxphase":
            objective = lambda rm, rc, qc: rm
        elif self.ns.metric == "centralphase":
            objective = lambda rm, rc, qc: rc
        elif self.ns.metric == "qc":
            objective = lambda rm, rc, qc: qc / 1000
        else:
            raise ArgumentError("Metric {:s} not supported".format(self.ns.metric))
        manifold = sp.interpolate.CloughTocher2DInterpolator(
            np.array([self.df[tunes[0]], self.df[tunes[1]]]).T,
            np.array([self.df["f0"], self.df["response_max"], self.df["response_center"], self.df["qc"]]).T,
            fill_value=0,
        )

        if x0 is None:
            flt = self.df[(self.df["f0"] < freq) & (self.df["generation"] == self.generation)]
            resplt = flt[objective(flt["response_max"], flt["response_center"], flt["qc"]) < target]
            if len(resplt) == 0:
                resplt = flt
            start = resplt.iloc[
                objective(resplt["response_max"], resplt["response_center"], resplt["qc"]).argmax()
            ]
            x0 = np.array([start[tunes[0]], start[tunes[1]]])
        obj = lambda x: np.abs(target - objective(manifold(x[0], x[1])[1], manifold(x[0], x[1])[2], manifold(x[0], x[1])[3])) ** 2 + np.abs(freq - manifold(x[0], x[1])[0]) ** 2
        # obj = lambda x: [objp(x), print(objp(x)), print(x)][0]
        sol = sp.optimize.minimize(
            obj,
            x0,
            bounds=[(0, 1), (0, 1)],
        ).x

        log = logging.getLogger(__name__)
        log.info("Estimated Solution: " + repr(sol))

        quantized_ll = np.array(
            [
                np.max(self.grid[tunes[0]][self.grid[tunes[0]] <= sol[0]]),
                np.max(self.grid[tunes[1]][self.grid[tunes[1]] <= sol[1]]),
            ]
        )
        quantized_ur = np.array(
            [
                np.min(self.grid[tunes[0]][self.grid[tunes[0]] >= sol[0]]),
                np.min(self.grid[tunes[1]][self.grid[tunes[1]] >= sol[1]]),
            ]
        )

        fully_cached = True
        for tunes in [
            {tunes[0]: quantized_ll[0], tunes[1]: quantized_ll[1]},
            {tunes[0]: quantized_ur[0], tunes[1]: quantized_ur[1]},
            {tunes[0]: quantized_ll[0], tunes[1]: quantized_ur[1]},
            {tunes[0]: quantized_ur[0], tunes[1]: quantized_ll[1]},
        ]:
            fully_cached = fully_cached and self.have_cached(tunes, deltal)
            if not self.have_cached(tunes, deltal):
                f0, rm, rc, qc = self.get_result(tunes, deltal)
                log.info(
                    "Guess "
                    + repr(tunes)
                    + " f0: {:.3f}, qc: {:.1f}, resp max: {:.1f} deg, resp center: {:.1f} deg, resp mean: {:.1f} deg".format(
                        f0, qc, rm, rc, 0.5 * rm + 0.5 * rc
                    )
                )
        if fully_cached:
            log.info("FOUND SOLUTION WITH {:d} ITERATIONS REMAINING FOR f0={:.3f}".format(maxiter, freq))
            return
        return self.optimize_freq(freq, deltal, target, maxiter - 1, quantized_ll)

    def have_cached(self, tunables, deltal):
        df = self.df
        res = df[(df.generation == self.generation) & (df.geom == hash(self.geometry))]
        for k, v in tunables.items():
            res = res[res[k] == v]
        if len(res[res["deltal"] == deltal]) != 0:
            return True
        return False

    def get_response(self, touchstone, touchstonevar, deltal):
        import loopfit

        f = _fit(touchstone)
        fv = _fit(touchstonevar)
        l_bulk = (
            (self.variational_layer.properties.ls - self.base_layer.properties.ls)
            * 1e-12
            * (f["f0"] * 1e9 / (f["f0"] * 1e9 - fv["f0"] * 1e9))
            / 2
        )
        c_bulk = 1 / (l_bulk * np.pi * 2 * (f["f0"] * 1e9) ** 2)
        f["lb"] = l_bulk
        f["cb"] = c_bulk
        df = 1 / np.sqrt(2 * np.pi * l_bulk * c_bulk) - 1 / np.sqrt(
            2 * np.pi * (l_bulk + deltal * 1e-12) * c_bulk
        )

        freqs, i, q = loopfit.load_touchstone(touchstone)
        iq = i + 1.0j * q
        center = sp.optimize.minimize(lambda x: np.std(np.abs(iq + x[0] + x[1] * 1.0j)), [0, 0]).x
        iqc = iq + center[0] + center[1] * 1.0j

        fs = np.linspace(f["f0"] * 1e9 - 1e6, f["f0"] * 1e9 + 1e6, 1024)
        interp = sp.interpolate.interp1d(freqs * 1e9, np.unwrap(np.angle(iqc)))
        rmax = np.degrees(np.max((interp(fs) - interp(fs + df))))
        rcenter = np.degrees(interp(f["f0"] * 1e9) - interp(f["f0"] * 1e9 + df))
        log = logging.getLogger(__name__)
        log.info("FIT RESPONSE: {:.3f} deg max, {:.3f} deg central".format(rmax, rcenter))
        return rmax, rcenter, f

    def get_result(self, tunables, deltal):
        df = self.df
        res = df[(df.generation == self.generation) & (df.geom == hash(self.geometry))]
        for k, v in tunables.items():
            res = res[res[k] == v]
        if len(res) != 0:
            if len(res[res["deltal"] == deltal]) != 0:
                return (
                    res[res["deltal"] == deltal].iloc[0]["f0"],
                    res[res["deltal"] == deltal].iloc[0]["response_max"],
                    res[res["deltal"] == deltal].iloc[0]["response_center"],
                    res[res["deltal"] == deltal].iloc[0]["qc"],
                )
            else:
                r = res.iloc[0]
                ts, tsvar = r["ts"], r["tsvar"]
        else:
            son, ts = self.get_sim(tunables, False)
            sonvar, tsvar = self.get_sim(tunables, True)
        respmax, respcenter, fit = self.get_response(ts, tsvar, deltal)
        output = {
            "son": str(son),
            "ts": str(ts),
            "sonvar": str(sonvar),
            "tsvar": str(tsvar),
            "geom": hash(self.geometry),
            "generation": self.generation,
            "fm": fit["fm"],
            "f0": fit["f0"],
            "qi": fit["qi"],
            "qc": fit["qc"],
            "lb": fit["lb"],
            "cb": fit["cb"],
            "deltal": deltal,
            "response_max": respmax,
            "response_center": respcenter,
        }
        for k, v in tunables.items():
            output[k] = v
        row = pd.DataFrame(output, index=range(1))
        self.df = pd.concat([df, row], ignore_index=True, axis=0)
        return output["f0"], output["response_max"], output["response_center"], output["qc"]

    def get_sim(self, tunables, variational: bool = False):
        RETRIES = 5
        cell = self.command.draw_cell(self.geometry, tunables, variational)
        tb, emited = self.command.construct_testbench(cell, self.geometry, self.ns)
        tb.run()
        son = pathlib.Path(self.ns.output_folder) / tb._filename
        ts = pathlib.Path(self.ns.output_folder) / (tb._filename.split(".")[0] + ".ts")
        for _ in range(RETRIES):
            if ts.is_file():
                break
            tb.run()
        return son, ts

    def get_database(self, file, tunables):
        columns = [
            "son",
            "ts",
            "sonvar",
            "tsvar",
            "geom",
            "generation",
            "fm",
            "f0",
            "qi",
            "qc",
            "lb",
            "cb",
            "deltal",
            "response_max",
            "response_center",
        ]
        columns.extend(tunables)
        file = Path(file)
        if file.is_file():
            return pd.read_parquet(file, columns=columns)
        return pd.DataFrame(columns=columns)

    def save_database(self, file):
        self.df.to_parquet(file)


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
    generation: int = 0

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
        return _fit(pathlib.Path(ns.output_folder) / (tb._filename.split(".")[0] + ".ts"), f_range)

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
