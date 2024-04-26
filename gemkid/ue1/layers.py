import gdstk
from .. import layers
from ..simulate import SonnetLayer, SonnetPlanarGeneral

ATA_NB = layers.DrawingLayer((0, 0), "aTa_Nb")
HF = layers.DrawingLayer((1, 0), "Hf_Bridge")
HF_CONTACT = layers.DrawingLayer((2, 0), "Hf_CONTACT")

ATA_NB_SONNET = SonnetLayer((0, 0), "atanb", 0, SonnetPlanarGeneral(1e-7, 0, 0, 0.2878), 200.0)
HF_SONNET = SonnetLayer((1, 0), "hf", 0, SonnetPlanarGeneral(1e-7, 0, 0, 23), 200)


def drawing_to_sonnet(cell: gdstk.Cell):
    cf = cell.flatten()
    cell_sim = gdstk.Cell(cf.name + "-SIM")
    atanb = [
        p for p in cf.get_polygons() if p.layer == ATA_NB.gds_layer[0] and p.datatype == ATA_NB.gds_layer[1]
    ]
    hf = [p for p in cf.get_polygons() if p.layer == HF.gds_layer[0] and p.datatype == HF.gds_layer[1]]
    hf_sim = gdstk.boolean(hf, atanb, "not", 0.00001, *HF_SONNET)
    atanb_sim = gdstk.boolean(atanb, atanb, "or", 0.00001, *ATA_NB_SONNET)
    cell_sim.add(*hf_sim, *atanb_sim)
    return cell_sim
