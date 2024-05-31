import gdstk
from .. import layers
from ..simulate import SonnetMetalLayer, SonnetViaLayer, SonnetPlanarGeneral

NB = layers.DrawingLayer((0, 0), "Nb")
BTA = layers.DrawingLayer((1, 0), "bTa")

NB_SONNET = SonnetMetalLayer((0, 0), "nb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.3), 105.0)
BTA_SONNET = SonnetMetalLayer((1, 0), "bta", 0, SonnetPlanarGeneral(1e-7, 0, 0, 95.0), 220.0)
BTA_VAR_SONNET = SonnetMetalLayer((1, 1), "bta-var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 195.0), 220.0)
TI_GOLD_SONNET = SonnetMetalLayer((99, 0), "tiau", 1, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)

NB_SONNET_3D = SonnetMetalLayer((0, 0), "nb", 1, SonnetPlanarGeneral(1e-7, 0, 0, 0.3), 105.0)
BTA_SONNET_3D = SonnetMetalLayer((1, 0), "bta", 0, SonnetPlanarGeneral(1e-7, 0, 0, 95.0), 220.0)
TI_GOLD_SONNET_3D = SonnetMetalLayer((99, 0), "tiau", 2, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")
    nb = [p for p in cf.get_polygons() if p.layer == NB.gds_layer[0] and p.datatype == NB.gds_layer[1]]
    bta = [p for p in cf.get_polygons() if p.layer == BTA.gds_layer[0] and p.datatype == BTA.gds_layer[1]]
    bta_var = [
        p
        for p in cf.get_polygons()
        if p.layer == BTA_VAR_SONNET.gds_layer[0] and p.datatype == BTA_VAR_SONNET.gds_layer[1]
    ]
    bta_sim = gdstk.boolean(bta, nb, "not", 0.00001, *BTA_SONNET)
    bta_var_sim = gdstk.boolean(bta_var, nb, "not", 0.00001, *BTA_VAR_SONNET)
    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET)
    cell_sim.add(*bta_sim, *nb_sim, *bta_var_sim)
    return cell_sim


def drawing_to_sonnet_3d(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM3D")
    nb = [p for p in cf.get_polygons() if p.layer == NB.gds_layer[0] and p.datatype == NB.gds_layer[1]]
    bta = [p for p in cf.get_polygons() if p.layer == BTA.gds_layer[0] and p.datatype == BTA.gds_layer[1]]
    # hf_contact = [
    #     p
    #     for p in cf.get_polygons()
    #     if p.layer == HF_CONTACT.gds_layer[0] and p.datatype == HF_CONTACT.gds_layer[1]
    # ]
    bta_sim = gdstk.boolean(bta, bta, "or", 0.00001, *BTA_SONNET_3D)
    nb_sim = gdstk.boolean(nb, nb, "or", 0.00001, *NB_SONNET_3D)
    # via_sim = gdstk.boolean(hf, hf_contact, "and", 0.00001, *HF_VIA_SONNET_3D)
    cell_sim.add(*bta_sim, *nb_sim)  # , *via_sim)
    return cell_sim
