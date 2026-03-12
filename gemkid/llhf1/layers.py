import gdstk
from .. import layers
from ..simulate import SonnetMetalLayer, SonnetViaLayer, SonnetPlanarGeneral

NB = layers.DrawingLayer((0, 0), "Nb")
HF = layers.DrawingLayer((1, 0), "hf")
HF_CONTACT = layers.DrawingLayer((1, 2), "MoKeepout")
AL = layers.DrawingLayer((2, 0), "Al")
VIA = layers.DrawingLayer((3, 0), "AltoNb")

NB_SONNET = SonnetMetalLayer((0, 0), "nb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.3), 105.0)
HF_SONNET = SonnetMetalLayer((1, 0), "hf", 0, SonnetPlanarGeneral(1e-7, 0, 0, 19.0), 220.0)
HF_VAR_SONNET = SonnetMetalLayer((1, 1), "hf-var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 119.0), 220.0)
TI_GOLD_SONNET = SonnetMetalLayer((99, 0), "tiau", 1, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)

NB_SONNET_3D = SonnetMetalLayer((0, 0), "nb", 1, SonnetPlanarGeneral(1e-7, 0, 0, 0.3), 105.0)
HF_SONNET_3D = SonnetMetalLayer((1, 0), "hf", 1, SonnetPlanarGeneral(1e-7, 0, 0, 19.0), 220.0)
HF_VAR_SONNET_3D = SonnetMetalLayer((1, 1), "hf-var", 1, SonnetPlanarGeneral(1e-7, 0, 0, 119.0), 220.0)
AL_SONNET_3D = SonnetMetalLayer((2, 0), "al", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.043), 700.0)
VIA_SONNET_3D = SonnetViaLayer((3, 0), "altonb", 0, None, 1)
TI_GOLD_SONNET_3D = SonnetMetalLayer((99, 0), "tiau", 2, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)


def filter_polygons(polys, layer):
    return [p for p in polys if p.layer == layer.gds_layer[0] and p.datatype == layer.gds_layer[1]]


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")

    nb = filter_polygons(cf.get_polygons(), NB)
    hf = filter_polygons(cf.get_polygons(), HF)
    hf_var = filter_polygons(cf.get_polygons(), HF_VAR_SONNET)

    hf_sim = gdstk.boolean(hf, nb, "not", 0.00001, *HF_SONNET)
    hf_var_sim = gdstk.boolean(hf_var, nb, "not", 0.00001, *HF_VAR_SONNET)
    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET)
    cell_sim.add(*hf_sim, *nb_sim, *hf_var_sim)
    return cell_sim


def drawing_to_sonnet_3d(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM3D")

    nb = filter_polygons(cf.get_polygons(), NB)
    hf = filter_polygons(cf.get_polygons(), HF)
    hf_var = filter_polygons(cf.get_polygons(), HF_VAR_SONNET_3D)
    al = filter_polygons(cf.get_polygons(), AL)
    via = filter_polygons(cf.get_polygons(), VIA)

    hf_sim = gdstk.boolean(hf, nb, "not", 0.00001, *HF_SONNET_3D)
    hf_var_sim = gdstk.boolean(hf_var, nb, "not", 0.00001, *HF_VAR_SONNET_3D)
    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET_3D)
    al_sim = gdstk.boolean(al, al, "or", 0.00001, *AL_SONNET_3D)
    via_sim = gdstk.boolean(via, via, "or", 0.000001, *VIA_SONNET_3D)
    cell_sim.add(*hf_sim, *nb_sim, *hf_var_sim, *al_sim, *via_sim)
    return cell_sim
