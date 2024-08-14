import gdstk
from .. import layers
from ..simulate import SonnetMetalLayer, SonnetViaLayer, SonnetPlanarGeneral

NB = layers.DrawingLayer((0, 0), "Nb")
BTA = layers.DrawingLayer((1, 0), "bTa")
BTA_CONTACT = layers.DrawingLayer((1, 2), "MoKeepout")
AL = layers.DrawingLayer((2, 0), "Al")
VIA = layers.DrawingLayer((3, 0), "AltoNb")

NB_SONNET = SonnetMetalLayer((0, 0), "nb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.3), 105.0)
BTA_SONNET = SonnetMetalLayer((1, 0), "bta", 0, SonnetPlanarGeneral(1e-7, 0, 0, 95.0), 220.0)
BTA_VAR_SONNET = SonnetMetalLayer((1, 1), "bta-var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 195.0), 220.0)
TI_GOLD_SONNET = SonnetMetalLayer((99, 0), "tiau", 1, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)

NB_SONNET_3D = SonnetMetalLayer((0, 0), "nb", 1, SonnetPlanarGeneral(1e-7, 0, 0, 0.3), 105.0)
BTA_SONNET_3D = SonnetMetalLayer((1, 0), "bta", 1, SonnetPlanarGeneral(1e-7, 0, 0, 95.0), 220.0)
BTA_VAR_SONNET_3D = SonnetMetalLayer((1, 1), "bta-var", 1, SonnetPlanarGeneral(1e-7, 0, 0, 195.0), 220.0)
AL_SONNET_3D = SonnetMetalLayer((2, 0), "al", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.043), 700.0)
VIA_SONNET_3D = SonnetViaLayer((3, 0), "altonb", 0, None, 1)
TI_GOLD_SONNET_3D = SonnetMetalLayer((99, 0), "tiau", 2, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)


def filter_polygons(polys, layer):
    return [p for p in polys if p.layer == layer.gds_layer[0] and p.datatype == layer.gds_layer[1]]


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")

    nb = filter_polygons(cf.get_polygons(), NB)
    bta = filter_polygons(cf.get_polygons(), BTA)
    bta_var = filter_polygons(cf.get_polygons(), BTA_VAR_SONNET)

    bta_sim = gdstk.boolean(bta, nb, "not", 0.00001, *BTA_SONNET)
    bta_var_sim = gdstk.boolean(bta_var, nb, "not", 0.00001, *BTA_VAR_SONNET)
    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET)
    cell_sim.add(*bta_sim, *nb_sim, *bta_var_sim)
    return cell_sim


def drawing_to_sonnet_3d(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM3D")

    nb = filter_polygons(cf.get_polygons(), NB)
    bta = filter_polygons(cf.get_polygons(), BTA)
    bta_var = filter_polygons(cf.get_polygons(), BTA_VAR_SONNET_3D)
    al = filter_polygons(cf.get_polygons(), AL)
    via = filter_polygons(cf.get_polygons(), VIA)

    bta_sim = gdstk.boolean(bta, nb, "not", 0.00001, *BTA_SONNET_3D)
    bta_var_sim = gdstk.boolean(bta_var, nb, "not", 0.00001, *BTA_VAR_SONNET_3D)
    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET_3D)
    al_sim = gdstk.boolean(al, al, "or", 0.00001, *AL_SONNET_3D)
    via_sim = gdstk.boolean(via, via, "or", 0.000001, *VIA_SONNET_3D)
    cell_sim.add(*bta_sim, *nb_sim, *bta_var_sim, *al_sim, *via_sim)
    return cell_sim
