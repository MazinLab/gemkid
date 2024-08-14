import gdstk
from .. import layers
from ..simulate import SonnetMetalLayer, SonnetViaLayer, SonnetPlanarGeneral

NB = layers.DrawingLayer((0, 0), "Nb")

NB_SONNET = SonnetMetalLayer((0, 0), "nb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 1.1), 25.0)
NB_VAR_SONNET = SonnetMetalLayer((0, 0), "nb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 101.1), 25.0)


def filter_polygons(polys, layer):
    return [p for p in polys if p.layer == layer.gds_layer[0] and p.datatype == layer.gds_layer[1]]


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")

    nb = filter_polygons(cf.get_polygons(), NB)
    nb_var = filter_polygons(cf.get_polygons(), NB_VAR_SONNET)

    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET)
    nb_var_sim = gdstk.boolean(nb_var, nb_var, "or", 0.00001, *NB_VAR_SONNET)
    cell_sim.add(*nb_sim, *nb_var_sim)
    return cell_sim
