import gdstk
from .. import layers
from ..simulate import SonnetMetalLayer, SonnetViaLayer, SonnetPlanarGeneral

ATA_NB = layers.DrawingLayer((0, 0), "aTa_Nb")
HF = layers.DrawingLayer((1, 0), "Hf_Bridge")
HF_CONTACT = layers.DrawingLayer((2, 0), "Hf_Contact")

ATA_NB_SONNET = SonnetMetalLayer((0, 0), "atanb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.2878), 105.0)
HF_SONNET = SonnetMetalLayer((1, 0), "hf", 0, SonnetPlanarGeneral(1e-7, 0, 0, 8.0), 200.0)
HF_VAR_SONNET = SonnetMetalLayer((1, 1), "hf_var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 200.0), 200.0)
TI_GOLD_SONNET = SonnetMetalLayer((99, 0), "tiau", 1, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)

ATA_NB_SONNET_3D = SonnetMetalLayer((0, 0), "atanb", 1, SonnetPlanarGeneral(1e-7, 0, 0, 0.2878), 105.0)
HF_SONNET_3D = SonnetMetalLayer((1, 0), "hf", 0, SonnetPlanarGeneral(1e-7, 0, 0, 8.0), 200.0)
HF_VAR_SONNET_3D = SonnetMetalLayer((1, 1), "hf_var", 0, SonnetPlanarGeneral(1e-7, 0, 0, 200.0), 200.0)
HF_VIA_SONNET_3D = SonnetViaLayer((2, 0), "hf_via", 0, None, 1)
TI_GOLD_SONNET_3D = SonnetMetalLayer((99, 0), "tiau", 2, SonnetPlanarGeneral(0.1, 0, 0, 0), 100.0)


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")
    atanb = [
        p for p in cf.get_polygons() if p.layer == ATA_NB.gds_layer[0] and p.datatype == ATA_NB.gds_layer[1]
    ]
    hf = [p for p in cf.get_polygons() if p.layer == HF.gds_layer[0] and p.datatype == HF.gds_layer[1]]
    hf_var = [p for p in cf.get_polygons() if p.layer == HF_VAR_SONNET.gds_layer[0] and p.datatype == HF_VAR_SONNET.gds_layer[1]]
    hf_sim = gdstk.boolean(hf, atanb, "not", 0.00001, *HF_SONNET)
    atanb_sim = gdstk.boolean(atanb, atanb, "or", 0.00001, *ATA_NB_SONNET)
    cell_sim.add(*hf_sim, *atanb_sim, *hf_var)
    return cell_sim


def drawing_to_sonnet_3d(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM3D")
    atanb = [
        p for p in cf.get_polygons() if p.layer == ATA_NB.gds_layer[0] and p.datatype == ATA_NB.gds_layer[1]
    ]
    hf = [p for p in cf.get_polygons() if p.layer == HF.gds_layer[0] and p.datatype == HF.gds_layer[1]]
    hf_contact = [
        p
        for p in cf.get_polygons()
        if p.layer == HF_CONTACT.gds_layer[0] and p.datatype == HF_CONTACT.gds_layer[1]
    ]
    hf_var = [p for p in cf.get_polygons() if p.layer == HF_VAR_SONNET_3D.gds_layer[0] and p.datatype == HF_VAR_SONNET_3D.gds_layer[1]]
    hf_sim = gdstk.boolean(hf, hf, "or", 0.00001, *HF_SONNET_3D)
    atanb_sim = gdstk.boolean(atanb, atanb, "or", 0.00001, *ATA_NB_SONNET_3D)
    via_sim = gdstk.boolean(
        hf,
        hf_contact,
        "and",
        0.00001,
        *HF_VIA_SONNET_3D
    )
    cell_sim.add(*hf_sim, *atanb_sim, *hf_var, *via_sim)
    return cell_sim
