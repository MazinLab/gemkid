import gdstk

from dataclasses import dataclass, is_dataclass
from .. import simulate

from .layers import (
    ATA_NB_SONNET,
    HF_SONNET,
    TI_GOLD_SONNET,
    ATA_NB_SONNET_3D,
    HF_SONNET_3D,
    HF_VIA_SONNET_3D,
    TI_GOLD_SONNET_3D,
)
from .layers import drawing_to_sonnet, drawing_to_sonnet_3d


@dataclass(frozen=True, eq=True)
class UE1Testbench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [ATA_NB_SONNET, HF_SONNET, TI_GOLD_SONNET]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet(super()._cell)
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
        return "UE1" + super()._filename

    @property
    def _portlevel(self):
        return 0


@dataclass(frozen=True, eq=True)
class UE13DTestBench(simulate.LeftFeedlineTestbench):
    delta: float = 0.25

    @property
    def _delta(self):
        return (self.delta, self.delta)

    @property
    def _filename(self):
        return "3D" + super()._filename

    @property
    def _layer_stack(self) -> list[simulate.SonnetLayer]:
        return [ATA_NB_SONNET_3D, HF_SONNET_3D, HF_VIA_SONNET_3D, TI_GOLD_SONNET_3D]

    @property
    def _cell(self) -> gdstk.Cell:
        c = drawing_to_sonnet_3d(super()._cell)
        c.add(
            gdstk.rectangle((self.padding, 0), (self._width - self.padding, self._height), *TI_GOLD_SONNET_3D)
        )
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


if __name__ == "__main__":
    from .geometry import BoxConfig
    from ..geometry import GeomConfigMarker

    import argparse
    import logging
    import typing

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="UE1 Simulation Tool")
    sp = parser.add_subparsers(dest="subparsers")
    parser.add_argument("--3d", dest="threed", action="store_const", const=True, default=False)

    emit = sp.add_parser("emit")
    emit.add_argument("--cap_fill", type=float, default=0.5)
    emit.add_argument("--coupler_fill", type=float, default=0.5)
    emit.add_argument("--f_low", type=float, default=1.0)
    emit.add_argument("--f_high", type=float, default=12.0)
    emit.add_argument("--filename", type=str)
    emit.add_argument("--output_folder", type=str)

    corner = sp.add_parser("corner")
    corner.add_argument("--output_folder", type=str)
    corner.add_argument("--f_low", type=float, default=1.0)
    corner.add_argument("--f_high", type=float, default=12.0)

    geo = emit.add_argument_group("Geometry Args")

    def add_geom_args(sp, c, prefix="ue1"):
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
                add_geom_args(sp, v, prefix + "." + k)

    def construct_geometry(args, c, prefix="ue1"):
        kws = {}
        for k, v in typing.get_type_hints(c).items():
            if typing.get_args(v):
                if len(typing.get_args(v)) == 2:
                    v = typing.get_args(v)[0]
                else:
                    continue
            if prefix + "." + k in args:
                kws[k] = args[prefix + "." + k]
            elif is_dataclass(v) and issubclass(v, GeomConfigMarker):
                kws[k] = construct_geometry(args, v, prefix + "." + k)
        return c(**kws)

    add_geom_args(geo, BoxConfig)
    add_geom_args(corner, BoxConfig)

    def fit(testcase, f_range=(), output_folder=None):
        import loopfit
        import numpy as np
        import pathlib
        import os

        if output_folder is None:
            output_folder = os.getcwd()
        output_folder = pathlib.Path(output_folder)

        f, i, q = loopfit.load_touchstone(output_folder / (testcase._filename.split(".")[0] + ".ts"))

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

    ns = parser.parse_args()
    if ns.threed:
        TB = UE13DTestBench
    else:
        TB = UE1Testbench

    if ns.subparsers == "emit":
        box = construct_geometry(ns.__dict__, BoxConfig)
        cell = box.draw(ns.cap_fill, ns.coupler_fill, True, {})
        cell_son = drawing_to_sonnet(cell)
        logging.info("Material Volumes:")
        for l in [ATA_NB_SONNET, HF_SONNET]:
            if l.thickness:
                v = (
                    sum(
                        [
                            p.area()
                            for p in cell_son.polygons
                            if p.layer == l.gds_layer[0] and p.datatype == l.gds_layer[1]
                        ]
                    )
                    * l.thickness
                    / 1000
                )
                logging.info("    {:s}: {:f} um^3".format(l.name, v))
        setup = TB(cell, box.feedline, filename=ns.filename)
        logging.info("Emitting SONNET file: {:s}".format(setup._filename))
        setup.emit(output_folder=ns.output_folder)

    if ns.subparsers == "corner":
        box = construct_geometry(ns.__dict__, BoxConfig)
        deets = []
        for corner in [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]:
            cell = box.draw(*corner, True, {})
            setup = TB(cell, box.feedline)
            setup.add_sweep(simulate.AdaptiveSweep(ns.f_low, ns.f_high))
            logging.info("Simulating {:s} ...".format(setup._filename))
            setup.run(output_folder=ns.output_folder)
            f = fit(setup, output_folder=ns.output_folder)
            deets.append(
                "cap_fill={:.1f}, coupler_fill={:.1f}, f0={:.4f}, qc={:.2f}, qi?={:.2f}, file={:s}".format(
                    corner[1], corner[0], f["fm"], f["qc"], f["qi"], setup._filename
                )
            )
            logging.info(deets[-1])
        logging.info("Analysis Summary:")
        for d in deets:
            logging.info("\t" + d)
